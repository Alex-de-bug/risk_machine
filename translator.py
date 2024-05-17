#!/usr/bin/python3
import sys

from isa import Opcode, Term, write_code


def remove_comments_and_blank_lines(code: str) -> list:
    lines = code.split("\n")
    cleaned_lines = ["jmp .text"]
    for line in lines:
        stripped_line = line.split("@")[0].strip()
        if stripped_line:
            if "section " in stripped_line:
                stripped_line = stripped_line[8:]
            cleaned_lines.append(stripped_line)
    return cleaned_lines

def process_data_section_in_list_inplace(code_lines: list) -> None:
    """
    Модифицирует секцию .data в предоставленном списке строк ASM кода, преобразуя строки в Unicode значения,
    обрабатывая числа и специальные директивы resb. Изменения происходят на месте в исходном списке.
    """
    in_data_section = False

    for index, line in enumerate(code_lines):
        stripped_line = line.strip()
        if is_data_section_start(stripped_line):
            in_data_section = True
            continue

        if is_data_section_end(in_data_section, stripped_line):
            break

        if ":" in stripped_line and in_data_section:
            key, value = parse_line(stripped_line)
            new_lines = process_value(key, value)
            update_code_lines(code_lines, index, new_lines)

def is_data_section_start(line: str) -> bool:
    return line == ".data:"

def is_data_section_end(in_data_section: bool, line: str) -> bool:
    return in_data_section and line.startswith(".")

def parse_line(line: str) -> tuple:
    key, value = line.split(":", 1)
    return key.strip(), value.strip()

def process_value(key: str, value: str) -> list:
    if "resb" in value:
        return process_resb(key, value)
    if '"' in value:
        return process_string(key, value)
    return [f"{key}:", value]

def process_resb(key: str, value: str) -> list:
    _, size = value.split()
    return [f"{key}:"] + ["0" for _ in range(int(size))]

def process_string(key: str, value: str) -> list:
    new_lines = [f"{key}:"]
    on_str = False
    for ch in value:
        if ch == '"':
            on_str = not on_str
        elif not on_str and ch != " ":
            if ch != ",":
                new_lines += ch
        elif on_str:
            new_lines += [str(ord(ch))]
    return new_lines

def update_code_lines(code_lines: list, index: int, new_lines: list) -> None:
    del code_lines[index]
    for idx, item in enumerate(new_lines):
        code_lines.insert(index + idx, item)

def process_labels(lines: list) -> dict:
    """
    Обрабатывает список строк и извлекает метки в словарь.
    Метки - это строки, содержащие '.название:' или 'название:'.
    Эти строки удаляются из исходного списка, и их индексы корректируются соответственно.
    """
    labels_dict = {}
    i = 0

    while i < len(lines):
        line = lines[i].strip()
        if ":" in line and (line.startswith(".") or not line.startswith(" ")):
            label_name = line.split(":")[0].strip()
            labels_dict[label_name] = i
            lines.pop(i)
        else:
            i += 1
    return labels_dict

def translate_to_machine_word(labels: dict, lines: list) -> list:
    """
    Обрабатывает список строк, генерируя формат инструкций или данных, подставляя метки.
    """
    code = []

    for pc, line in enumerate(lines):
        instr = process_line(pc, line, labels)
        code.append(instr)

    append_interrupt_label(code, labels)
    return code

def process_line(pc: int, line: str, labels: dict) -> dict:
    line_term = line.split(" ")
    op = line_term[0]

    if op in [opcode.value for opcode in Opcode]:
        return process_opcode(pc, op, line_term, labels)
    return process_data(pc, op, labels)

def process_opcode(pc: int, op: str, line_term: list, labels: dict) -> dict:
    if op in ["load", "store"]:
        return process_load_store(op, line_term, labels, pc)
    if op in ["add", "sub", "mod", "inc", "cmp"]:
        return process_arithmetic(op, line_term, pc)
    if op in ["di", "ei", "in", "out", "iret", "halt"]:
        return process_single_op(op, line_term, pc)
    if op in ["jz", "jnz", "jmp"]:
        return process_jump(op, line_term, labels, pc)
    if op == "move":
        return process_move(op, line_term, pc)
    return {}

def process_load_store(op: str, line_term: list, labels: dict, pc: int) -> dict:
    num_first_reg = int(line_term[1][1:-1])
    if "(" in line_term[2]:
        addr = labels.get(line_term[2][1:-1])
        return {"opcode": op, "reg": num_first_reg, "op": addr, "addrType": 1, "term": Term(pc, line_term[2][1:-1])}
    addr = labels.get(line_term[2])
    return {"opcode": op, "reg": num_first_reg, "op": addr, "addrType": 0, "term": Term(pc, line_term[2])}

def process_arithmetic(op: str, line_term: list, pc: int) -> dict:
    if len(line_term) == 2:
        num_first_reg = int(line_term[1][1:])
        return {"opcode": op, "op": num_first_reg, "addrType": 2, "term": Term(pc, "")}
    if len(line_term) == 3:
        num_first_reg = int(line_term[1][1:-1])
        num_second_reg = int(line_term[2][1:])
        return {"opcode": op, "op1": num_first_reg, "op2": num_second_reg, "addrType": 2, "term": Term(pc, "")}
    if len(line_term) == 4:
        num_1_reg = int(line_term[1][1:-1])
        num_2_reg = int(line_term[2][1:-1])
        num_3_reg = int(line_term[3][1:])
        return {"opcode": op, "op1": num_1_reg, "op2": num_2_reg, "op3": num_3_reg, "addrType": 2, "term": Term(pc, "")}
    return {}

def process_single_op(op: str, line_term: list, pc: int) -> dict:
    if len(line_term) == 1:
        return {"opcode": op, "addrType": 3, "term": Term(pc, "")}
    if len(line_term) == 3:
        num_first_reg = int(line_term[1][1:-1])
        num_port = int(line_term[2])
        return {"opcode": op, "reg": num_first_reg, "op": num_port, "addrType": 4, "term": Term(pc, "")}
    return {}

def process_jump(op: str, line_term: list, labels: dict, pc: int) -> dict:
    addr = int(labels.get(line_term[1]))
    return {"opcode": op, "op": addr, "addrType": 0, "term": Term(pc, line_term[1])}

def process_move(op: str, line_term: list, pc: int) -> dict:
    num_first_reg = int(line_term[1][1:-1])
    if "r" in line_term[2]:
        reg = int(line_term[2][1:])
        return {"opcode": op, "reg": num_first_reg, "op": reg, "addrType": 2, "term": Term(pc, "")}
    if "#" in line_term[2]:
        value = int(line_term[2][1:])
        return {"opcode": op, "reg": num_first_reg, "op": value, "addrType": 0, "term": Term(pc, "")}
    return {}

def process_data(pc: int, op: str, labels: dict) -> dict:
    if op.isdigit():
        return {"data": int(op), "term": Term(pc, "")}
    return {"data": labels.get(op), "term": Term(pc, op)}

def append_interrupt_label(code: list, labels: dict) -> None:
    if ".int1" in labels:
        code.append({"int1": labels.get(".int1")})
    else:
        code.append({"int1": "-"})

def translate(text):
    clear_lines = remove_comments_and_blank_lines(text)
    process_data_section_in_list_inplace(clear_lines)
    labels = process_labels(clear_lines)
    return translate_to_machine_word(labels, clear_lines)


def main(source, target):
    """Функция запуска транслятора. Параметры -- исходный и целевой файлы."""
    with open(source, encoding="utf-8") as f:
        source = f.read()

    code = translate(source)
    write_code(target, code)
    print("source LoC:", len(source.split("\n")), "code instr:", len(code))

if __name__ == "__main__":
    assert len(sys.argv) == 3, "Wrong arguments: translator.py <input_file> <target_file>"
    _, source, target = sys.argv
    main(source, target)

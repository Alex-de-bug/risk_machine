#!/usr/bin/python3

import sys

from isa import Opcode, Term, write_code
from typing import List, Dict


def remove_comments_and_blank_lines(code: str) -> List[str]:
    lines = code.split('\n')
    cleaned_lines = ["jmp .text"]
    for line in lines:
        stripped_line = line.split('@')[0].strip()
        if stripped_line:
            if "section " in stripped_line:
                stripped_line = stripped_line[8:]
            cleaned_lines.append(stripped_line)
    return cleaned_lines


def process_data_section_in_list_inplace(code_lines: List[str]) -> None:
    """
    Модифицирует секцию .data в предоставленном списке строк ASM кода, преобразуя строки в Unicode значения,
    обрабатывая числа и специальные директивы resb. Изменения происходят на месте в исходном списке.
    """
    in_data_section = False
    insert_index = 0

    for index, line in enumerate(code_lines):
        stripped_line = line.strip()
        if stripped_line == ".data:":
            in_data_section = True
            insert_index = index + 1
            continue

        if in_data_section and stripped_line.startswith('.'):
            break

        if ':' in stripped_line and in_data_section:
            key, value = stripped_line.split(':', 1)
            key = key.strip()
            value = value.strip()
            if 'resb' in value:
                _, size = value.split()
                new_lines = [f"{key}:"] + ['0' for _ in range(int(size))]
            elif '"' in value:
                new_lines = [f"{key}:"]
                on_str = False
                for ch in value:
                    if ch == '"':
                        on_str = on_str.__invert__()
                    elif on_str.__invert__() and ch != ' ':
                        if ch == ',':
                            continue
                        else:
                            new_lines += ch
                    elif on_str:
                        new_lines += [str(ord(ch))]
            else:
                new_lines = [f"{key}:"] + [value]

            del code_lines[index]
            for idx, item in enumerate(new_lines):
                code_lines.insert(index + idx, item)
            insert_index += len(new_lines) - 1


def process_labels(lines: List[str]) -> Dict[str, int]:
    """
    Обрабатывает список строк и извлекает метки в словарь.
    Метки - это строки, содержащие '.название:' или 'название:'.
    Эти строки удаляются из исходного списка, и их индексы корректируются соответственно.
    """
    labels_dict = {}
    i = 0

    while i < len(lines):
        line = lines[i].strip()
        if ':' in line and (line.startswith('.') or not line.startswith(' ')):
            label_name = line.split(':')[0].strip()
            labels_dict[label_name] = i
            lines.pop(i)
        else:
            i += 1
    return labels_dict


def translate_to_machine_word(labels: Dict[str, int], lines: List[str]) -> List[Dict]:
    """
    Обрабатывает список строк, генерируя формат инструкций или данных, подставляя метки.
    """
    code = []

    for pc, line in enumerate(lines):
        line_term = line.split(" ")
        op = line_term[0]
        instr = []
        if op in [opcode.value for opcode in Opcode]:
            if op in ['load', 'store']:
                num_first_reg = int(line_term[1][1:-1])
                if "(" in line_term[2]:
                    addr = labels.get(line_term[2][1:-1])
                    instr = {'opcode': op, 'reg': num_first_reg, 'op': addr, 'term': Term(pc, 1)}
                else:
                    addr = labels.get(line_term[2])
                    instr = {'opcode': op, 'reg': num_first_reg, 'op': addr, 'term': Term(pc, 0)}
            elif op in ['add', 'sub', 'mod', 'inc', 'cmp']:
                if len(line_term) == 2:
                    num_first_reg = int(line_term[1][1:])
                    instr = {'opcode': op, 'op': num_first_reg, 'term': Term(pc, 2)}
                elif len(line_term) == 3:
                    num_first_reg = int(line_term[1][1:-1])
                    num_second_reg = int(line_term[2][1:])
                    instr = {'opcode': op, 'op1': num_first_reg, 'op2': num_second_reg, 'term': Term(pc, 2)}
                elif len(line_term) == 4:
                    num_1_reg = int(line_term[1][1:-1])
                    num_2_reg = int(line_term[2][1:-1])
                    num_3_reg = int(line_term[3][1:])
                    instr = {'opcode': op, 'op1': num_1_reg, 'op2': num_2_reg, 'op3': num_3_reg, 'term': Term(pc, 2)}
            elif op in ['di', 'ei', 'in', 'out', 'iret', 'halt']:
                if len(line_term) == 1:
                    instr = {'opcode': op, 'term': Term(pc, 3)}
                elif len(line_term) == 3:
                    num_first_reg = int(line_term[1][1:-1])
                    num_port = int(line_term[2])
                    instr = {'opcode': op, 'reg': num_first_reg, 'op': num_port, 'term': Term(pc, 4)}
            elif op in ['jz', 'jnz', 'jmp']:
                addr = int(labels.get(line_term[1]))
                instr = {'opcode': op, 'op': addr, 'term': Term(pc, 0)}
            elif op == 'move':
                num_first_reg = int(line_term[1][1:-1])
                if 'r' in line_term[2]:
                    reg = int(line_term[2][1:])
                    instr = {'opcode': op, 'reg': num_first_reg, 'op': reg, 'term': Term(pc, 2)}
                elif '#' in line_term[2]:
                    value = int(line_term[2][1:])
                    instr = {'opcode': op, 'reg': num_first_reg, 'op': value, 'term': Term(pc, 0)}
        else:
            if op.isdigit():
                instr = {'data': int(op)}
            else:
                instr = {'data': labels.get(op)}
        code.append(instr)
    if '.int1' in labels:
        code.append({'int1': labels.get('.int1')})
    else:
        code.append({'int1': '-'})
    return code


def translate(text):
    clear_lines = remove_comments_and_blank_lines(text)
    process_data_section_in_list_inplace(clear_lines)
    labels = process_labels(clear_lines)
    code = translate_to_machine_word(labels, clear_lines)

    return code


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

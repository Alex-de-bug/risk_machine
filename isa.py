import enum
from collections import namedtuple
import json

MEMORY_SIZE = 1048567
MAX_NUMBER = 1 << 31 - 1
MIN_NUMBER = -(1 << 31)
INT1_ADDRESS = 1
INPUT_PORT_ADDRESS = 0
OUTPUT_PORT_ADDRESS = 1


class Opcode(str, enum.Enum):
    LOAD = "load"  # Загрузка значения из памяти в регистр
    STORE = "store"  # Сохранение значения из регистра в память

    ADD = "add"  # Сложение
    SUB = "subtract"  # Вычитание
    MOD = "modulus"  # Остаток от деления
    INC = "increment"  # Увеличение на единицу
    CMP = "compare"  # Сравнение

    DI = "disable_interrupts"  # Отключение прерываний
    EI = "enable_interrupts"  # Включение прерываний
    IN = "input"  # Ввод данных из внешнего порта
    OUT = "output"  # Вывод данных во внешний порт

    JZ = "jump_if_zero"  # Переход, если флаг нуля
    JNZ = "jump_if_not_zero"  # Переход, если нет флага нуля
    JMP = "jump"  # Безусловный переход

    MOVE = "move"  # Перемещение данных между регистрами

    HALT = "halt"  # Остановка выполнения программы

    def __str__(self):
        """`Opcode.INC` - `increment`."""
        return str(self.value)

class Term(namedtuple("Term", "line pos symbol")):
    """Сделано через класс, чтобы был docstring."""


def write_code(filename, code):
    """Записать машинный код в файл."""
    with open(filename, "w", encoding="utf-8") as file:
        buf = []
        for instr in code:
            buf.append(json.dumps(instr))
        file.write("[" + ",\n ".join(buf) + "]")


def read_code(filename):
    """Прочесть машинный код из файла."""
    with open(filename, encoding="utf-8") as file:
        code = json.loads(file.read())

    for instr in code:
        # Конвертация строки в Opcode
        instr["opcode"] = Opcode(instr["opcode"])

        # Конвертация списка term в класс Term
        if "term" in instr:
            assert len(instr["term"]) == 3
            instr["term"] = Term(instr["term"][0], instr["term"][1], instr["term"][2])

    return code
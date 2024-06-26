import enum
import json
from collections import namedtuple

MEMORY_SIZE = 1048567
MAX_NUMBER = 1 << 31 - 1
MIN_NUMBER = -(1 << 31)
INT1_ADDRESS = 1
INPUT_PORT_ADDRESS = 0
OUTPUT_PORT_ADDRESS = 1

DIRECTION_ADDRESS = 0
INDERECTION_ADDRESS = 1
REGISTER_ADDRESS = 2
NO_ADDRESS = 3
PORT_ADDRESS = 4


class Opcode(str, enum.Enum):
    LOAD = "load"  # Загрузка значения из памяти в регистр
    STORE = "store"  # Сохранение значения из регистра в память

    ADD = "add"  # Сложение
    SUB = "sub"  # Вычитание
    MOD = "mod"  # Остаток от деления
    INC = "inc"  # Увеличение на единицу
    CMP = "cmp"  # Сравнение

    DI = "di"  # Отключение прерываний
    EI = "ei"  # Включение прерываний
    IN = "in"  # Ввод данных из внешнего порта
    OUT = "out"  # Вывод данных во внешний порт

    JZ = "jz"  # Переход, если флаг нуля
    JNZ = "jnz"  # Переход, если нет флага нуля
    JMP = "jmp"  # Безусловный переход

    MOVE = "move"  # Перемещение данных между регистрами

    HALT = "halt"  # Остановка выполнения программы

    IRET = "iret"  # Возврат из прерывания

    def __str__(self):
        """`Opcode.INC` - `increment`."""
        return str(self.value)


class Term(namedtuple("Term", "index related_label")):
    """Тип может быть:
    0 - прямая
    1 - косвенная
    2 - регистр
    3 - безадрессная
    4 - портовая адресация
    """


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
        if "opcode" in instr:
            instr["opcode"] = Opcode(instr["opcode"])

        # Конвертация списка term в класс Term
        if "term" in instr:
            assert len(instr["term"]) == 2
            instr["term"] = Term(instr["term"][0], instr["term"][1])

    return code

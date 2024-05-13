#!/usr/bin/python3

import logging
import sys

from isa import Opcode, read_code

from isa import (
    INPUT_PORT_ADDRESS,
    MAX_NUMBER,
    MEMORY_SIZE,
    MIN_NUMBER,
    OUTPUT_PORT_ADDRESS,
    Opcode,
    read_code,
)

INSTRUCTION_LIMIT = 1500

ALU_OPCODE_BINARY_HANDLERS = {
    Opcode.ADD: lambda left, right: int(left + right),
    Opcode.SUB: lambda left, right: int(left - right),
    Opcode.MOD: lambda left, right: int(left % right),
    Opcode.CMP: lambda left, right: int(left - right),
}

ALU_OPCODE_SINGLE_HANDLERS = {
    Opcode.INC: lambda right: right + 1,
}

class InterruptionController:
    interruption: bool = None
    interruption_number: int = None

    def __init__(self):
        self.interruption = False
        self.interruption_number = 0

    def generate_interruption(self, number: int) -> None:
        assert number == 1, f"Interruption controller doesn't invoke interruption-{number}"
        self.interruption = True
        self.interruption_number = number

class RegistersFile:
    r0: int = None
    r1: int = None
    r2: int = None
    r3: int = None
    r4: int = None
    r5: int = None
    r6: int = None
    r7: int = None
    r8: int = None
    r9: int = None
    r10: int = None
    r11: int = None
    r12: int = None
    ar: int = None
    ir: dict = None
    ipc: int = None

    left_out: int = None
    right_out = None
    def __init__(self):
        self.r0 = 0
        self.r1 = 0
        self.r2 = 0
        self.r3 = 0
        self.r4 = 0
        self.r5 = 0
        self.r6 = 0
        self.r7 = 0
        self.r8 = 0
        self.r9 = 0
        self.r10 = 0
        self.r11 = 0
        self.r12 = 0
        self.ar = 0 #13
        self.ir = {} #14
        self.ipc = 0 #15
        self.left_out: int = 0

    def latch_reg_n(self, number: int, value: int) -> None:
        """ Выбор регистра, в который защёлкнется значение """
        if 0 <= number <= 12:
            setattr(self, f'r{number}', value)
        elif number == 13:
            self.ar = value
        elif number == 15:
            self.ipc = value
        else:
            raise ValueError("Invalid register number")

    def latch_reg_ir(self, instruction) -> None:
        """ Защёлкивание в регистр инструкции """
        self.ir = instruction

    def sel_left_reg(self, number: int) -> None:
        """Выбор регистра, который поступит на левый выход"""
        if 0 <= number <= 12:
            self.left_out = getattr(self, f'r{number}')
        elif number == 13:
            self.left_out = self.ar
        elif number == 15:
            self.left_out = self.ipc
        else:
            raise ValueError("Invalid register number")

    def sel_right_reg(self, number: int) -> None:
        """ Выбор регистра значение, который поступит на правый выход """
        if 0 <= number <= 13:
            self.right_out = getattr(self, f'r{number}')
        elif number == 13:
            self.right_out = self.ar
        elif number == 14:
            self.right_out = self.ir
        elif number == 15:
            self.right_out = self.ipc
        else:
            raise ValueError("Invalid register number")

class Alu:
    zero_flag = None

    def __init__(self):
        self.zero_flag = 0

    def perform(self, left: int, right: int, opcode: Opcode) -> int:
        """ Математические действия алу """
        assert (
            opcode in ALU_OPCODE_BINARY_HANDLERS or opcode in ALU_OPCODE_SINGLE_HANDLERS
        ), f"Unknown ALU command {opcode}"
        if opcode in ALU_OPCODE_BINARY_HANDLERS:
            handler = ALU_OPCODE_BINARY_HANDLERS[opcode]
            value = handler(left, right)
        else:
            handler = ALU_OPCODE_SINGLE_HANDLERS[opcode]
            value = handler(right)
        value = self.handle_overflow(value)
        self.set_flags(value)
        return value

    @staticmethod
    def cut_operand(right: dict) -> int:
        """ Вырезание операнда """
        if "op" in right:
            return right.get("op")
        else:
            raise ValueError("OperandError")

    @staticmethod
    def handle_overflow(value: int) -> int:
        """ Обработка переполнения """
        if value > MAX_NUMBER:
            value %= MAX_NUMBER
        elif value < MIN_NUMBER:
            value %= abs(MIN_NUMBER)
        return value

    def set_flags(self, value) -> None:
        """ Выставление флагов по результату """
        if value == 0:
            self.zero_flag = True
        else:
            self.zero_flag = False

class DataPath:
    register_file: RegistersFile = None
    pc = None
    memory = None
    memory_size = None
    alu: Alu = None
    interruption_controller: InterruptionController = None
    input_buffer = None
    output_buffer = None

    def __init__(self, memory):
        self.register_file = RegistersFile()
        self.pc = 0

        self.memory = [0] * MEMORY_SIZE
        for i in range(len(memory)):
            self.memory[i] = memory[i]
        self.memory_size = MEMORY_SIZE

        self.alu = Alu()
        self.interruption_controller = InterruptionController()

        self.input_buffer = 0
        self.output_buffer = []

    def signal_latch_pc(self, value: int) -> None:
        """ Защёлкнуть значение в Program Counter """
        self.pc = value

    def signal_write_memory(self, address: int, value: int) -> None:
        """ Записать значение в память """
        assert address < self.memory_size, f"Memory doesn't have cell with index {address}"
        self.memory[address] = value

    def signal_read_memory(self, address: int) -> int:
        """ Прочитать значение из памяти """
        assert address < self.memory_size, f"Memory doesn't have cell with index {address}"
        return self.memory[address]



class ControlUnit:

def initiate_interruption(control_unit, input_tokens):
    if len(input_tokens) != 0:
        next_token = input_tokens[0]
        if control_unit.tick_counter >= next_token[0]:
            control_unit.data_path.interruption_controller.generate_interruption(1)
            if next_token[1]:
                control_unit.data_path.input_buffer = ord(next_token[1])
            else:
                control_unit.data_path.input_buffer = 0
            return input_tokens[1:]
    return input_tokens
def simulation(code, input_tokens):
    data_path = DataPath(code)
    control_unit = ControlUnit(data_path)

    control_unit.initialization_cycle()

    instruction_counter = 0
    try:
        while instruction_counter < INSTRUCTION_LIMIT:
            input_tokens = initiate_interruption(control_unit, input_tokens)
            control_unit.check_and_handle_interruption()
            control_unit.decode_and_execute_instruction()
            instruction_counter += 1
    except StopIteration:
        pass

    if instruction_counter == INSTRUCTION_LIMIT:
        logging.warning("Instruction limit reached")

    return data_path.output_buffer, instruction_counter, control_unit.tick_counter


def main(code_file: str, input_file: str):
    code = read_code(code_file)
    with open(input_file, encoding="utf-8") as f:
        input_text = f.read().strip()
        if not input_text:
            input_tokens = []
        else:
            input_tokens = eval(input_text)

    output, instruction_counter, ticks = simulation(code, input_tokens)

    print("".join(output) + "\n")
    print(f"instr_counter: {instruction_counter} ticks: {ticks}")


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    assert len(sys.argv) == 3, "Wrong arguments: machine.py <code_file> <input_file>"
    _, code_file, input_file = sys.argv
    main(code_file, input_file)
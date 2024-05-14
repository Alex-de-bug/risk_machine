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
        self.ar = 0  #13
        self.ir = {}  #14
        self.ipc = 0  #15
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
        if 0 <= number <= 12:
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
        """ Отделение операнада из инструкции"""
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


class InterruptionController:
    interruption: bool = None
    interruption_vector_address: int = None

    def __init__(self):
        self.interruption = False
        self.interruption_vector_address = 0

    def generate_interruption(self, number: int) -> None:
        self.interruption = True
        self.interruption_vector_address = number


class PortController:
    port_0: int = None
    port_1: int = None

    def __init__(self):
        self.port_0 = 0
        self.port_1 = 0

    @staticmethod
    def int_signal(interruption_controller, address: int) -> None:
        """  Генерация прерывания """
        interruption_controller.generate_interruption(address)

    def read_value(self, buffer: int) -> int:
        self.port_0 = buffer
        return self.port_0

    def write_value(self, char: chr) -> None:
        self.port_0 = char


class DataPath:
    register_file: RegistersFile = None
    pc = None
    memory = None
    memory_size = None
    alu: Alu = None
    interruption_controller: InterruptionController = None
    input_buffer = None
    output_buffer = None
    port_controller: PortController = None

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

        self.port_controller = PortController()

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

    def signal_read_port(self, address: int) -> int:
        """ Прочитать значение из порта """
        if address == INPUT_PORT_ADDRESS:
            return self.port_controller.read_value(self.input_buffer)
        raise ValueError("PortAddressError")

    def signal_write_port(self, address: int, value: int) -> bool:
        """  Вывод значения в порт """
        if address == OUTPUT_PORT_ADDRESS:
            character = chr(value)
            self.port_controller.write_value(character)
            logging.debug("output: %s << %s", repr("".join(self.output_buffer)), repr(character))
            self.output_buffer.append(character)
            return True
        raise ValueError("PortAddressError")


class ControlUnit:
    tick_counter: int = None

    interruption_enabled: bool = None

    handling_interruption: bool = None

    data_path: DataPath = None

    current_instruction: Opcode = None

    current_operand: int = None

    instruction_executors = None

    def __init__(self, data_path: DataPath):
        self.tick_counter = 0
        self.interruption_enabled = False
        self.handling_interruption = False
        self.data_path = data_path
        self.instruction_executors = {
            # Opcode.LOAD: self.execute_load,
            # Opcode.STORE: self.execute_store,
            #
            # Opcode.ADD: self.execute_binary_math_instruction,
            # Opcode.SUB: self.execute_binary_math_instruction,
            # Opcode.MOD: self.execute_binary_math_instruction,
            # Opcode.INC: self.execute_unary_math_instruction,
            # Opcode.CMP: self.execute_cmp,
            #
            # Opcode.EI: self.execute_ei,
            # Opcode.DI: self.execute_di,
            # Opcode.IN: self.execute_in,
            # Opcode.OUT: self.execute_out,
            #
            # Opcode.JZ: self.execute_jz,
            # Opcode.JNZ: self.execute_jnz,
            # Opcode.JMP: self.execute_jmp,
            #
            # Opcode.MOVE: self.execute_move,
            #
            # Opcode.HALT: self.execute_halt,
            #
            # Opcode.IRET: self.execute_iret,
        }

    def tick(self):
        self.tick_counter += 1
        registers_repr = "TICK: {:3} PC: {:3} Z_FLAG: {:3} \n r0: {:3}  r1: {:3}  r2: {:3} r3: {:3} r4: {:3} r5: {:3} r6: {:3} r7: {:3} r8: {:3} r9: {:3} r10: {:3} r11: {:3} r12: {:3} ar: {:3} ir: {:3} ipc: {:3} ".format(
            str(self.tick_counter),
            str(self.data_path.pc),
            int(self.data_path.alu.zero_flag),
            str(self.data_path.register_file.r0),
            str(self.data_path.register_file.r1),
            str(self.data_path.register_file.r2),
            str(self.data_path.register_file.r3),
            str(self.data_path.register_file.r4),
            str(self.data_path.register_file.r5),
            str(self.data_path.register_file.r6),
            str(self.data_path.register_file.r7),
            str(self.data_path.register_file.r8),
            str(self.data_path.register_file.r9),
            str(self.data_path.register_file.r10),
            str(self.data_path.register_file.r11),
            str(self.data_path.register_file.r12),
            str(self.data_path.register_file.ar),
            str(self.data_path.register_file.ir.get("opcode")),
            str(self.data_path.register_file.ipc),
        )

        port_0 = "PORT_0: {}".format(self.data_path.port_controller.port_0)
        port_1 = "PORT_1: {}".format(self.data_path.port_controller.port_1)

        instruction_repr = self.current_instruction

        if self.current_operand is not None:
            instruction_repr += " {}".format(self.current_operand)

        print("{} \t instruction: {}\n\t   {}\n\t   {}".format(registers_repr, instruction_repr, port_0, port_1))

    def initialization_cycle(self):
        data_out = self.data_path.signal_read_memory(self.data_path.pc)
        self.current_instruction = Opcode(data_out.get("opcode"))
        self.data_path.register_file.latch_reg_ir(data_out)
        self.tick()
        self.data_path.register_file.sel_right_reg(14)
        address = self.data_path.alu.cut_operand(self.data_path.register_file.right_out)
        self.tick()
        self.data_path.register_file.latch_reg_n(13, address)
        self.data_path.register_file.sel_right_reg(13)
        alu_result = self.data_path.alu.perform(0, self.data_path.register_file.right_out, Opcode("add"))
        self.data_path.signal_latch_pc(alu_result)
        self.tick()




def initiate_interruption(control_unit, input_tokens):
    if len(input_tokens) != 0:
        next_token = input_tokens[0]
        if control_unit.tick_counter >= next_token[0]:
            address = control_unit.data_path.memory[-1].get("int1")
            control_unit.data_path.port_controller.int_signal(control_unit.data_path.interruption_controller, address)
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
    # try:
    #     while instruction_counter < INSTRUCTION_LIMIT:
    #         input_tokens = initiate_interruption(control_unit, input_tokens)
    #         control_unit.check_and_handle_interruption()
    #         control_unit.decode_and_execute_instruction()
    #         instruction_counter += 1
    # except StopIteration:
    #     pass
    #
    # if instruction_counter == INSTRUCTION_LIMIT:
    #     logging.warning("Instruction limit reached")

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

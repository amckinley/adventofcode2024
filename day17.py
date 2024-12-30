import operator
import itertools
import sys

from textual.app import App, ComposeResult
from textual.widgets import Footer, Label, ListItem, ListView

class ListViewExample(App):
    CSS_PATH = "list_view.tcss"

    def __init__(self, computer):
        super().__init__()
        self.computer = computer

    def compose(self) -> ComposeResult:
        labels = []
        for o in self.computer.get_program():
            labels.append(ListItem(Label(str(o))))

        yield ListView(*labels)
        yield Footer()



class Computer(object):
    def __init__(self, reg_a: int, reg_b: int, reg_c: int, program: list[int]):
        self.reg_a = reg_a
        self.reg_b = reg_b
        self.reg_c = reg_c
        self.program = program
        self.ptr = 0
        self.output = []
        self.op_name_map = {
            0: 'adv',
            1: 'bxl',
            2: 'bst',
            3: 'jnz',
            4: 'bxc',
            5: 'out',
            6: 'bdv',
            7: 'cdv'
        }

    def run(self):
        while self.ptr < len(self.program):
            op = self.program[self.ptr]
            arg = self.program[self.ptr+1]
            steps = self._execute_instruction(op, arg)
            if steps == -1:
                # print('huh')
                raise Exception("no match")
            # print(self.get_output())
            self.ptr += steps


    def get_program(self):
        combo_map = {
            0: 0,
            1: 1,
            2: 2,
            3: 3,
            4: 'reg_a',
            5: 'reg_b',
            6: 'reg_c'
        }


        program = []
        for op, arg in itertools.batched(self.program, 2):
            op_name = self.op_name_map[op]
            arg_name = combo_map[arg]

            match op:
                # adv (division)
                case 0:
                    human = "reg_a = reg_a // (2 ** {})".format(arg_name)

                # bxl (bitwise XOR)
                case 1:
                    human = "reg_b = reg_b ^ {}".format(arg_name)

                # bst (modulo 8)
                case 2:
                    human = "reg_b = {} % 8".format(arg_name)

                # jnz (jump not zero)
                case 3:
                    human = ''

                # bxc (bitwise XOR)
                case 4:
                    human = "reg_b = reg_b ^ reg_c"

                # out (output)
                case 5:
                    human = "output += {} % 8".format(arg_name)

                # bdv (division)
                case 6:
                    human = "reg_b = reg_a // (2 ** {})".format(arg_name)

                # cdv (division)
                case 7:
                    human = "reg_x = reg_a // (2 ** {})".format(arg_name)

            program.append(f'{op_name} {arg_name} # {human}\n')

        return program


    def _execute_instruction(self, op, arg):
        # print("executing {} {}".format(op_name_map[op], arg))

        match op:
            # adv (division)
            case 0:
                res = operator.floordiv(self.reg_a, 2 ** self._decode_combo(arg))
                self.reg_a = res
                return 2

            # bxl (bitwise XOR)
            case 1:
                res = operator.xor(self.reg_b, arg)
                self.reg_b = res
                return 2

            # bst (modulo 8)
            case 2:
                res = operator.mod(self._decode_combo(arg), 8)
                self.reg_b = res
                return 2

            # jnz (jump not zero)
            case 3:
                if self.reg_a != 0:
                    self.ptr = arg
                    return 0
                return 2

            # bxc (bitwise XOR)
            case 4:
                res = operator.xor(self.reg_b, self.reg_c)
                self.reg_b = res
                return 2

            # out (output)
            case 5:
                res = operator.mod(self._decode_combo(arg), 8)
                self.add_output(res)
                return 2

            # bdv (division)
            case 6:
                res = operator.floordiv(self.reg_a, 2 ** self._decode_combo(arg))
                self.reg_b = res
                return 2

            # cdv (division)
            case 7:
                res = operator.floordiv(self.reg_a, 2 ** self._decode_combo(arg))
                self.reg_c = res
                return 2


    def _decode_combo(self, arg):
        combo_map = {
            0: 0,
            1: 1,
            2: 2,
            3: 3,
            4: self.reg_a,
            5: self.reg_b,
            6: self.reg_c
        }
        if arg not in combo_map:
            raise ValueError('tried to decode an arg of 7')
        return combo_map[arg]

    def get_output(self):
        return ','.join([str(o) for o in self.output])

    def get_registers(self):
        return "Register A: {}\nRegister B: {}\nRegister C: {}".format(self.reg_a, self.reg_b, self.reg_c)

    def get_state(self):
        return self.get_registers() + "\n" + self.get_output()

    def add_output(self, out):
        expected = self.program[len(self.output)]
        # print("calling add output with {}, expecting {}".format(out, expected))
        if out != expected:
            raise Exception("failed to match")
        self.output.append(out)

# def main():
# ran up to 8440750000
#     with open('day17_input.txt') as f:
#         reg_a = int(f.readline().split(':')[1].strip())
#         reg_b = int(f.readline().split(':')[1].strip())
#         reg_c = int(f.readline().split(':')[1].strip())
#         f.readline()
#         program = f.readline().split(':')[1].strip()
#         program = [int(op) for op in program.split(',')]

#         a_val = 0
#         while True:
#             if a_val % 10000 == 0:
#                 print('trying val {}'.format(a_val))
#             comp = Computer(a_val, reg_b, reg_c, program)
#             try:
#                 comp.run()
#                 if comp.output != comp.program:
#                     a_val += 1
#                     continue
#                 print("found it: {}".format(a_val))
#                 return
#             except:
#                 a_val += 1
#                 continue


def main():
    comp = None
    with open('input/day17_input_ex.txt') as f:
        reg_a = int(f.readline().split(':')[1].strip())
        reg_b = int(f.readline().split(':')[1].strip())
        reg_c = int(f.readline().split(':')[1].strip())
        f.readline()
        program = f.readline().split(':')[1].strip()
        program = [int(op) for op in program.split(',')]

        comp = Computer(reg_a, reg_b, reg_c, program)
    app = ListViewExample(comp)
    app.run()


if __name__ == '__main__':
    main()

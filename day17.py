import operator
import itertools
import sys

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Static, Button, ListView, ListItem, Label, Input
from textual.containers import Container, Horizontal
from textual.reactive import reactive
from rich.text import Text

class JumpLine(Static):
    """Widget to render jump lines for jnz instructions."""

    def __init__(self, *args, **kwargs):
        super().__init__("", *args, **kwargs)
        self.jump_map = {}

    def update_jump_map(self, jump_map):
        """Update the jump map."""
        self.jump_map = jump_map
        self.refresh()

    def render(self) -> Text:
        """Render jump lines."""
        lines = []
        if hasattr(self, "code_view"):
            for line_number in range(len(self.jump_map)):  # Corrected to use item_count
                if line_number in self.jump_map:
                    target = self.jump_map[line_number]
                    if target > line_number:
                        lines.append(Text(">─┐", style="#e06c75"))
                    else:
                        lines.append(Text(">─┘", style="#e06c75"))
                elif any(line_number > start and line_number < end for start, end in self.jump_map.items() if end > start):
                    lines.append(Text("│  ", style="#e06c75"))
                elif any(line_number < start and line_number > end for start, end in self.jump_map.items() if end < start):
                    lines.append(Text("│  ", style="#e06c75"))
                else:
                    lines.append(Text("   "))
            return Text("\n").join(lines)
        else:
            return Text("")

class DebuggerApp(App):
    """Textual debugger app for a simple assembly language."""
    CSS_PATH = "debugger.tcss"

    def __init__(self, computer):
        super().__init__()
        self.computer = computer
        self.instruction_ptr = 0
        self.total_steps = 0
        self.output_buffer = ""

    def compose(self) -> ComposeResult:
        """Create the UI components."""
        yield Header()
        yield Footer()

        # Main UI layout
        yield Container(
            Horizontal(
                Static("Code:", id="code-title"),
                Static("Registers:", id="registers-title"),
                Static("Info:", id="info-title"),
                id="titles"
            ),
            Horizontal(
                # No more VerticalScroll, just a Horizontal container
                Horizontal(
                    JumpLine(id="jump-line"),
                    ListView(*[
                        ListItem(Label(line))
                        for line in self.formatted_code_lines()
                    ], id="code-view", disabled=True),
                    id="code-container"
                ),
                Container(
                    Static(self.computer.get_registers(), id="register-view"),
                    Container(
                        Input(placeholder="Reg A", id="reg-a-input"),
                        Input(placeholder="Reg B", id="reg-b-input"),
                        Input(placeholder="Reg C", id="reg-c-input"),
                        Button("Set Registers", id="set-registers-button"),
                        id="register-inputs",
                    ),
                    Static("Output:", id="output-label"),
                    Static(id="output-view"),
                    id="registers-container"
                ),
                Container(
                    Static(f"Instruction Pointer: {self.instruction_ptr}", id="ip-view"),
                    Static(f"Total Steps: {self.total_steps}", id="steps-view"),
                    id="info-container"
                ),
                id="main-container"
            ),
            Horizontal(
                Button("Step", id="step-button", variant="primary"),
                Button("Step (5)", id="step-5-button", variant="primary"),
                Button("Step (10)", id="step-10-button", variant="primary"),
                Button("Run", id="run-button", variant="primary"),
                Button("Reset", id="reset-button", variant="primary"),
                Button("Quit", id="quit-button", variant="error"),
                id="button-container"
            )
        )

    def on_mount(self) -> None:
        """UI setup after mounting."""
        self.check_terminal_size()
        self.update_highlighted_line()
        self.update_jump_lines()

        # Set the code_view attribute for jump_line
        jump_line = self.query_one("#jump-line")
        jump_line.code_view = self.query_one("#code-view")

    def check_terminal_size(self):
        """Check if there's enough space to render the UI."""
        code_lines = len(self.formatted_code_lines())
        required_height = code_lines + 10  # 10 is an estimate of the other UI elements

        if required_height > self.size.height:
            self.exit(f"Error: Not enough vertical space to display the code. Required: {required_height}, Available: {self.size.height}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "step-button":
            self.step_forward(1)
        elif event.button.id == "step-5-button":
            self.step_forward(5)
        elif event.button.id == "step-10-button":
            self.step_forward(10)
        elif event.button.id == "run-button":
            self.run_program()
        elif event.button.id == "reset-button":
            self.reset_program()
        elif event.button.id == "quit-button":
            self.exit()
        elif event.button.id == "set-registers-button":
            self.set_registers()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id in ["reg-a-input", "reg-b-input", "reg-c-input"]:
            self.set_registers()

    def step_forward(self, steps):
        """Execute one step of the program."""
        try:
            self.computer.run(steps=steps)
            self.instruction_ptr = self.computer.ptr
            self.total_steps += steps
            self.update_ui()

            if self.instruction_ptr >= len(self.computer.program):
                self.disable_buttons()
        except Exception as e:
            self.handle_execution_error(e)

    def run_program(self):
        """Run the program until it terminates."""
        try:
            steps_to_end = len(self.computer.program) - self.instruction_ptr
            self.computer.run()
            self.instruction_ptr = self.computer.ptr
            self.total_steps += steps_to_end // 2
            self.update_ui()
            self.disable_buttons()
        except Exception as e:
            self.handle_execution_error(e)

    def reset_program(self):
        """Reset the program to its initial state."""
        self.computer.reset()
        self.instruction_ptr = 0
        self.total_steps = 0
        self.update_ui()
        self.reenable_buttons()

    def set_registers(self):
        """Set the computer's registers based on user input."""
        try:
            reg_a = int(self.query_one("#reg-a-input").value)
            reg_b = int(self.query_one("#reg-b-input").value)
            reg_c = int(self.query_one("#reg-c-input").value)
            self.computer.reg_a = reg_a
            self.computer.reg_b = reg_b
            self.computer.reg_c = reg_c
            self.update_ui()
        except ValueError:
            self.handle_execution_error("Invalid register input")

    def update_ui(self):
        """Update register, output, and code views."""
        self.update_register_display()
        self.update_output_view()
        self.update_highlighted_line()
        self.update_info_view()
        self.update_jump_lines()

    def update_output_view(self):
        """Update the output view."""
        output_str = self.computer.get_output()
        self.query_one("#output-view").update(output_str)

    def update_highlighted_line(self):
        """Highlight the current instruction in the code view."""
        code_view = self.query_one("#code-view")
        code_view.index = self.instruction_ptr // 2

    def update_info_view(self):
        """Update instruction pointer and total steps display."""
        self.query_one("#ip-view").update(f"Instruction Pointer: {self.instruction_ptr}")
        self.query_one("#steps-view").update(f"Total Steps: {self.total_steps}")

    def handle_execution_error(self, error):
        """Display an error message (e.g., in a popup or a dedicated area)."""
        self.query_one("#output-view").update(f"Error: {error}")
        self.disable_buttons()

    def disable_buttons(self):
        """Disable all step/run buttons."""
        self.query_one("#step-button").disabled = True
        self.query_one("#step-5-button").disabled = True
        self.query_one("#step-10-button").disabled = True
        self.query_one("#run-button").disabled = True
        self.query_one("#set-registers-button").disabled = True

    def reenable_buttons(self):
        """Turn all the buttons back on after a reset."""
        self.query_one("#step-button").disabled = False
        self.query_one("#step-5-button").disabled = False
        self.query_one("#step-10-button").disabled = False
        self.query_one("#run-button").disabled = False
        self.query_one("#set-registers-button").disabled = False

    def formatted_code_lines(self):
        """Format code lines for display in the ListView."""
        formatted_lines = []
        for line_number, op_name, arg_name, human in self.computer.get_program():
            formatted_line = f"{line_number:<4} {op_name:<6} {arg_name:<8} # {human}"
            formatted_lines.append(formatted_line)
        return formatted_lines

    def update_jump_lines(self):
        """Update the jump lines to the left of the code."""
        jump_map = self.computer.get_jump_map()
        code_view = self.query_one("#code-view")
        jump_line = self.query_one("#jump-line")
        jump_line.update_jump_map(jump_map)
        jump_line.code_view = code_view
        jump_line.refresh()

    def update_register_display(self):
        """Update the register display with decimal, binary, and hex values."""
        register_view = self.query_one("#register-view")
        register_view.update(self.get_registers_display())

    def get_registers_display(self):
        """Format the register values in decimal, binary, and hexadecimal."""
        reg_a = self.computer.reg_a
        reg_b = self.computer.reg_b
        reg_c = self.computer.reg_c

        return (f"Reg A: {reg_a:10} (0b{reg_a:032b}) (0x{reg_a:08x})\n"
                f"Reg B: {reg_b:10} (0b{reg_b:032b}) (0x{reg_b:08x})\n"
                f"Reg C: {reg_c:10} (0b{reg_c:032b}) (0x{reg_c:08x})")

class Computer(object):
    def __init__(self, reg_a: int, reg_b: int, reg_c: int, program: list[int]):
        self.reg_a = reg_a
        self.reg_b = reg_b
        self.reg_c = reg_c
        self._orig_reg = [reg_a, reg_b, reg_c]
        self.program = program
        self.ptr = 0
        self.output = []
        self.steps_taken = 0
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

    def run(self, steps=-1):
        while self.ptr < len(self.program):
            op = self.program[self.ptr]
            arg = self.program[self.ptr+1]
            steps_done = self._execute_instruction(op, arg)
            self.steps_taken += 1
            if steps_done == -1:
                raise Exception("no match")
            self.ptr += steps_done

            if steps > 0:
                steps -= 1
                if not steps:
                    break

    def reset(self):
        self.ptr = 0
        self.steps_taken = 0
        self.output = []
        self.reg_a, self.reg_b, self.reg_c = self._orig_reg

    def get_program(self):
        combo_map = {
            0: '0',
            1: '1',
            2: '2',
            3: '3',
            4: 'reg_a',
            5: 'reg_b',
            6: 'reg_c'
        }

        program = []
        line_number = 0
        for op, arg in itertools.batched(self.program, 2):
            op_name = self.op_name_map[op]
            arg_name = combo_map.get(arg, str(arg))

            match op:
                # adv (division)
                case 0:
                    human = "reg_a = reg_a // (2 ** {})".format(arg_name)

                # bxl (bitwise XOR with literal)
                case 1:
                    human = "reg_b = reg_b ^ {} (literal)".format(arg_name)

                # bst (modulo 8)
                case 2:
                    human = "reg_b = {} % 8".format(arg_name)

                # jnz (jump not zero)
                case 3:
                    human = "if reg_a != 0: jump to {} (literal)".format(arg_name)

                # bxc (bitwise XOR)
                case 4:
                    human = "reg_b = reg_b ^ reg_c  # (operand ignored)"

                # out (output)
                case 5:
                    human = "output += {} % 8".format(arg_name)

                # bdv (division)
                case 6:
                    human = "reg_b = reg_a // (2 ** {})".format(arg_name)

                # cdv (division)
                case 7:
                    human = "reg_c = reg_a // (2 ** {})".format(arg_name)

            program.append((line_number, op_name, arg_name, human))
            line_number += 1

        return program

    def get_jump_map(self):
        """Return a map of jnz instructions and their target lines."""
        jump_map = {}
        line_number = 0
        for op, arg in itertools.batched(self.program, 2):
            if op == 3:  # jnz instruction
                jump_map[line_number] = arg
            line_number += 1
        return jump_map

    def _execute_instruction(self, op, arg):
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
        self.output.append(out)

def main():
    comp = None
    with open('input/day17_input.txt') as f:
        reg_a = int(f.readline().split(':')[1].strip())
        reg_b = int(f.readline().split(':')[1].strip())
        reg_c = int(f.readline().split(':')[1].strip())
        f.readline()
        program = f.readline().split(':')[1].strip()
        program = [int(op) for op in program.split(',')]

        comp = Computer(reg_a, reg_b, reg_c, program)
        # comp.run()
        # print(comp.get_output())
    app = DebuggerApp(comp)
    app.run()

if __name__ == '__main__':
    main()

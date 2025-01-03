import re
from termcolor import colored
from math import prod
from collections import defaultdict
from time import sleep

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Static, Button
from textual.containers import Container, Horizontal

class MapApp(App):
    def __init__(self, map):
        super().__init__()
        self.map = map

    def on_mount(self) -> None:
        """Event handler called when widget is added to the app."""
        self.update_timer = self.set_interval(1 / 60, self.step_forward, pause=False)

    def render(self):
        return Text("Steps:"+ self.map.total_steps + "\n" + self.map.get_state())

    def compose(self) -> ComposeResult:
        """Create the UI components."""
        yield Header()
        yield Footer()

        yield Container(
            Horizontal(
                Button("Step", id="step-button", variant="primary"),
                Static(self.map.get_state(), id="output-view")))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == 'step-button':
            self.step_forward(1)

    def step_forward(self, steps=1):
        try:
            self.map.step(steps)
            output_str = "Steps: {}\n".format(self.map.total_steps) + self.map.get_state()
            self.query_one("#output-view").update(output_str)
        except ValueError:
            self.handle_execution_error("Invalid register input")

    def handle_execution_error(self, error):
        """Display an error message (e.g., in a popup or a dedicated area)."""
        self.query_one("#output-view").update(f"Error: {error}")
        # self.disable_buttons()

class BathroomMap(object):
    def __init__(self, bot_specs, width, height):
        self.bot_specs = bot_specs
        self.width = width
        self.height = height
        self.row_map = None
        self.total_steps = 0

    def get_state(self, highlight=None):
        if not highlight:
            highlight = set()
        buf = ''
        for r in range(self.height):
            for c in range(self.width):
                bot_count = self.bot_count(r, c)
                char = None
                if bot_count > 0:
                    char = str(bot_count)
                else:
                    char = '.'

                if (r, c) in highlight:
                    char = colored(char, "red")
                buf += char
            buf += '\n'
        return buf

    def bot_count(self, row, col):
        """
        Returns the number of bots present at a given location
        """
        acc = 0
        for s in self.bot_specs:
            if s['r_pos'] == row and s['c_pos'] == col:
                acc += 1
        return acc

    def get_row_bot_count(self, row):
        if self.row_map:
            return self.row_map[row]
        return len([s for s in self.bot_specs if s['r_pos'] == row])

    def step(self, step_count=1):
        row_map = defaultdict(int)
        for s in self.bot_specs:
            new_row = (s['r_pos'] + (step_count * s['r_vel'])) % self.height
            new_col = (s['c_pos'] + (step_count * s['c_vel'])) % self.width
            s['r_pos'] = new_row
            s['c_pos'] = new_col
            row_map[new_row] += 1
        self.row_map = row_map
        self.total_steps += step_count

    def get_safety_factor(self):
        # correct boundaries for 7 x 11:
        # 0, 3, 0, 5
        quad_boundaries = [
            #r_start,              r_end,            c_start,             c_end
            (0,                    self.height // 2, 0,                   self.width // 2), # ▟
            (0,                    self.height // 2, self.width // 2 + 1, self.width),      # ▙
            (self.height // 2 + 1, self.height,      0,                   self.width // 2), # ▜
            (self.height // 2 + 1, self.height,      self.width // 2 + 1, self.width)       # ▛
        ]
        quad_bot_counts = []
        for r_s, r_e, c_s, c_e in quad_boundaries:
            # print(r_s, r_e, c_s, c_e)
            bot_count = 0
            highlight = set()
            for row in range(r_s, r_e):
                for col in range(c_s, c_e):
                    highlight.add((row, col))
                    bot_count += self.bot_count(row, col)
            quad_bot_counts.append(bot_count)
            # print(self.get_state(highlight=highlight))
        return prod(quad_bot_counts)

    def xmas_scan(self):
        while True:
            if self.total_steps % 1000 == 0:
                print(self.total_steps)
            incr_cnt = 0
            bot_count = -1
            for row in range(self.height):
                row_cnt = self.get_row_bot_count(row)
                if row_cnt > bot_count:
                    incr_cnt += 1
                    bot_count = row_cnt

            if incr_cnt > 60:
                print(steps)
                print(self.get_state())
                input("good?")

            self.step()


def main():

    r = re.compile(r'p=(?P<c_pos>\d+),(?P<r_pos>\d+) v=(?P<c_vel>-?\d+),(?P<r_vel>-?\d+)')
    # with open('day14_input_ex.txt', 'r') as f:
    #     specs = []
    #     for l in f.readlines():
    #         gs = r.match(l).groupdict()
    #         gs = {k: int(v) for k, v in gs.items()}
    #         specs.append(gs)
    #     bm = BathroomMap(specs, 11, 7)
    #     # print(bm.get_state())
    #     bm.step(100)
    #     print(bm.get_state())
    #     for r in range(11):
    #         print(bm.get_row_bot_count(r))
    #     # print(bm.get_safety_factor())
    input_sizes = {
        'input/day14_input_ex.txt': (7, 11),
        'input/day14_input.txt': (103, 101)
    }
    f_name = 'input/day14_input.txt'
    (rows, cols) = input_sizes[f_name]

    with open(f_name, 'r') as f:
        specs = []
        for l in f.readlines():
            gs = r.match(l).groupdict()
            gs = {k: int(v) for k, v in gs.items()}
            specs.append(gs)
        bm = BathroomMap(specs, cols, rows)
        app = MapApp(bm)
        app.run()



if __name__ == '__main__':
    main()

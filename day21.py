import itertools
from collections import deque
from functools import cache

class Keypad(object):
    STEPS = {
        '>': (0, 1),  # right
        'v': (1, 0),  # down
        '<': (0, -1), # left
        '^': (-1, 0)  # up
    }

    def __init__(self):
        self.invalid_locs = set()
        self.key_pos_map = None
        self.pressed = []

    def get_key_on(self):
        row, col = self.loc
        return self.layout[row][col]


    def get_key_pos(self, key_name):
        if not self.key_pos_map:
            m = {}
            for r_idx, r in enumerate(self.layout):
                for c_idx, k in enumerate(r):
                    m[k] = (r_idx, c_idx)

            self.key_pos_map = m

        return self.key_pos_map[key_name]

    def get_neighbors(self, row, col):
        neighbors = []
        for d, off in self.STEPS.items():
            r_off, c_off = off
            c_row, c_col = (row + r_off, col + c_off)
            if self.is_valid(c_row, c_col):
                neighbors.append((c_row, c_col, d))
        return neighbors

    def is_valid(self, row, col):
        if row < 0 or row >= self.height:
            return False
        if col < 0 or col >= self.width:
            return False

        if (row, col) in self.invalid_locs:
            return False

        return True

    def move(self, move_d):
        row, col = self.loc
        r_off, c_off = self.STEPS[move_d]
        c_row, c_col = (row + r_off, col + c_off)
        if not self.is_valid(c_row, c_col):
            raise ValueError(f'oops, ({c_row}, {c_col}) is out of bounds')
        self.loc = c_row, c_col

    def press(self):
        row, col = self.loc
        button_name = self.layout[row][col]
        self.pressed.append(button_name)

    @cache
    def get_cached_shortest_path(self, pad_type, start_key, end_key):
        """
        BFS to find the shortest path between start and end keys. Cache
        this so we only have to compute it once.
        """
        start = self.get_key_pos(start_key)
        end = self.get_key_pos(end_key)

        visited = set()
        q = deque()
        q.append((start, []))
        visited.add(start)

        while q:
            cur, path = q.popleft()
            if cur == end:
                return ''.join(path)

            for n_row, n_col, d in self.get_neighbors(*cur):
                if (n_row, n_col) in visited:
                    continue
                n = (n_row, n_col)
                q.append((n, path + [d]))

        raise ValueError("no path??")

    def find_path_for_output(self, output):
        """
        Returns a string of button presses on this keypad needed to generate the desired output.
        """
        # prepend the key we're currently on
        output = self.get_key_on() + output
        path = []

        for a, b in itertools.pairwise(output):
            ab_path = self.get_shortest_path(a, b)
            # print(f'path from {a} {b} is {ab_path}')
            path.append(ab_path)

        return 'A'.join(path) + 'A'


class NumKeypad(Keypad):
    def __init__(self):
        super().__init__()
        self.loc = (3, 2)
        self.width = 3
        self.height = 4
        self.invalid_locs.add((3, 0))
        self.layout = [
            ['7',  '8', '9'],
            ['4',  '5', '6'],
            ['1',  '2', '3'],
            [None, '0', 'A']
        ]

    def get_shortest_path(self, start_key, end_key):
        return self.get_cached_shortest_path('num', start_key, end_key)

class DirKeypad(Keypad):
    def __init__(self):
        super().__init__()
        self.loc = (0, 2)
        self.width = 3
        self.height = 2
        self.invalid_locs.add((0, 0))
        self.layout = [
            [None, '^', 'A'],
            ['<',  'v', '>'],
        ]

    def get_shortest_path(self, start_key, end_key):
        return self.get_cached_shortest_path('num', start_key, end_key)

def get_top_level_path_len(target_output):
    numpad = NumKeypad()
    numpad_path = numpad.find_path_for_output(target_output)
    # print(len(numpad_path), len('<A^A>^^AvvvA'))

    rad_dpad = DirKeypad()
    rad_dpad_path = rad_dpad.find_path_for_output(numpad_path)
    # print(len(rad_dpad_path), len('v<<A>>^A<A>AvA<^AA>A<vAAA>^A'))

    cold_dpad = DirKeypad()
    cold_dpad_path = cold_dpad.find_path_for_output(rad_dpad_path)
    return len(cold_dpad_path)

def main():
    with open('input/day21_input_ex.txt', 'r') as f:
        acc = 0
        for l in f.readlines():
            l = l.strip()
            p_len = get_top_level_path_len(l)
            num_prefix = int(l[0:3])
            print(f'for code {l}, path of len {p_len}, prefix {num_prefix}')
            acc += p_len * num_prefix

        print(acc)






    # # print(p)
    # # for p_chunk in p:
    # #     for m in p_chunk:
    # #         k.move(m)
    # #     k.press()

    # desired_path = 'A'.join(p) + 'A'
    # print("done with part A, dp = ", desired_path)
    # d_pad = DirKeypad()
    # p2 = d_pad.find_path_for_output(desired_path)

    # print(p2)
    # for p_chunk in p2:
    #     if p_chunk:
    #         for m in p_chunk:
    #             print('moving', m)
    #             d_pad.move(m)
    #     d_pad.press()

    # print(d_pad.pressed)



if __name__ == "__main__":
    main()

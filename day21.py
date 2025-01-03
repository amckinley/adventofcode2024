import itertools
import heapq
from functools import cache
import unittest

class TestPathCost(unittest.TestCase):
    def setUp(self):
        self.k = DirKeypad()

    def test_path_cost(self):
        self.assertEqual(self.k.get_cost_for_path('^^'), 0)
        self.assertEqual(self.k.get_cost_for_path('^<'), 1)
        self.assertEqual(self.k.get_cost_for_path('^>^'), 2)
        self.assertEqual(self.k.get_cost_for_path('^v^'), 2)
        self.assertEqual(self.k.get_cost_for_path('^^^>'), 1)


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
    def get_cost_for_path(self, path):
        """
        Add 1 for each direction change
        """
        acc = 0
        for a, b in itertools.pairwise(path):
            if a != b:
                acc += 1
        return acc

    # XXX: note that this decorator doesnt work correctly because it isnt shared between instances
    @cache
    def get_cached_shortest_path(self, pad_type, start_key, end_key):
        """
        Dijkstra to find the shortest path between start and end keys. Note that we define the path cost as
        the number of direction changes, NOT the number of button pushes.

        This prefers sequences like '^^>' over '^>^', even though these represent the same end position.
        The latter path is more expensive at higher levels of keypads, because its cheaper to repeatedly
        press 'A' rather than moving to a different button.
        """
        start = self.get_key_pos(start_key)
        end = self.get_key_pos(end_key)

        visited = set()
        q = []
        heapq.heappush(q, (0, start, ''))
        visited.add(start)

        while q:
            cost, cur, path = heapq.heappop(q)

            if cur == end:
                # print(f'cost is {cost}, path {path}')
                return path

            for n_row, n_col, d in self.get_neighbors(*cur):
                if (n_row, n_col) in visited:
                    continue
                n = (n_row, n_col)
                new_path = path + d
                new_cost = cost + self.get_cost_for_path(new_path)
                heapq.heappush(q, (new_cost, n, new_path))
                # q.append((n, path + [d]))

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
    def __init__(self, controlled_pad):
        super().__init__()
        self.loc = (0, 2)
        self.width = 3
        self.height = 2
        self.invalid_locs.add((0, 0))
        self.layout = [
            [None, '^', 'A'],
            ['<',  'v', '>'],
        ]
        self.controlled_pad = controlled_pad

    def get_shortest_path(self, start_key, end_key):
        return self.get_cached_shortest_path('num', start_key, end_key)

def get_top_level_path_len(initial_target, num_layers):
    prev_pad = NumKeypad()
    target_path = prev_pad.find_path_for_output(initial_target)

    d_pads_added = 0
    while d_pads_added < num_layers:
        dpad = DirKeypad(prev_pad)
        target_path = dpad.find_path_for_output(target_path)
        d_pads_added += 1

    return len(target_path)

def main():
    """
    guessed 161120, too high

    for code 341A, path of len 72, prefix 341
    for code 803A, path of len 80, prefix 803
    for code 149A, path of len 76, prefix 149
    for code 683A, path of len 68, prefix 683
    for code 208A, path of len 70, prefix 208
    """
    with open('input/day21_input.txt', 'r') as f:
        acc = 0
        for l in f.readlines():
            l = l.strip()
            p_len = get_top_level_path_len(l, 2)
            num_prefix = int(l[0:3])
            print(f'for code {l}, path of len {p_len}, prefix {num_prefix}')
            acc += p_len * num_prefix

        print(acc)


if __name__ == "__main__":
    # unittest.main()
    main()

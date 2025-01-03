from tqdm import tqdm

class Maze(object):
    OFFSETS = [
        (-1, 0), # up
        (0, 1),  # right
        (1, 0),  # down
        (0, -1)] # left

    def __init__(self, lines):
        self.lines = lines
        self.width = len(lines[0])
        self.height = len(lines)
        self.start = None

        for row, l in enumerate(lines):
            if '^' in l:
                self.start = (row, l.index('^'))
        if not self.start:
            raise ValueError('missing start')

    def is_valid(self, row, col):
        if row < 0 or row >= self.height:
            return False
        if col < 0 or col >= self.width:
            return False
        return True

    def run(self):
        row, col = self.start
        visited = set()
        dir_idx = 0 # up

        while True:
            visited.add((row, col))
            r_off, c_off = self.OFFSETS[dir_idx]
            n_row, n_col = row + r_off, col + c_off

            # if next move would leave the maze, we're done
            if not self.is_valid(n_row, n_col):
                break

            # check for an obstacle
            while self.lines[n_row][n_col] == '#':
                dir_idx = (dir_idx + 1) % 4
                r_off, c_off = self.OFFSETS[dir_idx]
                n_row, n_col = row + r_off, col + c_off

            row, col = n_row, n_col
        print(f'exited the maze at {row} {col}, visited {len(visited)}')
        return visited

    def does_create_loop(self, obs_row, obs_col):
        """
        Returns True if adding a loop at (row, col) will create a loop
        """
        row, col = self.start
        dir_idx = 0 # up
        loop_check = set()
        loop_check.add((row, col, dir_idx))

        while True:
            if self.lines[obs_row][obs_col] != '.':
                print(obs_row, obs_col, self.lines[obs_row][obs_col])
                sys.exit()
            r_off, c_off = self.OFFSETS[dir_idx]
            n_row, n_col = row + r_off, col + c_off

            if not self.is_valid(n_row, n_col):
                return False

            # if we've already been to the next cell while facing the current direction,
            # we're in a loop
            if (n_row, n_col, dir_idx) in loop_check:
                return True

            # keep turning until we dont have an obstacle in front of us
            while self.lines[n_row][n_col] == '#' or (obs_row, obs_col) == (n_row, n_col):
                dir_idx = (dir_idx + 1) % 4
                r_off, c_off = self.OFFSETS[dir_idx]
                n_row, n_col = row + r_off, col + c_off

            loop_check.add((n_row, n_col, dir_idx))
            row, col = n_row, n_col

    def part2(self, visited):
        acc = 0
        for row, col in tqdm(visited):
            if (row, col) == self.start:
                continue
            if self.does_create_loop(row, col):
                acc += 1
        return acc

def main():
    with open('input/day6_input.txt', 'r') as f:
        m = Maze([l.strip() for l in f.readlines()])
        visited = m.run()
        print(m.part2(visited))

if __name__ == '__main__':
    main()

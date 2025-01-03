import itertools
import sys
import termcolor


class DiskMap(object):
    def __init__(self, map_str: str):
        self.map_str = map_str

        blocks = []
        free_space_start_idxs = []
        free_blocks_remaining = 0
        file_id = 0

        for vals in itertools.batched(map_str, 2):
            b_len = int(vals[0])
            blocks.extend([file_id] * b_len)
            file_id += 1

            if len(vals) == 2 and int(vals[1]):
                f_len = int(vals[1])
                free_space_start_idxs.append(len(blocks))
                blocks.extend([None] * f_len)
                free_blocks_remaining += f_len

        self.blocks = blocks
        self.free_space_start_idxs = free_space_start_idxs
        self.free_blocks_remaining = free_blocks_remaining

    def __str__(self) -> str:
        # first chunk up the block list
        groups = [list(group) for key, group in itertools.groupby(self.blocks)]

        c_list = list(termcolor.COLORS.keys())
        c_list.remove('black')
        c_list.remove('grey')
        c_idx = 0

        buf = []
        for g in groups:
            if g[0] == None:
                g_str = '.' * len(g)
            else:
                g_str = ''.join([str(i) for i in g])

            b_color = c_list[c_idx]
            c_idx = (c_idx + 1) % len(c_list)
            block_str = termcolor.colored(g_str, b_color)
            buf.append(block_str)

        return ''.join(buf)

    def compact_part1(self) -> None:
        free_block_idx = self.free_space_start_idxs.pop(0)
        src_idx = -1

        # because we delete any trailing free space, this is our exit condition
        while self.free_blocks_remaining > 0:
            # print('before', self)
            # we've exhausted the current free block
            if self.blocks[free_block_idx] != None:
                free_block_idx = self.free_space_start_idxs.pop(0)

            dest_contents = self.blocks.pop()

            # tried to move a free space block
            if not dest_contents:
                self.free_blocks_remaining -= 1
                continue

            # cool, we can do this copy
            print(f'idx is {free_block_idx} len is {len(self.blocks)} fbs is {self.free_blocks_remaining}')
            self.blocks[free_block_idx] = dest_contents
            free_block_idx += 1
            self.free_blocks_remaining -= 1

    def compact_part2(self) -> None:
        pass

    def get_checksum(self) -> int:
        """
        To calculate the checksum, add up the result of multiplying each of these blocks' position with
        the file ID number it contains. The leftmost block is in position 0. If a block contains free space,
        skip it instead.
        """
        acc = 0
        for block_idx, file_id in enumerate(self.blocks):
            if not file_id:
                print('skipping a free block')
                continue
            acc += block_idx * file_id
        return acc

def main():
    # 6400828038148 is too low
    # 6401092019345
    with open('input/day9_input.txt', 'r') as f:
        dm = DiskMap(f.readline().strip())
        # dm = DiskMap('12345')
        # dm = DiskMap('2333133121414131402')
        # print(dm.blocks)
        print(dm.free_space_start_idxs)
        # print(dm)
        dm.compact_part1()
        dm.compact_part2()
        print(dm)
        print(dm.get_checksum())
        # print(dm)


        # dm.compact()
        # print(dm.decompress())
        # # print([str(b) for b in dm.decompress()])

        # dm = DiskMap('2333133121414131402')
        # print(dm.decompress() == '00...111...2...333.44.5555.6666.777.888899')


if __name__ == '__main__':
    main()

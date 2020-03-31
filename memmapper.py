# (C) 2020 by Folkert van Heusden <mail@vanheusden.com>
# released under AGPL v3.0

import sys
from typing import List, Tuple

class memmap:
    def __init__(self, n_pages:int, debug):
        assert n_pages > 0 and n_pages <= 256

        self.n_pages: int = n_pages
        self.debug = debug

        self.mapper: List[int] = [ 3, 2, 1, 0 ]

        self.ram = [ [ 0 for k in range(16384)] for j in range(self.n_pages)]

    def get_n_pages(self):
        return 4

    def split_addr(self, a: int) -> Tuple[int, int]:
        page = self.mapper[a >> 14]
        offset = a & 0x3fff

        return page, offset

    def write_mem(self, a:int, v:int) -> None:
        page, offset = self.split_addr(a)
        if a == 0x340f:
            self.debug('GREPW2B %04x %02x / %02x [%d %d %d %d] %d/%d' % (a, v, self.ram[page][offset], self.mapper[0], self.mapper[1], self.mapper[2], self.mapper[3], a >> 14, page))
        else:
            self.debug('GREPW3 %04x %02x / %02x [%d %d %d %d] %d/%d' % (a, v, self.ram[page][offset], self.mapper[0], self.mapper[1], self.mapper[2], self.mapper[3], a >> 14, page))

        self.ram[page][offset] = v

    def read_mem(self, a: int) -> int:
        page, offset = self.split_addr(a)

        if a == 0x340f:
            self.debug('GREPR2B %04x %02x [%d %d %d %d] %d/%d' % (a, self.ram[page][offset], self.mapper[0], self.mapper[1], self.mapper[2], self.mapper[3], a >> 14, page))

        return self.ram[page][offset]

    def write_io(self, a: int, v: int) -> None:
        self.debug('memmap write %02x: %d' % (a, v))
        self.mapper[a - 0xfc] = v

    def read_io(self, a: int) -> int:
        self.debug('memmap read %02x' % a)
        return self.mapper[a - 0xfc]

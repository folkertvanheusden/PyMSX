# (C) 2020 by Folkert van Heusden <mail@vanheusden.com>
# released under AGPL v3.0

import sys
from typing import List, Tuple

class msxdos2:
    def __init__(self, msxdos2_rom_file, debug):
        print('Loading MSX-DOS2 rom %s...' % msxdos2_rom_file, file=sys.stderr)

        fh = open(msxdos2_rom_file, 'rb')
        self.msxdos2_rom = [ int(b) for b in fh.read() ]
        fh.close()

        assert len(self.msxdos2_rom) == 65536

        self.msxdos2_page: int = 0

        self.debug = debug

    def get_ios(self):
        return [ [ ] , [ ] ]

    def get_name(self):
        return 'MSX-DOS2'

    def get_n_pages(self):
        return 1

    def split_addr(self, a: int) -> Tuple[int, int]:
        assert a >= 0x4000

        bank = a // 0x4000 - 1
        offset = a & 0x3fff

        return bank, offset

    def write_mem(self, a: int, v: int) -> None:
        self.debug('MSX-DOS2: set bank to %d (%d) via %04x' % (v, v & 3, a))
        self.msxdos2_page = v & 3

    def read_mem(self, a: int) -> int:
        bank, offset = self.split_addr(a)

        p = self.msxdos2_page * 0x4000 + offset

        return self.msxdos2_rom[p]

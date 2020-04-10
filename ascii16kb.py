# (C) 2020 by Folkert van Heusden <mail@vanheusden.com>
# released under AGPL v3.0

import sys
from typing import List, Tuple

class ascii16kb:
    def __init__(self, ascii16kb_rom_file, debug):
        print('Loading ASCII-16kB rom %s...' % ascii16kb_rom_file, file=sys.stderr)

        fh = open(ascii16kb_rom_file, 'rb')
        self.ascii16kb_rom = [ int(b) for b in fh.read() ]
        fh.close()

        self.n_pages: int = (len(self.ascii16kb_rom) + 0x3fff) // 0x4000

        self.ascii16kb_pages: List[int] = [ 0, 1 ]

        self.debug = debug

    def get_ios(self):
        return [ [ ] , [ ] ]

    def get_name(self):
        return 'ASCII-16kB'

    def get_n_pages(self):
        return 2

    def split_addr(self, a: int) -> Tuple[int, int]:
        assert a >= 0x4000

        bank = a // 0x4000 - 1
        offset = a & 0x3fff

        return bank, offset

    def write_mem(self, a: int, v: int) -> None:
        if a >= 0x6000 and a < 0x6800:
            self.debug('ASCII 16kB: set bank 0 to %d' % v)
            self.ascii16kb_pages[0] = v

        elif a >= 0x7000 and a < 0x7800:
            self.debug('ASCII 16kB: set bank 1 to %d' % v)
            self.ascii16kb_pages[1] = v

        else:
            self.debug('ASCII-16kB write to %04x not understood' % a)

    def read_mem(self, a: int) -> int:
        bank, offset = self.split_addr(a)

        p = self.ascii16kb_pages[bank] * 0x4000 + offset

        return self.ascii16kb_rom[p]

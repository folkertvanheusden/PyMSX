# (C) 2020 by Folkert van Heusden <mail@vanheusden.com>
# released under AGPL v3.0

import struct
import sys
from enum import Enum, IntFlag, IntEnum
from typing import List

class sunriseide:
    class bytesel(Enum):
        lowbyte = 1
        highbyte = 2

    def __init__(self, disk_rom_file: str, debug, disk_image_file: str):
        print('Loading disk rom %s...' % disk_rom_file, file=sys.stderr)

        fh = open(disk_rom_file, 'rb')
        self.rom = [ int(b) for b in fh.read() ]
        fh.close()
        self.rom_n_pages = len(self.rom) // 0x4000

        self.fh = open(disk_image_file, 'ab+')

        self.which_byte: sunriseide.bytesel = sunriseide.bytesel.lowbyte
        self.word: int = 0

        self.control: int = 0xff

        self.debug = debug

    def get_ios(self):
        return [ [ ] , [ ] ]

    def get_name(self):
        return 'SunRise IDE'

    def write_mem(self, a: int, v: int) -> None:
        if a == 0x7e00 or (a >= 0x7c00 and a <= 0x7dff):  # data
            if self.which_byte == sunriseide.bytesel.lowbyte:
                self.word = (self.word & 0xff00) | v
                self.which_byte = sunriseide.bytesel.highbyte
            else:
                self.word = (self.word & 0x00ff) | (v << 8)
                self.which_byte = sunriseide.bytesel.lowbyte

                # FIXME process word

        elif (a & 0xbf04) == 0x0104:  # control
            self.debug('sunrise-ide: set control to %02x' % v)
            self.control = v

        elif a >= 0x7e00 and a <= 0x7eff:
            reg = a & 0x0f

            self.debug('write %d %02x' % (reg, v))

            if reg == 7:  # command execute register
                pass

        else:
            self.debug('Unexpected write: %04x %02x' % (a, v))

    def read_mem(self, a: int) -> int:
        if (self.control & 1) == 1 and (a == 0x7e00 or (a >= 0x7c00 and a <= 0x7dff)):
            v = None

            if self.which_byte == sunriseide.bytesel.lowbyte:
                v = self.word & 0xff00
                self.which_byte = sunriseide.bytesel.highbyte
            else:
                v = self.word >> 8
                self.which_byte = sunriseide.bytesel.lowbyte

                # FIXME get word

            return v

        elif (self.control & 1) == 1 and a >= 0x7e00 and a <= 0x7eff:
            reg = a & 0x0f

            self.debug('read %d' % reg)

            if reg == 7:  # status register
                return 0

            return 0xff

        else:
            sel_page = (self.control >> 7) | ((self.control >> 6) & 2) | ((self.control >> 5) & 4);

            if sel_page >= self.rom_n_pages:
                sel_page &= self.rom_n_pages - 1
            offset = 0x4000 * sel_page
            return self.rom[a - 0x4000 + offset]

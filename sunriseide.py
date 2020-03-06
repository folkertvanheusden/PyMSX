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
        self.disk_rom = [ int(b) for b in fh.read() ]
        fh.close()
        self.rom_n_pages = len(self.disk_rom) // 0x4000

        self.fh = open(disk_image_file, 'ab+')

        self.which_byte: sunriseide.bytesel = sunriseide.bytesel.lowbyte
        self.word = 0

        self.control = 0xff

        self.debug = debug

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
            self.control = v

        elif a >= 0x7e00:
            reg = a & 0x0f

            print('write', reg, v)

            if reg == 7:  # command execute register
                pass

        else:
            print('Unexpected write: %04x %02x' % (a, v))

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

        elif a >= 0x7e00:
            reg = a & 0x0f

            print('read', reg)

            if reg == 7:  # status register
                return 0

            return 0xff

        else:
            sel_page = self.control >> 5
            if sel_page >= self.rom_n_pages:
                sel_page &= self.rom_n_pages - 1
            offset = 0x4000 * sel_page
            return self.disk_rom[a - 0x4000 + offset]

# (C) 2020 by Folkert van Heusden <mail@vanheusden.com>
# released under AGPL v3.0

import struct
import sys
from enum import Enum, IntFlag
from pagetype import PageType
from typing import List

class disk:
    class T1(IntFlag):
        BUSY = 0x01
        INDEX = 0x02
        TRACK0 = 0x04
        CRCERR = 0x08
        SEEKERR = 0x10
        HEADLOAD = 0x20
        PROT = 0x40
        NOTREADY = 0x80

    class T2(IntFlag):
        BUSY = 0x01
        DRQ = 0x02
        NOTREADY = 0x80

    class BufMode(Enum):
        IDLE = 1
        RW = 2

    class Register(Enum):
        STATUS_CMD = 0x08
        TRACK = 0x09
        SECTOR = 0x0a
        DATA_REGISTER = 0x0b
        FLAGS = 0x0c

    class Cmd(Enum):
        RESTORE = 0
        SEEK = 1
        STEP1 = 2
        STEP2 = 3
        STEP_IN1 = 4
        STEP_IN2 = 5
        STEP_OUT1 = 6
        STEP_OUT2 = 7
        READ1 = 8
        READ2 = 9
        WRITE1 = 10
        WRITE2 = 11
        READ_ADDR = 12
        FORCE_INT = 13
        READ_TRACK = 14
        WRITE_TRACK = 15

    def __init__(self, disk_rom_file: str, debug, disk_image_file: str):
        print('Loading disk rom %s...' % disk_rom_file, file=sys.stderr)

        fh = open(disk_rom_file, 'rb')
        self.disk_rom = [ int(b) for b in fh.read() ]
        fh.close()

        self.fh = open(disk_image_file, 'ab+')

        self.regs: List[int] = [ 0 ] * 16

        self.buffer: List[int] = [ 0 ] * 512
        self.bufp: int = 0
        self.bmode: disk.BufMode = disk.BufMode.IDLE
        self.need_flush: bool = False

        self.tc = None
        self.flags: int = 0

        self.step_dir: int = 1
        self.track: int = 0

        self.debug = debug

    def file_offset(self, side: int, track: int, sector: int) -> int:
        return (sector - 1) * 512 + (track * 9 * 512) + (80 * 9 * 512) * side

    def get_signature(self):
        return (self.disk_rom, PageType.DISK, self)

    def write_mem(self, a: int, v: int) -> None:
        offset = a - 0x4000

        if offset >= 0x3ff0: # HW registers
            reg = offset - 0x3ff0

            self.regs[reg] = v

            if reg == disk.Register.STATUS_CMD:
                command: disk.Cmd = v >> 4
                T: bool = ((v >> 4) & 1) == 1
                h: bool = ((v >> 3) & 1) == 1

                if command == disk.Cmd.RESTORE:
                    self.debug('CMD: restore')
                    self.track = self.regs[disk.Register.TRACK] = 0

                    self.flags = disk.T1.INDEX | disk.T1.TRACK0
                    if h:
                        self.flags |= disk.T1.HEADLOAD

                    self.tc = 1

                elif command == disk.Cmd.SEEK:
                    self.track = self.regs[disk.Register.TRACK] = self.regs[0x0b]
                    self.debug('CMD: seek to %d' % self.track)

                    self.flags = disk.T1.INDEX | (disk.T1.TRACK0 if self.track == 0 else 0)
                    if h:
                        self.flags |= disk.T1.HEADLOAD

                    self.tc = 1

                elif command in (disk.Cmd.STEP1, disk.Cmd.STEP2):
                    self.debug('CMD step %d' % self.step_dir)
                    self.track += self.step_dir

                    if self.track < 0:
                        self.track = 0
                    elif self.track > 79:
                        self.track = 79

                    self.flags = disk.T1.INDEX

                    if self.track == 0:
                        self.flags |= disk.T1.TRACK0

                    if T:
                        self.regs[disk.Register.TRACK] = self.track

                    self.tc = 1

                elif command in (disk.Cmd.STEP_IN1, disk.Cmd.STEP_IN2):
                    self.debug('CMD step in')
                    self.track += 1

                    if self.track > 79:
                        self.track = 79

                    self.step_dir = 1

                    self.tc = 1

                    self.flags = disk.T1.INDEX

                    if T:
                        self.regs[disk.Register.TRACK] = self.track

                elif command in (disk.Cmd.STEP_OUT1, disk.Cmd.STEP_OUT2):
                    self.debug('CMD step out')
                    self.track -= 1

                    if self.track < 0:
                        self.track = 0

                    self.step_dir = -1

                    self.tc = 1

                    self.flags = disk.T1.INDEX
                    if self.track == 0:
                        self.flags |= disk.T1.TRACK0

                    if T:
                        self.regs[disk.Register.TRACK] = self.track

                elif command in (disk.Cmd.READ1, disk.Cmd.READ2):
                    self.debug('CMD read sector')
                    self.bufp = 0
                    self.need_flush = False

                    side = 1 if (self.regs[self.Register.FLAGS] & 0x08) == 0x08 else 0
                    o = self.file_offset(side, self.track, self.regs[disk.Register.SECTOR])
                    self.debug('Read sector %d:%d:%d (offset %d) / %d' % (side, self.track, self.regs[disk.Register.SECTOR], o, self.regs[disk.Register.TRACK]))
                    self.fh.seek(o)
                    for i in range(0, 512):
                        b = self.fh.read(1)

                        if len(b) == 0:
                            self.buffer[i] = 0
                        else:
                            self.buffer[i] = struct.unpack('<B', b)[0]
                            print('%c' % self.buffer[i], end='')
                    print('')

                    self.tc = 2

                    self.flags |= disk.T2.BUSY | disk.T2.DRQ

                    self.bmode = disk.BufMode.RW

                elif command in (disk.Cmd.WRITE1, disk.Cmd.WRITE2):
                    self.debug('CMD write sector')
                    self.bufp = 0
                    self.need_flush = True

                    self.tc = 2

                    self.flags |= disk.T2.BUSY | disk.T2.DRQ

                    self.bmode = disk.BufMode.RW

                elif command == disk.Cmd.READ_ADDR:
                    self.debug('CMD read address')
                    self.tc = 3

                    self.flags |= disk.T2.BUSY | disk.T2.DRQ
                    self.bmode = disk.BufMode.RW

                elif command == disk.Cmd.FORCE_INT:
                    self.debug('CMD force interrupt')
                    self.bufp = 0
                    self.bmode = disk.BufMode.IDLE
                    self.tc = 4

                elif command == disk.Cmd.READ_TRACK:
                    self.debug('CMD read track %d' % self.regs[disk.Register.TRACK])

                    self.tc = 3

                    self.flags |= disk.T2.BUSY | disk.T2.DRQ

                elif command == disk.Cmd.WRITE_TRACK:
                    self.debug('CMD write track %d' % self.regs[disk.Register.TRACK])

                    self.tc = 3

                    self.flags |= disk.T2.BUSY | disk.T2.DRQ

                    self.bmode = disk.BufMode.RW

                else:
                    self.debug('unknown disk-command %02x' % command)

            elif reg == disk.Register.DATA_REGISTER:
                # self.debug('Write data register %02x' % v)

                if self.bmode != disk.BufMode.IDLE and self.bufp < 512:
                    self.buffer[self.bufp] = v
                    self.bufp += 1

                    if self.bufp == 512:
                        if self.need_flush:
                            side = 1 if (self.regs[self.Register.FLAGS] & 0x08) == 0x08 else 0
                            o = self.file_offset(side, self.track, self.regs[disk.Register.SECTOR])
                            self.debug('Write sector %d:%d:%d (offset %o) / %d' % (side, self.track, self.regs[disk.Register.SECTOR], o, self.regs[disk.Register.TRACK]))

                            self.fh.seek(o)
                            self.fh.write(bytes(self.buffer))
                            self.fh.flush()

                        self.flags &= ~(disk.T2.DRQ | disk.T2.BUSY)

                        self.bmode = disk.BufMode.IDLE

                    else:
                        self.flags |= disk.T2.DRQ
                else:
                    self.debug('Write data register: %02x' % self.regs[reg])

            elif reg == disk.Register.SECTOR:  # sector
                self.debug('Select sector %d' % v)

            elif reg == self.Register.FLAGS:  # side
                self.debug('Write side register %d' % 1 if v & 0x04 else 0)

                if (v & 0x04) == 0x04:  # reset
                    self.regs[disk.Register.TRACK] = 0

            elif reg == 0x0d:  # motor control
                self.debug('Write motor control')

            else:
                self.debug('write: unknown disk register %02x' % reg)

    def read_mem(self, a: int) -> int:
        offset = a - 0x4000

        if offset >= 0x3ff0: # HW registers
            reg = offset - 0x3ff0

            self.debug('Read DISK register %02x' % reg)

            if reg == self.Register.STATUS_CMD:
                self.debug('Read register %d' % reg)

                if self.tc == 1 or self.tc == 4:  # read
                    v = self.flags
                    self.flags &= (disk.T1.NOTREADY | disk.T1.BUSY)
                    return v

                elif self.tc == 2 or self.tc == 3:  # write
                    return self.flags

            elif reg == self.Register.TRACK:
                self.debug('Read track nr (%d)' % self.regs[reg])
                return self.regs[reg]

            elif reg == disk.Register.SECTOR:
                self.debug('Read sector nr (%d)' % self.regs[reg])
                return self.regs[reg]

            elif reg == disk.Register.DATA_REGISTER:
                if self.bmode != disk.BufMode.IDLE:
                    if self.bufp < 512:
                        v = self.buffer[self.bufp]
                        self.bufp += 1
                        self.flags |= disk.T2.DRQ
                        return v

                    else:
                        self.flags &= ~(disk.T2.DRQ | disk.T2.BUSY | 32)
                        self.debug('end of buffer READ')
                        self.bmode = disk.BufMode.IDLE

                self.debug('Read data register: %02x' % self.regs[reg])

                return self.regs[reg]

            elif reg == self.Register.FLAGS:
                self.debug('Read side (%d)' % self.regs[reg])
                return self.regs[reg]

            elif reg == 0x0f:
                v = 0

                if self.flags & disk.T2.DRQ:
                    v |= 128
                    self.flags &= ~disk.T2.DRQ

                if self.flags & disk.T2.BUSY:
                    v |= 64

                self.debug('Read status register (%02x) %02x' % (reg, v))
                return v

            else:
                self.debug('read (unknown) disk reg %d' % reg)

            return self.regs[reg]

        return self.disk_rom[offset]

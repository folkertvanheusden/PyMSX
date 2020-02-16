# (C) 2020 by Folkert van Heusden <mail@vanheusden.com>
# released under AGPL v3.0

import struct
import sys
from pagetype import PageType

class disk:
    T1_BUSY = 0x01
    T1_INDEX = 0x02
    T1_TRACK0 = 0x04
    T1_CRCERR = 0x08
    T1_SEEKERR = 0x10
    T1_HEADLOAD = 0x20
    T1_PROT = 0x40
    T1_NOTREADY = 0x80

    T2_BUSY = 0x01
    T2_DRQ = 0x02
    T2_NOTREADY = 0x80

    BUF_MODE_IDLE = 1
    BUF_MODE_RW = 2

    def __init__(self, disk_rom_file, debug, disk_image_file):
        print('Loading disk rom %s...' % disk_rom_file, file=sys.stderr)

        fh = open(disk_rom_file, 'rb')
        self.disk_rom = [ int(b) for b in fh.read() ]
        fh.close()

        self.fh = open(disk_image_file, 'ab+')

        self.regs = [ 0 ] * 16

        self.buffer = [ 0 ] * 512
        self.bufp = 0
        self.bmode = disk.BUF_MODE_IDLE
        self.need_flush = False

        self.tc = None
        self.flags = 0

        self.step_dir = 1
        self.track = 0

        self.debug = debug

    def file_offset(self, side, track, sector):
        return (sector - 1)* 512 + (track * 9 * 512) + (80 * 9 * 512) * side;

    def get_signature(self):
        return (self.disk_rom, PageType.DISK, self)

    def write_mem(self, a, v):
        offset = a - 0x4000

        if offset >= 0x3ff0: # HW registers
            reg = offset - 0x3ff0

            self.regs[reg] = v

            if reg == 0x08:
                command= v >> 4
                T      = (v >> 4) & 1;
                h      = (v >> 3) & 1;
                V      = (v >> 2) & 1;
                r1     = (v >> 1) & 1;
                r0     = (v     ) & 1;
                m      = (v >> 4) & 1;
                S      = (v >> 3) & 1;
                E      = (v >> 2) & 1;
                C      = (v >> 1) & 1;
                A0     = (v     ) & 1;
                i      = (v & 15);

                if command == 0:  # restore
                    print('CMD: restore')
                    self.track = self.regs[0x09] = 0

                    self.flags = disk.T1_INDEX | disk.T1_TRACK0
                    if h:
                        self.flags |= disk.T1_HEADLOAD

                    self.tc = 1

                elif command == 1:  # seek
                    self.track = self.regs[0x09] = self.regs[0x0b]
                    print('CMD: seek to %d' % self.track)

                    self.flags = disk.T1_INDEX | (disk.T1_TRACK0 if self.track == 0 else 0)
                    if h:
                        self.flags |= disk.T1_HEADLOAD

                    self.tc = 1

                elif command == 2 or command == 3:  # step
                    print('CMD step %d' % self.step_dir)
                    self.track += self.step_dir

                    if self.track < 0:
                        self.track = 0
                    elif self.track > 79:
                        self.track = 79

                    self.flags = disk.T1_INDEX

                    if self.track == 0:
                        self.flags |= disk.T1_TRACK0

                    if t:
                        self.regs[0x09] = self.track

                    self.tc = 1

                elif command == 4 or command == 5:  # step-in
                    print('CMD step in')
                    self.track += 1

                    if self.track > 79:
                        self.track = 79

                    self.step_dir = 1

                    self.tc = 1

                    self.flags = disk.T1_INDEX

                    if T:
                        self.regs[0x09] = self.track

                elif command == 6 or command == 7:  # step-out
                    print('CMD step out')
                    self.track -= 1

                    if self.track < 0:
                        self.track = 0

                    self.step_dir = -1

                    self.tc = 1

                    self.flags = disk.T1_INDEX
                    if self.track == 0:
                        self.flags |= disk.T1_TRACK0;

                    if T:
                        self.regs[0x09] = track

                elif command == 8 or command == 9:  # read sector
                    print('CMD read sector')
                    self.bufp = 0
                    self.need_flush = False

                    side = 1 if (self.regs[0x0c] & 0x10) == 0x10 else 0
                    o = self.file_offset(side, self.track, self.regs[0x0a])
                    print('Read sector %d:%d:%d (offset %d) / %d' % (side, self.track, self.regs[0x0a], o, self.regs[0x09]))
                    self.fh.seek(o)
                    for i in range(0, 512):
                        b = self.fh.read(1)

                        if len(b) == 0:
                            b = 0
                        else:
                            self.buffer[i] = struct.unpack('<B', b)[0]
                            print('%c' % self.buffer[i], end='')
                    print('')

                    self.tc = 2

                    self.flags |= disk.T2_BUSY | disk.T2_DRQ

                    self.bmode = disk.BUF_MODE_RW

                elif command == 10 or command == 11:  # write sector
                    print('CMD write sector')
                    self.bufp = 0
                    self.need_flush = True

                    self.tc = 2

                    self.flags |= disk.T2_BUSY | disk.T2_DRQ

                    self.bmode = disk.BUF_MODE_RW

                elif command == 12:
                    print('CMD read address')
                    self.tc = 3

                    self.flags |= disk.T2_BUSY | disk.T2_DRQ
                    self.bmode = disk.BUF_MODE_RW

                elif command == 13:
                    print('CMD force interrupt')
                    self.bufp = 0

                    self.tc = 4

                elif command == 14:
                    print('CMD read track %d' % self.regs[0x09])

                    self.tc = 3

                    self.flags |= disk.T2_BUSY | disk.T2_DRQ

                elif command == 15:
                    print('CMD write track %d' % self.regs[0x09])

                    self.tc = 3

                    self.flags |= disk.T2_BUSY | disk.T2_DRQ

                    self.bmode = disk.BUF_MODE_RW

            elif reg == 0x0b:  # data register
                # print('Write data register %02x' % v)

                if self.bmode != disk.BUF_MODE_IDLE and self.bufp < 512:
                    self.buffer[self.bufp] = v
                    self.bufp += 1

                    if self.bufp == 512:
                        if self.need_flush:
                            side = 1 if (self.regs[0x0c] & 0x10) == 0x10 else 0
                            o = self.file_offset(side, self.track, self.regs[0x0a])
                            print('Write sector %d:%d:%d (offset %o) / %d' % (side, self.track, self.regs[0x0a], o, self.regs[0x09]))

                            self.fh.seek(o)
                            self.fh.write(bytes(self.buffer))
                            self.fh.flush()

                        self.flags &= ~(disk.T2_DRQ | disk.T2_BUSY)

                        self.bmode = disk.BUF_MODE_IDLE

                    else:
                        self.flags |= disk.T2_DRQ

            elif reg == 0x0a:  # sector
                print('Select sector %d' % v)

            elif reg == 0x0c:  # side
                print('Write side register %d' % 1 if v & 0x04 else 0)

                if (v & 0x04) == 0x04:  # reset
                    self.regs[0x09] = 0

            elif reg == 0x0d:  # motor control
                print('Write motor control')
                pass

    def read_mem(self, a):
        offset = a - 0x4000

        if offset >= 0x3ff0: # HW registers
            reg = offset - 0x3ff0

            # self.debug('Read DISK register %02x' % reg)

            if reg == 0x08:
                if self.tc == 1 or self.tc == 4:  # read
                    v = self.flags
                    self.flags &= disk.T1_NOTREADY
                    self.flags &= disk.T1_BUSY
                    return v

                elif self.tc == 2 or self.tc == 3:  # write
                    return self.flags

            elif reg == 0x09:
                print('Read track nr (%d)' % self.regs[reg])
                return self.regs[reg]

            elif reg == 0x0a:
                print('Read sector nr (%d)' % self.regs[reg])
                return self.regs[reg]

            elif reg == 0x0b:
                if self.bmode != disk.BUF_MODE_IDLE:
                    if self.bufp < 512:
                        v = self.buffer[self.bufp]
                        self.bufp += 1
                        self.flags |= disk.T2_DRQ
                        return v

                    else:
                        self.flags &= ~(disk.T2_DRQ | disk.T2_BUSY | 32)
                        print('end of buffer READ')
                        self.bmode = disk.BUF_MODE_IDLE

                return self.regs[reg]

            elif reg == 0x0f:
                v = 0

                if self.flags & disk.T2_DRQ:
                        v |= 128
                        self.flags &= ~disk.T2_DRQ

                if self.flags & disk.T2_BUSY:
                        v |= 64

                return v

            else:
                print('read disk reg %d' % reg)

            return self.regs[reg]

        return self.disk_rom[offset]

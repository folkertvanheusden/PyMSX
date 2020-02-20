#! /usr/bin/python3

# (C) 2020 by Folkert van Heusden <mail@vanheusden.com>
# released under AGPL v3.0

import sys
import threading
import time
from disk import disk
from gen_rom import gen_rom
from pagetype import PageType
from scc import scc
from z80 import z80
from screen_kb import screen_kb
from sound import sound
from memmapper import memmap
from rom import rom
from optparse import OptionParser
from RP_5C01 import RP_5C01
from NMS_1205 import NMS_1205

abort_time = None # 60

debug_log = None

class msx:
    def __init__(self, debug_log):
        self.io_values = [ 0 ] * 256
        self.io_read = [ None ] * 256
        self.io_write = [ None ] * 256

        self.stop_flag = False

        self.debug_log = debug_log

        self.subpage = 0x00

        self.mm = memmap(256, self.debug)
        mm_sig = self.mm.get_signature()

        self.slot_0 = [ None, None, None, mm_sig ]
        self.slot_1 = [ None, None, None, mm_sig ]
        self.slot_2 = [ None, None, None, mm_sig ]
        self.slot_3 = [ None, None, None, mm_sig ]

        self.pages = [ 0, 0, 0, 0 ]

        self.clockchip = RP_5C01(self.debug)

        self.dk = screen_kb(self.io_values)

        self.cpu = z80(self.read_mem, self.write_mem, self.read_io, self.write_io, self.debug, self.dk)

        self.musicmodule = NMS_1205(self.cpu, self.debug)
        self.musicmodule.start()

        self.snd = sound(self.debug)

    def debug(self, x):
        self.dk.debug('%s <%02x/%02x>' % (x, self.io_values[0xa8], self.subpage))

        if self.debug_log:
            fh = open(self.debug_log, 'a+')
            fh.write('%s <%02x/%02x>\n' % (x, self.io_values[0xa8], self.subpage))
            fh.close()

    def read_mem(self, a):
        if a == 0xffff:
            return self.subpage

        page = a >> 14

        slot = self.slots[page][self.pages[page]]
        if slot == None:
            return 0xee

        return slot[2].read_mem(a)

    def write_mem(self, a, v):
        assert v >= 0 and v <= 255

        if a == 0xffff:
            self.subpage = v
            return

        page = a >> 14

        slot = self.slots[page][self.pages[page]]
        if slot == None:
            self.debug('Writing %02x to %04x which is not backed by anything' % (v, a))
            return
        
        slot[2].write_mem(a, v)

    def read_page_layout(self, a):
        return (self.pages[3] << 6) | (self.pages[2] << 4) | (self.pages[1] << 2) | self.pages[0]

    def write_page_layout(self, a, v):
        for i in range(0, 4):
            self.pages[i] = (v >> (i * 2)) & 3

    def printer_out(self, a, v):
        # FIXME handle strobe
        print('%c' % v, END='')

    def terminator(self, a, v):
        if a == 0:
            self.stop_flag = True

    def init_io(self):
        self.io_write[0x00] = self.terminator

        if self.musicmodule:
            print('NMS-1205')
            self.io_read[0x00] = self.musicmodule.read_io
            self.io_read[0x01] = self.musicmodule.read_io
            self.io_write[0x00] = self.musicmodule.write_io
            self.io_write[0x01] = self.musicmodule.write_io
            self.io_read[0x04] = self.musicmodule.read_io
            self.io_read[0x05] = self.musicmodule.read_io
            self.io_write[0x04] = self.musicmodule.write_io
            self.io_write[0x05] = self.musicmodule.write_io
            self.io_read[0xc0] = self.musicmodule.read_io
            self.io_read[0xc1] = self.musicmodule.read_io
            self.io_write[0xc0] = self.musicmodule.write_io
            self.io_write[0xc1] = self.musicmodule.write_io

        if self.clockchip:
            print('clockchip')
            self.io_read[0xb5] = self.clockchip.read_io
            self.io_write[0xb4] = self.clockchip.write_io
            self.io_write[0xb5] = self.clockchip.write_io

        if self.dk:
            print('set screen')
            for i in (0x98, 0x99, 0x9a, 0x9b):
                self.io_read[i] = self.dk.read_io
                self.io_write[i] = self.dk.write_io

            self.io_read[0xa9] = self.dk.read_io

            self.io_read[0xaa] = self.dk.read_io
            self.io_write[0xaa] = self.dk.write_io

        if self.snd:
            print('set sound')
            self.io_write[0xa0] = self.snd.write_io
            self.io_write[0xa1] = self.snd.write_io
            self.io_read[0xa2] = self.snd.read_io

        print('set memorymapper')
        for i in range(0xfc, 0x100):
            self.io_read[i] = self.mm.read_io
            self.io_write[i] = self.mm.write_io

        print('set "mmu"')
        self.io_read[0xa8] = self.read_page_layout
        self.io_write[0xa8] = self.write_page_layout

        print('set printer')
        self.io_write[0x91] = self.printer_out

        self.slots = ( self.slot_0, self.slot_1, self.slot_2, self.slot_3 )

    def read_io(self, a):
        if self.io_read[a]:
            return self.io_read[a](a)

        print('Unmapped I/O read %02x' % a)

        return self.io_values[a]
     
    def write_io(self, a, v):
        self.io_values[a] = v

        if self.io_write[a]:
            self.io_write[a](a, v)
        else:
            print('Unmapped I/O write %02x: %02x' % (a, v))

m = msx(debug_log)
m.stop_flag = False

bb_file = None

parser = OptionParser()
parser.add_option('-b', '--biosbasic', dest='bb_file', help='select BIOS/BASIC ROM')
parser.add_option('-l', '--debug-log', dest='debug_log', help='logfile to write to (optional)')
parser.add_option('-R', '--rom', dest='rom', help='select a simple ROM to use, format: slot:rom-filename')
parser.add_option('-S', '--scc-rom', dest='scc_rom', help='select an SCC ROM to use, format: slot:rom-filename')
parser.add_option('-D', '--disk-rom', dest='disk_rom', help='select a disk ROM to use, format: slot:rom-filename:disk-image.dsk')
(options, args) = parser.parse_args()

debug_log = options.debug_log

if not options.bb_file:
    print('No BIOS/BASIC ROM selected (e.g. msxbiosbasic.rom)')
    sys.exit(1)

# bb == bios/basic
bb = rom(options.bb_file, m.debug, 0x0000)
bb_sig = bb.get_signature()
m.slot_0[0] = bb_sig
m.slot_1[0] = bb_sig

if options.scc_rom:
    parts = options.scc_rom.split(':')
    scc_obj = scc(parts[1], m.snd, m.debug)
    scc_sig = scc_obj.get_signature()
    scc_slot = int(parts[0])
    m.slot_1[scc_slot] = scc_sig
    m.slot_2[scc_slot] = scc_sig

if options.disk_rom:
    parts = options.disk_rom.split(':')
    disk_slot = int(parts[0])
    disk_obj = disk(parts[1], m.debug, parts[2])
    m.slot_1[disk_slot] = disk_obj.get_signature()

if options.rom:
    parts = options.rom.split(':')
    rom_slot = int(parts[0])
    offset = 0x4000
    if len(parts) == 3:
        offset = int(parts[2], 16)
    rom_obj = gen_rom(parts[1], m.debug, offset=offset)
    rom_sig = rom_obj.get_signature()
    m.slot_1[rom_slot] = rom_sig
    if len(rom_sig[0]) >= 32768:
        m.slot_2[rom_slot] = rom_sig

m.init_io()

def cpu_thread():
    #t = time.time()
    #while time.time() - t < 5:
    while not m.stop_flag:
        m.cpu.step()

t = threading.Thread(target=cpu_thread)
t.start()

if abort_time:
    time.sleep(abort_time)
    stop_flag = True

try:
    t.join()

except KeyboardInterrupt:
    m.stop_flag = True
    t.join()

m.dk.stop()

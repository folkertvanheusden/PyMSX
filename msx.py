#! /usr/bin/python3

# (C) 2020 by Folkert van Heusden <mail@vanheusden.com>
# released under AGPL v3.0

import sys
import threading
import time
from disk import disk
from gen_rom import gen_rom
from scc import scc
from z80 import z80
from screen_kb import screen_kb
from sound import sound
from memmapper import memmap
from rom import rom
from optparse import OptionParser
from RP_5C01 import RP_5C01
from NMS_1205 import NMS_1205
from typing import Callable, List
from sunriseide import sunriseide

abort_time = None # 60

debug_log = None

io_values: List[int] = [ 0 ] * 256
io_read: List[Callable[[int], int]] = [ None ] * 256
io_write: List[Callable[[int, int], None]] = [ None ] * 256

subpage: List[int] = [ 0x00, 0x00, 0x00, 0x00 ]
has_subpages: List[bool] = [ False, False, False, False ]

def debug(x):
    dk.debug('%s' % x)

    if debug_log:
        fh = open(debug_log, 'a+')
        fh.write('%s\n' % x)
        fh.close()

slots = [[[None for k in range(4)] for j in range(4)] for i in range(4)]

def put_page(slot: int, subslot: int, page: int, obj):
    has_subpages[slot] |= subslot > 0

    slots[slot][subslot][page] = obj

def get_page(slot: int, subslot: int, page: int):
    return slots[slot][subslot][page]

mm = memmap(256, debug)
for p in range(0, 4):
    put_page(3, 2, p, mm)

bb_file = None

parser = OptionParser()
parser.add_option('-b', '--biosbasic', dest='bb_file', help='select BIOS/BASIC ROM')
parser.add_option('-l', '--debug-log', dest='debug_log', help='logfile to write to (optional)')
parser.add_option('-R', '--rom', dest='rom', help='select a simple ROM to use, format: slot:rom-filename')
parser.add_option('-S', '--scc-rom', dest='scc_rom', help='select an SCC ROM to use, format: slot:rom-filename')
parser.add_option('-D', '--disk-rom', dest='disk_rom', help='select a disk ROM to use, format: slot:rom-filename:disk-image.dsk')
parser.add_option('-I', '--ide-rom', dest='ide_rom', help='select a Sunrise IDE ROM to use, format: slot:rom-filename:disk-image.dsk')
(options, args) = parser.parse_args()

debug_log = options.debug_log

if not options.bb_file:
    print('No BIOS/BASIC ROM selected (e.g. msxbiosbasic.rom)')
    sys.exit(1)

# bb == bios/basic
bb = rom(options.bb_file, debug, 0x0000)
put_page(0, 0, 0, bb)
put_page(0, 0, 1, bb)

snd = sound(debug)

if options.scc_rom:
    parts = options.scc_rom.split(':')
    scc_obj = scc(parts[1], snd, debug)
    scc_slot = int(parts[0])
    put_page(scc_slot, 0, 1, scc_obj)
    put_page(scc_slot, 0, 2, scc_obj)

if options.disk_rom:
    parts = options.disk_rom.split(':')
    disk_slot = int(parts[0])
    disk_obj = disk(parts[1], debug, parts[2])
    put_page(disk_slot, 0, 1, disk_obj)

if options.rom:
    parts = options.rom.split(':')
    rom_slot = int(parts[0])
    offset = 0x4000
    if len(parts) == 3:
        offset = int(parts[2], 16)
    rom_obj = gen_rom(parts[1], debug, offset=offset)
    put_page(rom_slot, 0, 1, rom_obj)
# FIXME    if len(rom_sig[0]) >= 32768:
# FIXME        slot_2[rom_slot] = rom_obj

if options.ide_rom:
    parts = options.ide_rom.split(':')
    ide_slot = int(parts[0])
    ide_obj = sunriseide(parts[1], debug, parts[2])
    put_page(ide_slot, 0, 1, ide_obj)

slot_for_page: List[int] = [ 0, 0, 0, 0 ]

clockchip = RP_5C01(debug)

def get_subslot_for_page(slot: int, page: int):
    if has_subpages[slot]:
        return (subpage[slot] >> (page * 2)) & 3

    return 0

def read_mem(a: int) -> int:
    if a == 0xffff:
        if has_subpages[slot_for_page[3]]:
            return subpage[slot_for_page[3]] ^ 0xff

    page = a >> 14

    slot = get_page(slot_for_page[page], get_subslot_for_page(slot_for_page[page], page), page)
    if slot == None:
        return 0xee

    return slot.read_mem(a)

def write_mem(a: int, v: int) -> None:
    if a == 0xffff:
        if has_subpages[slot_for_page[3]]:
            debug('Setting sub-page layout to %02x' % v)
            subpage[slot_for_page[3]] = v
            return

    page = a >> 14

    slot = get_page(slot_for_page[page], get_subslot_for_page(slot_for_page[page], page), page)
    if slot == None:
        debug('Writing %02x to %04x which is not backed by anything (slot: %02x, subslot: %02x)' % (v, a, read_page_layout(0), subpage[slot_for_page[3]]))
        return
    
    slot.write_mem(a, v)

def read_page_layout(a: int) -> int:
    return (slot_for_page[3] << 6) | (slot_for_page[2] << 4) | (slot_for_page[1] << 2) | slot_for_page[0]

def write_page_layout(a: int, v: int) -> None:
    for i in range(0, 4):
        slot_for_page[i] = (v >> (i * 2)) & 3

def printer_out(a: int, v: int) -> None:
    # FIXME handle strobe
    print('%c' % v, END='')

def terminator(a: int, v: int):
    global stop_flag

    if a == 0:
        stop_flag = True

def init_io():
    global dk
    global mm
    global musicmodule
    global snd

    io_write[0x00] = terminator

    if musicmodule:
        print('NMS-1205')
        io_read[0x00] = musicmodule.read_io
        io_read[0x01] = musicmodule.read_io
        io_write[0x00] = musicmodule.write_io
        io_write[0x01] = musicmodule.write_io
        io_read[0x04] = musicmodule.read_io
        io_read[0x05] = musicmodule.read_io
        io_write[0x04] = musicmodule.write_io
        io_write[0x05] = musicmodule.write_io
        io_read[0xc0] = musicmodule.read_io
        io_read[0xc1] = musicmodule.read_io
        io_write[0xc0] = musicmodule.write_io
        io_write[0xc1] = musicmodule.write_io

    if clockchip:
        print('clockchip')
        io_read[0xb5] = clockchip.read_io
        io_write[0xb4] = clockchip.write_io
        io_write[0xb5] = clockchip.write_io

    if dk:
        print('set screen')
        for i in (0x98, 0x99, 0x9a, 0x9b):
            io_read[i] = dk.read_io
            io_write[i] = dk.write_io

        io_read[0xa9] = dk.read_io

        io_read[0xaa] = dk.read_io
        io_write[0xaa] = dk.write_io

    if snd:
        print('set sound')
        io_write[0xa0] = snd.write_io
        io_write[0xa1] = snd.write_io
        io_read[0xa2] = snd.read_io

    print('set memorymapper')
    for i in range(0xfc, 0x100):
        io_read[i] = mm.read_io
        io_write[i] = mm.write_io

    print('set "mmu"')
    io_read[0xa8] = read_page_layout
    io_write[0xa8] = write_page_layout

    print('set printer')
    io_write[0x91] = printer_out

def read_io(a: int) -> int:
    global io_read

    if io_read[a]:
        return io_read[a](a)

    print('Unmapped I/O read %02x' % a)

    return io_values[a]
 
def write_io(a: int, v: int) -> None:
    global io_write

    io_values[a] = v

    if io_write[a]:
        io_write[a](a, v)
    else:
        print('Unmapped I/O write %02x: %02x' % (a, v))

stop_flag = False

def cpu_thread():
    #t = time.time()
    #while time.time() - t < 5:
    while not stop_flag:
        cpu.step()

dk = screen_kb(io_values)

cpu = z80(read_mem, write_mem, read_io, write_io, debug, dk)

musicmodule = NMS_1205(cpu, debug)
musicmodule.start()

init_io()

t = threading.Thread(target=cpu_thread)
t.start()

if abort_time:
    time.sleep(abort_time)
    stop_flag = True

try:
    t.join()

except KeyboardInterrupt:
    stop_flag = True
    t.join()

dk.stop()

#for i in range(0, 256):
#    if cpu.counts[i]:
#        print('instr %02x: %d' % (i, cpu.counts[i]), file=sys.stderr)

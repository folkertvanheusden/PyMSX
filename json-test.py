#! /usr/bin/python3

# (C) 2023 by Folkert van Heusden <mail@vanheusden.com>
# released under MIT license

import json
import sys
import time
from inspect import getframeinfo, stack
from z80 import z80
from screen_kb_dummy import screen_kb_dummy

io = [ 0 ] * 256

ram = [ 0 ] * 65536

def read_mem(a):
    return ram[a]

def write_mem(a, v):
    ram[a] = v

def read_io(a):
    return io[a]
 
def write_io(a, v):
    io[a] = v

def debug(x):
    print(x)

dk = screen_kb_dummy(io)
dk.start()

cpu = z80(read_mem, write_mem, read_io, write_io, debug, dk)

j = json.loads(open(sys.argv[1], 'rb').read())

for set in j:
    if not 'name' in set:
        continue

    cpu.reset()

    mem_reset = []

    print(' *** ' + set['name'] + ' *** ')

    for item in set['initial']:
        v = set['initial'][item]

        if item == 'a':
            cpu.a = v
        elif item == 'b':
            cpu.b = v
        elif item == 'c':
            cpu.c = v
        elif item == 'd':
            cpu.d = v
        elif item == 'e':
            cpu.e = v
        elif item == 'f':
            cpu.f = v
        elif item == 'h':
            cpu.h = v
        elif item == 'l':
            cpu.l = v
        elif item == 'i':
            cpu.i = v
        elif item == 'r':
            cpu.r = v
        elif item == 'pc':
            cpu.pc = v
        elif item == 'sp':
            cpu.sp = v
        elif item == 'iff1':
            cpu.iff1 = v
        elif item == 'iff2':
            cpu.iff2 = v
        elif item == 'ix':
            cpu.ix = v
        elif item == 'iy':
            cpu.iy = v
        elif item == 'af_':
            cpu.a_ = v >> 8
            cpu.f_ = v & 255
        elif item == 'bc_':
            cpu.b_ = v >> 8
            cpu.c_ = v & 255
        elif item == 'de_':
            cpu.d_ = v >> 8
            cpu.e_ = v & 255
        elif item == 'hl_':
            cpu.h_ = v >> 8
            cpu.l_ = v & 255
        elif item == 'ram':
            mem_reset = v
            for pair in v:
                write_mem(pair[0], pair[1])
        else:
            print(f'item {item} not known')

    # do
    cpu.step()

    # verify TODO

    for pair in mem_reset:
        write_mem(pair[0], 0)

    break

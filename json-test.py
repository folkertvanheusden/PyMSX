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

def fail(item, is_, should_be):
    print(f'Item {item} failed, is {is_}, should be {should_be}')

j = json.loads(open(sys.argv[1], 'rb').read())

ok = True

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
            # print(f'item {item} not known')
            pass

    # do
    cpu.step()

    # verify
    for item in set['final']:
        v = set['final'][item]

        if item == 'a':
            if cpu.a != v:
                ok = False
                fail(item, cpu.a, v)
        elif item == 'b':
            if cpu.b != v:
                ok = False
                fail(item, cpu.b, v)
        elif item == 'c':
            if cpu.c != v:
                ok = False
                fail(item, cpu.c, v)
        elif item == 'd':
            if cpu.d != v:
                ok = False
                fail(item, cpu.d, v)
        elif item == 'e':
            if cpu.e != v:
                ok = False
                fail(item, cpu.e, v)
        elif item == 'f':
            if cpu.f != v:
                ok = False
                fail(item, cpu.f, v)
        elif item == 'h':
            if cpu.h != v:
                ok = False
                fail(item, cpu.h, v)
        elif item == 'l':
            if cpu.l != v:
                ok = False
                fail(item, cpu.l, v)
        elif item == 'i':
            if cpu.i != v:
                ok = False
                fail(item, cpu.i, v)
#        elif item == 'r':
#            if cpu.r != v:
#                ok = False
#                fail(item, cpu.r, v)
        elif item == 'pc':
            if cpu.pc != v:
                ok = False
                fail(item, cpu.pc, v)
        elif item == 'sp':
            if cpu.sp != v:
                ok = False
                fail(item, cpu.sp, v)
        elif item == 'iff1':
            if cpu.iff1 != v:
                ok = False
                fail(item, cpu.iff1, v)
        elif item == 'iff2':
            if cpu.iff2 != v:
                ok = False
                fail(item, cpu.iff2, v)
        elif item == 'ix':
            if cpu.ix != v:
                ok = False
                fail(item, cpu.ix, v)
        elif item == 'iy':
            if cpu.iy != v:
                ok = False
                fail(item, cpu.iy, v)
        elif item == 'af_':
            if cpu.a_ != v >> 8:
                ok = False
                fail(item, cpu.a_, v)
            if cpu.f_ != v & 255:
                ok = False
                fail(item, cpu.f_, v)
        elif item == 'bc_':
            if cpu.b_ != v >> 8:
                ok = False
                fail(item, cpu.b_, v)
            if cpu.c_ != v & 255:
                ok = False
                fail(item, cpu.c_, v)
        elif item == 'de_':
            if cpu.d_ != v >> 8:
                ok = False
                fail(item, cpu.d_, v)
            if cpu.e_ != v & 255:
                ok = False
                fail(item, cpu.e_, v)
        elif item == 'hl_':
            if cpu.h_ != v >> 8:
                ok = False
                fail(item, cpu.h_, v)
            if cpu.l_ != v & 255:
                ok = False
                fail(item, cpul_a, v)
        elif item == 'ram':
            for pair in v:
                if read_mem(pair[0]) != pair[1]:
                    ok = False
                    fail(item, read_mem(pair[0]), pair[1])
        else:
            # print(f'item {item} not known')
            pass

    if ok == False:
        print(json.dumps(set, indent=2))
        break

sys.exit(1 if ok == False else 0)

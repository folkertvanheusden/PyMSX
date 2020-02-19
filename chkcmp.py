#! /usr/bin/python3

# (C) 2020 by Folkert van Heusden <mail@vanheusden.com>
# released under AGPL v3.0

import sys
import time
from inspect import getframeinfo, stack
from z80 import z80
from screen_kb_dummy import screen_kb_dummy

pages = dk = cpu = io = slots = None

def init_test():
    global io
    global slots
    global pages
    global dk
    global cpu

    io = [ 0 ] * 256

    ram0 = [ 0 ] * 16384
    ram1 = [ 0 ] * 16384
    ram2 = [ 0 ] * 16384
    ram3 = [ 0 ] * 16384

    slots = [ ] # slots
    slots.append(( ram0, None, None, None ))
    slots.append(( ram1, None, None, None ))
    slots.append(( ram2, None, None, None ))
    slots.append(( ram3, None, None, None ))

    pages = [ 0, 0, 0, 0 ]

    dk = screen_kb_dummy(io)
    dk.start()

    cpu = z80(read_mem, write_mem, read_io, write_io, debug, dk)

def read_mem(a):
    global slots
    global pages

    page = a >> 14

    if slots[page][pages[page]] == None:
        assert False

    return slots[page][pages[page]][a & 0x3fff]

def write_mem(a, v):
    global slots
    global pages

    assert v >= 0 and v <= 255

    page = a >> 14

    if slots[page][pages[page]] == None:
        assert False

    slots[page][pages[page]][a & 0x3fff] = v

def read_io(a):
    return io[a]
 
def write_io(a, v):
    io[a] = v

def debug(x):
    #fh = open('debug.log', 'a+')
    #fh.write('%s\n' % x)
    #fh.close()
    pass

def flag_str(f):
    flags = ''

    flags += 's1 ' if f & 128 else 's0 '
    flags += 'z1 ' if f & 64 else 'z0 '
    flags += '51 ' if f & 32 else '50 '
    flags += 'h1 ' if f & 16 else 'h0 '
    flags += '31 ' if f & 8 else '30 '
    flags += 'P1 ' if f & 4 else 'P0 '
    flags += 'n1 ' if f & 2 else 'n0 '
    flags += 'c1 ' if f & 1 else 'c0 '

    return flags

def my_assert(before, after, v1, v2):
    if v1 != v2:
        print(before)
        print(after)
        print('expected:', v2)
        print('is:', v1)
        print(cpu.reg_str())
        caller = getframeinfo(stack()[1][0])
        print(flag_str(cpu.f))
        print('%s:%d' % (caller.filename, caller.lineno))
        sys.exit(1)

startt = pt = time.time()
lines = ntests = 0
before = after = None
for line in open('/tmp/rlc.dat', 'r'):
    line = line.rstrip()

    parts = line.split()
    i = 1

    lines += 1

    if parts[0] == 'before':
        ntests += 1

        init_test()

        before = line

        memp = 0
        while parts[i] != '|':
            write_mem(memp, int(parts[i], 16))
            i += 1
            memp += 1

        i += 1  # skip |
        i += 1  # skip endaddr
        i += 1  # skip cycles

        cpu.a, cpu.f = cpu.u16(int(parts[i], 16))
        i += 1
        cpu.b, cpu.c = cpu.u16(int(parts[i], 16))
        i += 1
        cpu.d, cpu.e = cpu.u16(int(parts[i], 16))
        i += 1
        cpu.h, cpu.l = cpu.u16(int(parts[i], 16))
        i += 1

        i += 1 # AF_
        i += 1 # BC_
        i += 1 # DE_
        i += 1 # HL_

        cpu.ix = int(parts[i], 16)
        i += 1

        cpu.iy = int(parts[i], 16)
        i += 1

    elif parts[0] == 'memchk':
        my_assert(before, line, read_mem(int(parts[1], 16)), int(parts[2], 16))

    else:
        after = line
        while parts[i] != '|':
            i += 1

        i += 1  # skip |

        endaddr = int(parts[i], 16)
        i += 1

        expcycles = int(parts[i])
        i += 1

        cycles = 0
        while cpu.pc < endaddr:
            cycles += cpu.step()

        # my_assert(before, line, cycles, expcycles)

        my_assert(before, line, cpu.m16(cpu.a, cpu.f), int(parts[i], 16))
        i += 1

        my_assert(before, line, cpu.m16(cpu.b, cpu.c), int(parts[i], 16))
        i += 1

        my_assert(before, line, cpu.m16(cpu.d, cpu.e), int(parts[i], 16))
        i += 1

        my_assert(before, line, cpu.m16(cpu.h, cpu.l), int(parts[i], 16))
        i += 1

        i += 1 # AF_
        i += 1 # BC_
        i += 1 # DE_
        i += 1 # HL_

        my_assert(before, line, cpu.ix, int(parts[i], 16))
        i += 1

        my_assert(before, line, cpu.iy, int(parts[i], 16))
        i += 1

        my_assert(before, line, cpu.pc, int(parts[i], 16))
        i += 1

        my_assert(before, line, cpu.sp, int(parts[i], 16))
        i += 1

        i += 1  # i
        i += 1  # r
        i += 1  # r7

        my_assert(before, line, cpu.im, int(parts[i], 16))
        i += 1

        i += 1  # iff1
        i += 1  # iff2

        # obsoloted by memchk: my_assert(before, line, read_mem(cpu.m16(cpu.h, cpu.l)), int(parts[i], 16))
        i += 1

        assert i == len(parts)

    now = time.time()
    if now - pt >= 1.0:
        took = now - startt
        print('%d lines, %.1f tests/s' % (lines, ntests / took))
        pt = now

print('All fine, took %.1f seconds, %.1f lines/s' % (time.time() - startt, lines))

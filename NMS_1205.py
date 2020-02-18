# (C) 2020 by Folkert van Heusden <mail@vanheusden.com>
# released under AGPL v3.0

import pygame.midi
import queue
import threading
import time

class NMS_1205(threading.Thread):
    def __init__(self, cpu, debug):
        self.cpu = cpu
        self.debug = debug

        pygame.midi.init()
        self.mpo = pygame.midi.Output(pygame.midi.get_default_output_id())
        self.mpi = pygame.midi.Input(pygame.midi.get_default_input_id())

        self.outbuf = [ 0 ] * 3
        self.outbufin = 0

        self.qinbuf = queue.Queue()
        self.inbuf = [ ]

        self.stop_flag = False

        super(NMS_1205, self).__init__()

    def stop(self):
        self.stop_flag = True

    def run(self):
        while not self.stop_flag:
            i = self.mpi.read(1)
            if len(i):
                print(i)
            #in_ = self.mpi.read(1)[0]

            #self.qinbuf.put(in_)

            #print('MIDI in interrupt')

            #self.interrupt()

    def read_io(self, a):
        if a == 0x00:  # status register mpo
            return 0b00001110
        elif a == 0x01:
            return 0xff
        elif a == 0x04:  # status register mpo
            return 0b00001110 | (1 + 128 if self.inpuf or not self.qinbuf.empty() else 0)
        elif a == 0x05:
            if not self.inbuf and not self.qinbuf.empty():
                self.inbuf = self.qinbuf.get(block=False)

            if self.inbuf:
                c = self.inbuf[0]
                del self.inbuf[0]
                return c
        elif a == 0xc0:  # MSX-Music
            return 6

        return 0

    def push_byte(self, v):
        if v & 128:
            if self.outbufin > 0:
                self.mp.write_short(self.outbuf)

            self.outbuf[0] = v
            self.outbufin = 1

        elif self.outbufin < 3:
            self.outbuf[self.outbufin] = v
            self.outbufin += 1

            cmd = self.outbuf[0] & 0xf0
            if cmd in (0x80, 0x90, 0xa0, 0xb0, 0xe0) and self.outbufin == 3:
                self.mp.write_short(self.outbuf)
                self.outbufin = 0
            elif cmd in (0xc0, 0xd0) and self.outbufin == 2:
                self.mp.write_short(self.outbuf)
                self.outbufin = 0
            else:
                self.mp.write_short(self.outbuf)
                self.outbufin = 0

        else:
            self.debug('MIDI out buffer overrun')

    def write_io(self, a, v):
        if a == 0x00:
            pass
        elif a == 0x01:
            self.push_byte(v)
        elif a == 0x04:
            pass
        elif a == 0x05:
            pass

    def stop(self):
        del self.mpi
        del self.mpo
        pygame.midi.quite()

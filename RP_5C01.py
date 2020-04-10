# (C) 2020 by Folkert van Heusden <mail@vanheusden.com>
# released under AGPL v3.0

import time
from typing import List

class RP_5C01:
    def __init__(self, debug):
        self.ri: int = 0
        self.blocks = [ [ 0 for k in range(4)] for j in range(16)]
        self.debug = debug

    def get_ios(self):
        return [ [ 0xb5 ] , [ 0xb4, 0xb5 ] ]

    def get_name(self):
        return 'RP-5C01 (RTC)'

    def read_io(self, a: int) -> int:
        block = self.blocks[0x0d][0] & 3

        rc = 0

        if block > 0 or self.ri >= 0x0d:
            rc = (self.blocks[self.ri][block] & 15)

        else:
            now = time.localtime()

            if self.ri == 0:
                rc = now.tm_sec % 10
            elif self.ri == 1:
                rc = now.tm_sec // 10
            elif self.ri == 2:
                rc = now.tm_min % 10
            elif self.ri == 3:
                rc = now.tm_min // 10
            elif self.ri == 4:
                rc = now.tm_hour % 10
            elif self.ri == 5:
                rc = now.tm_hour // 10
            elif self.ri == 6:
                rc = now.tm_wday
            elif self.ri == 7:
                rc = now.tm_mday % 10
            elif self.ri == 8:
                rc = now.tm_mday // 10
            elif self.ri == 9:
                rc = now.tm_mon % 10
            elif self.ri == 0x0a:
                rc = now.tm_mon // 10
            elif self.ri == 0x0b:
                rc = now.tm_year % 10
            elif self.ri == 0x0c:
                rc = (now.tm_year // 10) % 10

            self.debug('RP_5C01: read %02x' % a)

        return rc | 0xf0

    def write_io(self, a: int, v: int) -> None:
        if a == 0xb4:
            self.ri = v

        elif a == 0xb5:
            block = self.blocks[0x0d][0] & 3

            if block > 0 or self.ri >= 0x0d:
                if self.ri >= 0x0d:
                    block = 0

                self.blocks[self.ri][block] = v

                if self.ri == 0x0f:
                    for i in range(16):
                        self.blocks[i][1] = 0

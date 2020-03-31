import struct

def read_byte_int(fh):
    return struct.unpack('<B', fh.read(1))[0]

def chk(fh, what):
    for v in what:
        assert read_byte_int(fh) == v

def load_cas_file(wm, f):
    fh = open(f, 'rb')

    hdr = [ 0x1F, 0xA6, 0xDE, 0xBA, 0xCC, 0x13, 0x7D, 0x74 ]
    chk(fh, hdr)

    d0 = [ 0xd0, 0xd0, 0xd0, 0xd0, 0xd0, 0xd0, 0xd0, 0xd0, 0xd0, 0xd0 ] 
    chk(fh, d0)

    print(fh.read(6)) # filename

    chk(fh, hdr)

    begin = read_byte_int(fh)
    begin += read_byte_int(fh) << 8
    end = read_byte_int(fh)
    end += read_byte_int(fh) << 8
    start = read_byte_int(fh)
    start += read_byte_int(fh) << 8

    if start == 0:
        start = begin

    print('begin: %04x end %04x, start %04x' % (begin, end, start))

    for a in range(begin, end):
        wm(a, read_byte_int(fh))

    return start

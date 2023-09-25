* requires the (python3-)pygame, pyaudio and mido packages for python3 (don't forget to install a backend for mido like rtmidi)

To run, execute msx.py

Run it with "-h" to see a list of options. At least "-b msxbiosbasic.rom" is required.

If it is too slow, remove the debug code with the following command:

sed -i 's/self.debug.*/pass/g' z80.py

What works:
revision 65735e2ab14a62ae78963df94b0aabb1f065e90d can run MSX-DOS 1, MSX Disk Basic, Nemesis 2, Athletic Land

msx.py -b msxbiosbasic.rom -S 1:0:NEMESIS2.ROM

msx.py -b msxbiosbasic.rom -D 1:0:FSFD1.ROM:md1.dsk

msx.py -b msxbiosbasic.rom -R 1:0:athletic.rom

msx.py -b nms8245_basic-bios2.rom -D 3:3:nms8245_disk.rom:MDOS22DE.DSK -R 3:0:nms8245_msx2sub.rom:0000 -M 1:0:MDOS22V3.ROM


(C) 2020, 2023 by Folkert van Heusden <mail@vanheusden.com>
released under AGPL v3.0

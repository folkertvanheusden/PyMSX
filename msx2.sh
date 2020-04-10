#! /bin/bash

#DIR=`mktemp -d`
#cp *py msxbiosbasic.rom athletic.rom $DIR/

#pushd $DIR
#sed -i 's/self.debug.*/pass/g' z80.py
python3 ./msx.py -b 2/nms8245_basic-bios2.rom -D 3:3:2/nms8245_disk.rom:md1.dsk -R 3:0:2/nms8245_msx2sub.rom:0000
#popd

#rm -rf $DIR

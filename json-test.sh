#! /bin/sh

for i in /home/folkert/t/jsmoo/misc/tests/GeneratedTests/z80/v1/*.json
do
	echo $i

	./json-test.py $i

	if [ $? -ne 0 ] ; then
		break
	fi

	echo
done

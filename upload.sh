#!/bin/bash

#avrdude -c usbasp -p m32 -U flash:w:tx.hex
avrdude -c stk500v1 -b 57600 -P /dev/ttyUSB0 -p atmega32 -U flash:w:tx.hex
#sudo avrdude -c bsd -p $arch -E noreset -U flash:w:$1.hex

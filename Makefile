ASFLAGS = -Wa, -gstabs
CPFLAGS	= -gdwarf-2 -Os -Wall -Wa,-ahlms=$(<:.c=.lst) -std=c99 -ffunction-sections -fdata-sections -dr -finline-functions-called-once 
LDFLAGS = -gdwarf-2

CC	= avr-gcc
AS	= avr-gcc -x assembler-with-cpp	
RM	= rm -f
RN	= mv
CP	= cp
OBJCOPY	= avr-objcopy
OBJDUMP	= avr-objdump
SIZE	= avr-size
INCDIR	= .
FORMAT = ihex	

MCU=atmega32
CPFLAGS += -mmcu=$(MCU) -DF_CPU=16000000UL
ASFLAGS += -mmcu=$(MCU) -DF_CPU=16000000UL

%.o : %.c 
	$(CC) -c $(CPFLAGS) -I$(INCDIR) $< -o $@

%.s : %.c
	$(CC) -S $(CPFLAGS) -I$(INCDIR) $< -o $@

%.o : %.s
	$(AS) -c $(ASFLAGS) -I$(INCDIR) $< -o $@

%.elf:
	$(CC) $^ $(LIB) -Wl,-Map=$*.map,--cref -mmcu=$(MCU) $(LDFLAGS) -o $@

%.cof: %.elf
	$(OBJCOPY) --debugging -O coff-ext-avr \
		--change-section-address   .data-0x00000 \
		--change-section-address    .bss-0x00000 \
		--change-section-address .noinit-0x00000 \
		--change-section-address .eeprom-0x10000 \
		$< $@

%.bin: %.elf
	$(OBJCOPY) -O binary -R .eeprom $< $@

%.hex: %.elf
	$(OBJCOPY) -O $(FORMAT) -R .eeprom $< $@

%.eep: %.elf
	$(OBJCOPY) -j .eeprom --set-section-flags=.eeprom="alloc,load" --change-section-lma .eeprom=0 -O $(FORMAT) $< $@

%.dmp: %.elf
	$(OBJDUMP) -h -S $< > $@

#################################################################
# Description of source files starts here

TARGETS = tx
ALL_SRC = main.c uart.c put.c command.c actions.o eeprom.c adc.c

default: tx

tx.elf: main.o uart.o put.o command.o actions.o eeprom.o adc.o

tx.coff: main.o

$(TARGETS:%=%-build): %-build: %.elf %.bin %.hex %.eep %.dmp
	$(SIZE) $*.elf
#	-git commit -e -a -uno
	@echo $< done

$(TARGETS:%=%-upload): %: %-build
	./upload.sh $*

$(TARGETS): %: %-build

clean:
	$(RM) $(ALL_SRC:.c=.o)
	$(RM) $(ALL_SRC:.c=.s)
	$(RM) $(ALL_SRC:.c=.lst)
	$(RM) $(TARGETS:=.map)
	$(RM) $(TARGETS:=.elf)
	$(RM) $(TARGETS:=.cof)
	$(RM) $(TARGETS:=.obj)
	$(RM) $(TARGETS:=.a90)
	$(RM) $(TARGETS:=.sym)
	$(RM) $(TARGETS:=.eep)
	$(RM) $(TARGETS:=.hex)
	$(RM) $(TARGETS:=.bin)
	$(RM) *~

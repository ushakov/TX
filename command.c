#include <avr/interrupt.h>

#include "command.h"

#include "uart.h"
#include "put.h"
#include "model.h"
#include "actions.h"

uint8_t line[80];
uint8_t pos;

void init_command() {
    pos = 0;
}

int8_t get_hex_nibble(uint8_t c) {
    if (c >= '0' && c <= '9') {
        return c - '0';
    }
    if (c >= 'a' && c <= 'f') {
        return c - 'a' + 10;
    }
    if (c >= 'A' && c <= 'F') {
        return c - 'A' + 10;
    }
    return -1;
}

int32_t get_hex_num(uint8_t *c, int8_t len) {
    int32_t out = 0;
    for (int i = 0; i < len; ++i) {
        int8_t n = get_hex_nibble(c[i]);
        if (n < 0) {
            return -1;
        }
        out *= 16;
        out += n;
    }
    return out;
}

uint8_t oldpos;

void error() {
    putProg("Err");
    putCRLF();
}

extern uint8_t no_serial_output;
void dump_model() {
    no_serial_output = 1;
    for(int i = 0; i < sizeof(Model); ++i) {
        if (i % 16 == 0) {
            putHexF(i, 3);
            putProg(":");
        }
        putProg(" ");
        putHexF(((uint8_t*)&model)[i], 2);
        if (i % 16 == 15) {
            putCRLF();
        }
    }
    putCRLF();
    no_serial_output = 0;
}

void ok() {
    putProg("DONE");
    putCRLF();
}

void check_command() {
    int16_t c = uart_getchar();
    if (c == -1) {
        return;
    }
    if (c != '\n' && c != '\r') {
        line[pos++] = c;
        return;
    }
    if (pos == 0) {
        return;
    }
    // Phew, now we have a non-empty complete line
    // First char is command
    line[pos] = 0;
    oldpos = pos;
    pos = 0; // Prepare for next command
    if (line[0] == 'D') {
        // D -- dump model description
        dump_model();
        ok();
        return;
    } else if (line[0] == 'S') {
        // S xxx yy -- write byte to model description
        // xxx -- address, yy -- value
        int16_t addr = get_hex_num(line + 2, 3);
        int16_t val = get_hex_num(line + 6, 2);
        if (addr < 0 || val < 0) {
            error();
            return;
        }
        if (addr >= sizeof(Model)) {
            error();
            return;
        }
        TX_model_write_byte(addr, val);
        ok();
        return;
    } else if (line[0] == 'C') {
        // C -- perform calibration
        TX_calibrate();
        ok();
    } else if (line[0] == 'R') {
        // R R R -- reset model
        if (line[2] != 'R' || line[4] != 'R') {
            error();
            return;
        }
        TX_reset();
        ok();
    } else {
        error();
    }
}

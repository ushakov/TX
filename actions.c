#include <avr/interrupt.h>
#include <util/delay.h>

#include "actions.h"
#include "eeprom.h"
#include "put.h"
#include "adc.h"

Model model;

int16_t adc_midpoint[NUM_CTLS];
int16_t adc_min[NUM_CTLS];
int16_t adc_max[NUM_CTLS];

// EEPROM layout:
// 0: 1 byte padding
// 1..36 -- calibration data
# define CALIB_OFFSET 1
// 37..  -- model data
# define MODEL_OFFSET 37

void TX_load_calibration_data() {
    for (int i = 0; i < 6; ++i) {
        adc_min[i] = eeprom_read(CALIB_OFFSET + i*6);
        adc_min[i] += eeprom_read(CALIB_OFFSET + i*6 + 1) << 8;
        adc_max[i] = eeprom_read(CALIB_OFFSET + i*6 + 2);
        adc_max[i] += eeprom_read(CALIB_OFFSET + i*6 + 3) << 8;
        adc_midpoint[i] = eeprom_read(CALIB_OFFSET + i*6 + 4);
        adc_midpoint[i] += eeprom_read(CALIB_OFFSET + i*6 + 5) << 8;
   }
}

void TX_load_model() {
    for (int i = 0; i < sizeof(Model); ++i) {
        uint8_t val = eeprom_read(MODEL_OFFSET + i);
        ((uint8_t*)&model)[i] = val;
    }
}

void TX_save_model() {
    for (int i = 0; i < sizeof(Model); ++i) {
        uint8_t val = ((uint8_t*)&model)[i];
        eeprom_write(MODEL_OFFSET + i, val);
    }
}

void TX_init() {
    TX_load_calibration_data();
    TX_load_model();
}

void TX_calibrate() {
    putProg("M Calibration starting. Move sticks");
    putCRLF();
    cli();
    for (int ch = 0; ch < 6; ++ch) {
        adc_min[ch] = 3000;
        adc_max[ch] = -1;
        adc_midpoint[ch] = 0;
    }

    for (int i = 0; i < 20000; ++i) {
        for (int ch = 0; ch < 6; ++ch) {
            int16_t t = read_adc(ch);
            if (adc_min[ch] > t) {
                adc_min[ch] = t;
            }
            if (adc_max[ch] < t) {
                adc_max[ch] = t;
            }
        }
        _delay_us(150);
    }
    sei();
    
    putProg("M Center sticks");
    putCRLF();

    _delay_ms(1000);
    cli();
    int32_t aggr[] = {0,0,0,0,0,0};
    int N = 5000;
    for (int i = 0; i < N; ++i) {
        for (int ch = 0; ch < 6; ++ch) {
            int16_t t = read_adc(ch);
            aggr[ch] += t;
        }
        _delay_ms(1);
    }
    for (int ch = 0; ch < 6; ++ch) {
        adc_midpoint[ch] = aggr[ch]/N;
    } 
    sei();
    putProg("M Calibration done");
    putCRLF();
    putProg("M");
    for (int i = 0; i < 6; ++i) {
        eeprom_write(CALIB_OFFSET + i*6, adc_min[i] & 0xff); 
        eeprom_write(CALIB_OFFSET + i*6 + 1, adc_min[i] >> 8);
        eeprom_write(CALIB_OFFSET + i*6 + 2, adc_max[i] & 0xff); 
        eeprom_write(CALIB_OFFSET + i*6 + 3, adc_max[i] >> 8);
        eeprom_write(CALIB_OFFSET + i*6 + 4, adc_midpoint[i] & 0xff); 
        eeprom_write(CALIB_OFFSET + i*6 + 5, adc_midpoint[i] >> 8);
        putProg(" [");
        putInt(adc_min[i]);
        putProg(", ");
        putInt(adc_midpoint[i]);
        putProg(", ");
        putInt(adc_max[i]);
        putProg("]");
    }
    putCRLF();
}

void TX_reset() {
    model.num_ch = 6;
    for (int m = 0; m < NUM_MODES; ++m) {
        Mode *mode = &model.modes[m];
        for (int ctl = 0; ctl < NUM_CTLS; ++ctl) {
            Control *control = &mode->controls[ctl];
            control->low_ep = 100;
            control->high_ep = 100;
            control->low_ep2 = 100;
            control->high_ep2 = 100;
            for (int c = 0; c < CURVE_NODES; ++c) {
                control->curve[c] = -100 + 200 * c / (CURVE_NODES-1);
            }
            control->source = 0;
        }
        for (int ch = 0; ch < model.num_ch; ++ch) {
            Channel *channel = &mode->channels[ch];
            channel->reverse = 0;
            for (int ctl = 0; ctl < NUM_CTLS; ++ctl) {
                if (ctl == ch) {
                    channel->mix[ctl] = 100;
                } else {
                    channel->mix[ctl] = 0;
                }
            }
        }
    }
    TX_save_model();
}

void TX_model_write_byte(uint16_t offset, uint8_t val) {
    ((uint8_t*)&model)[offset] = val;
    eeprom_write(MODEL_OFFSET + offset, val);
}

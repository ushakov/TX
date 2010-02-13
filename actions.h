#ifndef _ACTIONS_H_
#define _ACTIONS_H_

#include "model.h"

extern Model model;
extern int16_t adc_midpoint[NUM_CTLS];
extern int16_t adc_min[NUM_CTLS];
extern int16_t adc_max[NUM_CTLS];

void TX_init();
void TX_calibrate();
void TX_reset();
void TX_model_write_byte(uint16_t offset, uint8_t data);

#endif /* _ACTIONS_H_ */

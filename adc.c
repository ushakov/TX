#include <avr/io.h>
#include "adc.h"

#define ADC_VREF_TYPE 0x40
void init_adc() {
    // ADC initialization
    // ADC Clock frequency: 125,000 kHz
    // ADC Voltage Reference: VCC
    ADMUX=ADC_VREF_TYPE;
    ADCSRA=0x87;
}

uint16_t read_adc(uint8_t adc_input) {
    ADMUX = adc_input | ADC_VREF_TYPE;
    // Start the AD conversion
    ADCSRA |= 0x40;
    // Wait for the AD conversion to complete
    while ((ADCSRA & 0x40) != 0);
    uint16_t val = ADCL;
    uint16_t t = ADCH;
    val += t << 8;
    return val;
}

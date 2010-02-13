#include <avr/io.h>
#include <avr/interrupt.h>
#include <util/delay.h>

#include "model.h"
#include "uart.h"
#include "put.h"
#include "adc.h"
#include "actions.h"
#include "command.h"

int16_t input[NUM_CTLS];
int16_t controls[NUM_CTLS];
int16_t channels[NUM_CHANS];

uint8_t cur_mode;
uint8_t keys;

uint8_t keys;

uint8_t no_serial_output = 0;

uint8_t read_keys() {
    uint8_t ret = 0;
    if (!(PIND & _BV(7))) {
        ret |= K_SW_A1;
    }
    if (!(PINC & _BV(1))) {
        ret |= K_SW_A2;
    }
    if (!(PINC & _BV(2))) {
        ret |= K_SW_B;
    }
    if (!(PINC & _BV(3))) {
        ret |= K_DR;
    }
    if (!(PINC & _BV(4))) {
        ret |= K_MODE_A;
    }
    if (!(PINC & _BV(5))) {
        ret |= K_MODE_B;
    }
    return ret;
}

// compute mixers and apply physical data to channel chan.
// uses controls[], returns channel value in TT, [1800..4200].
uint16_t compute_channel (uint8_t chan) {
    int8_t *mix = model.modes[cur_mode].channels[chan].mix;
    int32_t value = 0; // 1,5 ms
    for (uint8_t i=0; i < NUM_CTLS; i++) {
        if (mix[i]!=0) {
            int32_t input = controls[i];
            input *= mix[i];
            input /= 100;
            value += input;
        }
    }
    if (value < -1200) value = -1200;
    if (value > 1200) value = 1200;
    if (model.modes[cur_mode].channels[chan].reverse) {
        value = -value;
    }
    value += 3000; // midpoint at 1.5ms
    channels[chan] = value;
    return (uint16_t)value;
}

// input: value in timer ticks, [0..2000]
// output: curve applied to value, in timer ticks, [-1200,1200].
const int16_t CURVE_SLOT = 2000 / (CURVE_NODES-1);
int16_t apply_curve(int16_t value, int8_t* curve) {
    int16_t n = value / CURVE_SLOT;
    if (n > CURVE_NODES - 2) n = CURVE_NODES - 2;
    if (n < 0) n = 0;
    int16_t c1 = curve[n]; c1 = c1 * 10; // -120..120 -> -1200..1200, timer value
    int16_t c2 = curve[n+1]; c2 = c2 * 10;
    int16_t lower = n * CURVE_SLOT;
    int32_t out;
    out = value - lower;
    out *= c2 - c1;
    out /= CURVE_SLOT;
    out += c1;
    return (int16_t)out;
}

// Apply endpoints
// input: value in timer ticks, [-1200,1200].
// output: rates applied, in TT, [-1200, 1200].
int16_t apply_ep(int16_t value, int8_t low, int8_t high) {
    int8_t rate;
    if (value < 0) {
        rate = low;
    } else {
        rate = high;
    }
    int32_t ret = value;
    ret = ret * rate / 100;
    return (int16_t)ret;
}


uint8_t get_mode() {
    if (keys & K_MODE_A) {
        return 2;
    }
    if (keys & K_MODE_B) {
        return 1;
    }
    return 0;
}

// Sample all inputs, do pre-mix processing, prepare controls[] array.
// Called 50 times per second, should not take more than
// 20ms - 2.5ms * (num_channels+2)! Otherwise, PPM may fall apart.
void get_inputs() {
    for(int i = 0; i < 6; ++i) {
        int32_t in = read_adc(i);
        if (in < adc_midpoint[i]) {
            //if (adc_min[i] > in) adc_min[i] = in;
            in = (in - adc_min[i]) * 1000 / (adc_midpoint[i] - adc_min[i]);
            input[i] = in;
        }
        else
        {
            //if (adc_max[i] < in) adc_max[i] = in;
            in = (in - adc_midpoint[i]) * 1000 / (adc_max[i] - adc_midpoint[i]);
            input[i] = 1000 + in;
        }
        if (i == 4 || i == 5) {
            // My Pot_A and Pot_B are wired backwards
            input[i] = 2000 - input[i];
        }
    }
  
    uint8_t new_keys = read_keys();
    if (new_keys != keys) {
        keys = new_keys;
//         putProg("M Keys");
//         if (keys & K_MODE_A) {
//             putProg(" ModeA");
//         }
//         if (keys & K_MODE_B) {
//             putProg(" ModeB");
//         }
//         if (keys & K_DR) {
//             putProg(" DR");
//         }
//         if (keys & K_SW_A1) {
//             putProg(" SwitchA1");
//         }
//         if (keys & K_SW_A2) {
//             putProg(" SwitchA2");
//         }
//         if (keys & K_SW_B) {
//             putProg(" SwitchB");
//         }
//         putCRLF();
    }

    // mode switch
    int8_t new_mode;
    new_mode = get_mode();
    if (cur_mode != new_mode) {
        cur_mode = new_mode;
        // ... additional actions to perform on mode change
//         putProg("Mode change: ");
//         putInt(cur_mode);
//         putCRLF();
    }
    Mode *mode = &(model.modes[cur_mode]);

    if (keys & K_SW_A1) {
        input[SW_A] = 0;
    } else if (keys & K_SW_A2) {
        input[SW_A] = 2000;
    } else {
        input[SW_A] = 1000;
    }
    
    if (keys & K_SW_B) {
        input[SW_B] = 0;
    } else {
        input[SW_B] = 2000;
    }

    input[Virt_A] = input[mode->controls[Virt_A].source];
    input[Virt_B] = input[mode->controls[Virt_B].source];

    uint8_t dual_rates = 0;
    if (keys & K_DR) {
        dual_rates = 1;
    }

    // Compute control values based on inputs.
    // Standard controls
    for(int8_t i = 0; i < NUM_CTLS; i++) {
        int16_t value = input[i];

        // Curves are applied to all controls (incl. virtual and discrete!)
        value = apply_curve(input[i], mode->controls[i].curve);

        // Dual rates are applied to ail, ele & rud only
        int16_t low_ep, high_ep;
        low_ep = mode->controls[i].low_ep;
        high_ep = mode->controls[i].high_ep;
        if (i == Ailerons || i == Elevator || i == Rudder) {
            if (dual_rates) {
                low_ep = mode->controls[i].low_ep2;
                high_ep = mode->controls[i].high_ep2;
            }
        }

        controls[i] = apply_ep(value, low_ep, high_ep);
    }
} 

uint8_t changed;
uint16_t out_ch[NUM_CHANS];

ISR(TIMER1_COMPA_vect) { 
    static uint8_t cur_channel = 0;
    static uint16_t sum;
    uint16_t out;
    
    if (cur_channel < model.num_ch) {       
        out = compute_channel(cur_channel);
        ICR1H = out >> 8;
        ICR1L = out & 0xff;
        if (out_ch[cur_channel] < out-5 || out_ch[cur_channel] > out+5) {
            changed = 1;
            out_ch[cur_channel] = out;
        }
        sum += out;
        cur_channel++;
    }
    else
    {
        out = 45000 - sum; //total packet is 22.5ms
        ICR1H = out >> 8; 
        ICR1L = out & 0xff;
        cur_channel = 0;
        sum = 0;
        sei();
        get_inputs();
        if (changed && !no_serial_output) {
            putProg(">");
            for (int i = 0; i < model.num_ch; ++i) {
                putProg(" ");
                putInt(out_ch[i]);
            }
            putCRLF();
        }
        changed = 0;
    }
}

int main(void)
{
    // All ports to input + pullup
    DDRB = 0;
    DDRC = 0;
    DDRD = 0;
    PORTB = 0xff;
    PORTC = 0xff;
    PORTD = 0xff;

    DDRD |= _BV(5); // set ppm pin to output

    // Init UART
    uart_init();
    uart_set_baud_rate(57600);
    
    init_adc();
    TX_init();

    // Timer/Counter 1 initialization
    // Clock source: System Clock
    // Clock value: 2MHz (F_CPU/8)
    // Mode: Fast PWM top=ICR1
    // OC1A output: Inv.
    // Compare Match Interrupt: On
    TCCR1A = 0xc2;
    TCCR1B = 0x1A;
    ICR1H = 0x17;
    ICR1L = 0x70;
    OCR1AH = 0x02;
    OCR1AL = 0x68;

    sei();

    keys = read_keys();
    cur_mode = get_mode();

    get_inputs();

    TIMSK |= (1 << OCIE1A); // Enable timer interrupt!

    init_command();
    while(1) {
        check_command();
    }
    return 0;
}

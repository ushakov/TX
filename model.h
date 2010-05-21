#ifndef _MODEL_H_
#define _MODEL_H_

#include <inttypes.h>

#define CURVE_NODES 7
#define NUM_CHANS   8
#define NUM_CTLS   10
#define NUM_MODES   3

// Controls, NUM_CTLS in total
#define Ailerons 0
#define Elevator 1
#define Throttle 2
#define Rudder   3
#define Pot_A    4
#define Pot_B    5
#define SW_A     6
#define SW_B     7
#define Virt_A   8
#define Virt_B   9

// Pressed/not pressed bitfields
#define K_MODE_A _BV(0)
#define K_MODE_B _BV(1)
#define K_DR     _BV(2)
#define K_SW_A1  _BV(3)
#define K_SW_A2  _BV(4)
#define K_SW_B   _BV(5)

// Endpoint values are signed and in 1% steps (-120%..120%)

// Main analog controls
typedef struct {
    // Endpoints (all types)
    int8_t low_ep;
    int8_t high_ep;
    // DR endpoints (ail, ele, rud)
    int8_t low_ep2;
    int8_t high_ep2;
    // Curve (all analog)
    int8_t curve[CURVE_NODES];
    // Source control (virtual)
    int8_t source;
} Control;

typedef struct {
    int8_t mix[NUM_CTLS];
    int8_t reverse;
} Channel;

typedef struct {
    Control controls[NUM_CTLS];
    Channel channels[NUM_CHANS];
} Mode;

typedef struct {
    uint8_t num_ch;
    Mode modes[NUM_MODES];
} Model;

#endif /* _MODEL_H_ */

#include <avr/io.h>
#include <avr/interrupt.h>

#include "uart.h"

static int errors;

#define BUFLEN 16
#define BUFLENMASK 15
static uint8_t buffer[BUFLEN];
static uint8_t volatile bstart;
static uint8_t volatile blen;

ISR(USART_RXC_vect) {
    uint8_t data = UDR;
    uint8_t place = (bstart + blen) & BUFLENMASK;
    buffer[place] = data;
    blen++;
    sei();
}

static uint8_t tbuf[BUFLEN];
static uint8_t volatile tbstart;
static uint8_t volatile tblen;
ISR(USART_TXC_vect) {
    tbstart = (tbstart + 1) & BUFLENMASK;
    tblen -= 1;
    if (tblen > 0) {
	UDR = tbuf[tbstart];
    }
    sei();
}

void uart_init() {
    UCSRA = 0; //(1 << U2X);
    UCSRB = (1 << RXEN ) | (1 << TXEN) | (1 << RXCIE) | (1 << TXCIE);
    UCSRC = (1 << URSEL) | (1 << UCSZ1) | (1 << UCSZ0); // | (1 << UPM1) | (1 << UPM0) 
    UBRRH = 0;
    UBRRL = 25;
    bstart = 0;
    blen = 0;
    errors = 0;
//    PIND |= (1 << PIND0);
    sei();
}

void uart_off() {
    UCSRA = 0;
    UCSRB = 0;
    UCSRC = 0;
    sei();
}

// set the uart baud rate
void uart_set_baud_rate(uint32_t baudrate)
{
    // calculate division factor for requested baud rate, and set it
    uint16_t bauddiv = (F_CPU)/(baudrate*16L)-1;
    UBRRL = bauddiv;
#ifdef UBRRH
    UBRRH = bauddiv>>8;
#endif
}

void uart_write_byte (uint8_t data) {
    while (tblen == BUFLEN);
    cli();
    int t = (tbstart + tblen) & BUFLENMASK;
    tbuf[t] = data;
    if(tblen == 0) {
	UDR = data;
    }
    tblen++;
    sei();
}

/* void uart_write_byte (uint8_t data) { */
/*     while ( !(UCSRA & (1 << UDRE)) ); */
/*     UDR = data; */
/* } */

int16_t uart_getchar()
{
    if (blen > 0) {
	char c = buffer[bstart];
	cli();
	bstart = (bstart + 1) & BUFLENMASK;
	blen--;
	sei();
	return c;
    }
    return -1;
}


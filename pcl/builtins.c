/* Built-in functions for PCL
  Most functionality wraps existing C functionality
*/
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <stdarg.h>

typedef int32_t integer;
typedef double real;
typedef int8_t boolean;
typedef int8_t chr;

// write
chr* writeInteger(integer n) {
  printf("%d", n);
  return NULL;
}

chr* writeBoolean(boolean b) {
  printf("%d", b);
  return NULL;
}

chr* writeChar(chr c) {
  printf("%c", c);
  return NULL;
}

chr* writeReal(real x) {
  printf("%f", x);
  return NULL;
}

chr* writeString(chr *s) {
  printf("%s", s);
  return NULL;
}


// read
integer readInteger() {
  integer n;
  scanf("%d", &n);
  return n;
}

boolean readBoolean() {
  boolean n;
  scanf("%d", &n);
  return n;
}

chr readChar() {
  chr n;
  n = getchar();
  return n;
}

real readReal() {
  real n;
  scanf("%f", &n);
  return n;
}

chr* readString(integer size, chr *target) {
  integer i;
  for (i = 0; i < size; i++) {
    *target = getchar();
    target++;
  }
  return NULL;
}

// ln
real ln(real x) {
  return log(x);
}

// arctan
real arctan(real x) {
  return (real)atan(x);
}

real pi() {
  return (real)M_PI;
}

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
  printf("%d\n", n);
  return NULL;
}

chr* writeBoolean(boolean b) {
  (b == 1) ? printf("true") : printf("false");
  printf("\n");
  return NULL;
}

chr* writeChar(chr c) {
  printf("%c", c);
  return NULL;
}

chr* writeReal(real x) {
  printf("%f\n", x);
  return NULL;
}

chr* writeString(chr *s) {
  printf("%s\n", s);
  return NULL;
}


// read
integer readInteger() {
  integer n;
  char t;
  scanf("%d%c", &n, &t);
  return (integer)n;
}

// ln
real ln(real x) {
  return log(x);
}

real pi() {
  return (real)M_PI;
}

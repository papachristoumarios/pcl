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

extern chr* writeInteger(integer);
extern chr* writeChar(chr);
extern chr* writeReal(real);
extern chr* writeBoolean(boolean);
extern chr* writeString(integer, ...);
extern integer readInteger();

// write
chr* writeInteger(integer n) {
  printf("%d\n", n);
}

chr* writeBoolean(boolean b) {
  (b == 1) ? printf("true") : printf("false");
  printf("\n");
}

chr* writeChar(chr c) {
  printf("%c\n", c + 'a' - 1);
}

chr* writeReal(real x) {
  printf("%f\n", x);
}

chr* writeString(integer len, ...) {
  va_list valist;
  va_start(valist, len);
  integer i;
  for (i = 0; i < len; i++) {
      putchar((chr)va_arg(valist, int) + 'a' - 1);
   }
   printf("\n");
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

int main() {
  writeString(3, 1, 2, 3);
  return 0;
}

/* Built-in functions for PCL
  Most functionality wraps existing C functionality
*/
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

typedef int32_t integer;
typedef double real;
typedef int8_t boolean;
typedef int8_t chr;

extern chr* writeInteger(integer);
extern chr* writeChar(chr);
extern chr* writeReal(real);
extern chr* writeString(chr*);

// write
chr* writeInteger(integer n) {
  printf("%d\n", n);
}

chr* writeBoolean(boolean b) {
  (b == 1) ? printf("true") : printf("false");
}

chr* writeChar(chr c) {
  printf("%c", c);
}

chr* writeReal(real x) {
  printf("%f", x);
}

chr* writeString(chr *s) {
  printf("%s", s);
}

// read
//
// real pi() {
//   return M_PI;
// }
//
// real ln(real x) {
//   return log(x);
// }

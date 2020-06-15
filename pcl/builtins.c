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
typedef int8_t character;

// write
character* writeInteger(integer n) {
  printf("%d", n);
  return NULL;
}

character* writeBoolean(boolean b) {
  if (b == 0) {
    printf("false");
  }
  else {
    printf("true");
  }
  return NULL;
}

character* writeChar(character c) {
  printf("%c", c);
  return NULL;
}

character* writeReal(real x) {
  printf("%f", x);
  return NULL;
}

character* writeString(character *s) {
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
  integer n;
  scanf("%d", &n);
  return (boolean)n;
}

character readChar() {
  character n;
  n = getchar();
  return n;
}

real readReal() {
  float n;
  scanf("%f", &n);
  return (double)n;
}

character* readString(integer size, character *s) {
    if (size <= 0) {
      return NULL;
    }

    // Create safeguard buffer
    character buf[size];

    // Sets the sequence to 0
    memset(buf, 0, size);

    if (size == 1) {
      return NULL;
    }

    size--; // Nead to read size - 1 chars

    // Counter
    integer i = 0;

    character c = getchar();

    // Read the string until EOF or newline

    for (i = 0; i < size; i++) {
      buf[i] = c;
      c = getchar();
      if (c == EOF || c == '\n') break;
    }

    // Copy from safeguard buffer
    strcpy((char *)s, (char *)buf);
    return NULL;
}

// ln
real ln(real x) {
  return log(x);
}

// arctan
real arctan(real x) {
  return (real) atan(x);
}

real pi() {
  return (real) M_PI;
}

integer trunc2(real x) {
  return (integer) trunc(x);
}

integer round2(real x){
  return (integer) round(x);
}

character chr(integer x){
  return (character) x;
}

integer ord(character x){
  return (integer) x;
}

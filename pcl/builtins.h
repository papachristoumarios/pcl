#ifndef builtins_h_
#define builtins_h_

extern chr* writeInteger(integer);
extern chr* writeChar(chr);
extern chr* writeReal(real);
extern chr* writeBoolean(boolean);
extern chr* writeString(chr *);
extern chr* writeStream(chr *);
extern integer readInteger();

#endif

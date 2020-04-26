#ifndef builtins_h_
#define builtins_h_

extern chr* writeInteger(integer);
extern chr* writeChar(chr);
extern chr* writeReal(real);
extern chr* writeBoolean(boolean);
extern chr* writeString(chr *);
extern integer readInteger();
extern boolean readBoolean();
extern chr readChar();
extern real readReal();
extern chr* readString(integer, chr*)

#endif

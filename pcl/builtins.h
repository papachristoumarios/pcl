#ifndef builtins_h_
#define builtins_h_

extern character* writeInteger(integer);
extern character* writeChar(character);
extern character* writeReal(real);
extern character* writeBoolean(boolean);
extern character* writeString(character *);
extern integer readInteger();
extern boolean readBoolean();
extern character readChar();
extern real readReal();
extern character* readString(integer, character*);
extern integer trunc2(real);
extern integer round2(real);
extern character chr(integer);
extern integer ord(character);
#endif

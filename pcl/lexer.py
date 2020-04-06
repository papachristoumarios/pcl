from sly import Lexer
from pcl.error import PCLLexerError
import re

def regex(s):
    return re.escape(s)


class PCLLexer(Lexer):
    tokens = {
        # keywords
        AND,
        DO,
        IF,
        OF,
        THEN,
        ARRAY,
        ELSE,
        INTEGER,
        OR,
        TRUE,
        BEGIN,
        END,
        LABEL,
        PROCEDURE,
        VAR,
        BOOLEAN,
        FALSE,
        MOD,
        PROGRAM,
        WHILE,
        CHAR,
        FORWARD,
        NEW,
        REAL,
        DISPOSE,
        FUNCTION,
        NIL,
        RESULT,
        DIV,
        GOTO,
        NOT,
        RETURN,
        # Arithmetic operators
        EQUAL,
        LPAREN,
        RPAREN,
        PLUS,
        MINUS,
        TIMES,
        FRAC,
        GT,
        LT,
        GTE,
        LTE,
        LSQUARE,
        RSQUARE,
        EXP,
        PTR,
        NEG,
        # Separators
        SET,
        SEMICOLON,
        COLON,
        DCOLON,
        COMMA,
        # others
        INT_CONS,
        REAL_CONS,
        CHARACTER,
        NAME,
        COMMENT,
        STRING,
        NEWLINE

    }

    # keywords
    AND = regex('and')
    DO = regex('do')
    IF = regex('if')
    OF = regex('of')
    THEN = regex('then')
    ARRAY = regex('array')
    ELSE = regex('else')
    INTEGER = regex('integer')
    OR = regex('or')
    TRUE = regex('true')
    BEGIN = regex('begin')
    END = regex('end')
    LABEL = regex('label')
    PROCEDURE = regex('procedure')
    VAR = regex('var')
    BOOLEAN = regex('boolean')
    FALSE = regex('false')
    MOD = regex('mod')
    PROGRAM = regex('program')
    WHILE = regex('while')
    CHAR = regex('char')
    FORWARD = regex('forward')
    NEW = regex('new')
    REAL = regex('real')
    DISPOSE = regex('dispose')
    FUNCTION = regex('function')
    NIL = regex('nil')
    RESULT = regex('result')
    DIV = regex('div')
    GOTO = regex('goto')
    NOT = regex('not')
    RETURN = regex('return')

    # Arithmetic operators
    EQUAL = regex('=')
    LPAREN = regex('(')
    RPAREN = regex(')')
    PLUS = regex('+')
    MINUS = regex('-')
    TIMES = regex('*')
    FRAC = regex('/')
    GT = regex('>')
    LT = regex('<')
    GTE = regex('>=')
    LTE = regex('<=')
    LSQUARE = regex('[')
    RSQUARE = regex(']')
    EXP = regex('^')
    PTR = regex('@')
    NEG = regex('<>')

    # Separators
    SET = regex(':=')
    SEMICOLON = regex(';')
    COLON = regex('.')
    DCOLON = regex(':')
    COMMA = regex(',')

    # "Special" tokens:
    INT_CONS = r'[0-9]+'
    REAL_CONS = r"[0-9]+(\.[0-9]+(['E', 'e']['\+','\-']?[0-9]+)?)?"
    NAME = r"(?<!\d\W\_)[^\d\W\_]\w*"
    CHARACTER = "'" + ".|" + "'"
    STRING = r"\"[^\"]*\""

    COMMENT = r'(?s)\(\*.*?\*\)'
    ignore = r'[\s, \t, \r]+'
    ignore_newline = '\n+'

    # "Special" functions:
    def COMMENT(self, t):
        self.lineno += t.value.count('\n')

    def ignore_newline(self, t):
        self.lineno += t.value.count('\n')

    def error(self, t):
        msg = 'Illegal character {} at line {}'.format(t.value[0], self.lineno)
        raise PCLLexerError(msg)


if __name__ == '__main__':
    lexer = PCLLexer()
    s = '''
        program collatz;

        label x, y;
        forward procedure hello();
        var x : integer;

        begin
          x := 6;
          while x > 1 do
          begin
            writeInteger(x);
            if x mod 2 = 0 then x := x div 2
            else x := 3 * x + 1;
          end;

        end.
        '''
    token_names = [x.value for x in lexer.tokenize(s)]
    token_types = [x.type for x in lexer.tokenize(s)]

    print(token_names)
    print(token_types)

from sly import Lexer
from pcl.error import PCLLexerError
import re


def regex(s):
    return re.escape(s)

def kw(s):
    return r'^{}$'.format(s)


class PCLLexer(Lexer):

    # keywords
    keywords = {
        regex('and') : 'AND',
        regex('do') : 'DO',
        regex('if') : 'IF',
        regex('of') : 'OF',
        regex('then') : 'THEN',
        regex('array') : 'ARRAY',
        regex('else') : 'ELSE',
        regex('integer') : 'INTEGER',
        regex('or') : 'OR',
        regex('true') : 'TRUE',
        regex('begin') : 'BEGIN',
        regex('end') : 'END',
        regex('label') : 'LABEL',
        regex('procedure') : 'PROCEDURE',
        regex('var') : 'VAR',
        regex('boolean') : 'BOOLEAN',
        regex('false') : 'FALSE',
        regex('mod') : 'MOD',
        regex('program') : 'PROGRAM',
        regex('while') : 'WHILE',
        regex('char') : 'CHAR',
        regex('forward') : 'FORWARD',
        regex('new') : 'NEW',
        regex('real') : 'REAL',
        regex('dispose') : 'DISPOSE',
        regex('function') : 'FUNCTION',
        regex('nil') : 'NIL',
        regex('result') : 'RESULT',
        regex('div') : 'DIV',
        regex('goto') : 'GOTO',
        regex('not') : 'NOT',
        regex('return') : 'RETURN'
    }

    tokens = {
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
        ADDRESSOF,
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
        STRING,
        NEWLINE
    } | set(keywords.values())

    # Ignore multiline comments
    ignore_comment = r'(?s)\(\*.*?\*\)'

    # This must be a string and not [\s, \t, \r ] according to SLY docs
    ignore = ' \t\r'

    # Arithmetic operators
    EQUAL = regex('=')
    LPAREN = regex('(')
    RPAREN = regex(')')
    PLUS = regex('+')
    MINUS = regex('-')
    TIMES = regex('*')
    FRAC = regex('/')
    NEG = regex('<>')
    GTE = regex('>=')
    LTE = regex('<=')
    GT = regex('>')
    LT = regex('<')
    LSQUARE = regex('[')
    RSQUARE = regex(']')
    EXP = regex('^')
    ADDRESSOF = regex('@')

    # Separators
    SET = regex(':=')
    SEMICOLON = regex(';')
    COLON = regex('.')
    DCOLON = regex(':')
    COMMA = regex(',')

    # "Special" tokens:
    INT_CONS = r'[0-9]+(?!\.)'
    REAL_CONS = r"[0-9]+(\.[0-9]+(['E', 'e']['\+','\-']?[0-9]+)?)?"
    NAME = r"(?<!\d\W\_)[^\d\W\_]\w*"
    CHARACTER = r"('.')"
    STRING = r"\"[^\"]*\""

    # Ignore newlines
    ignore_newline = '\n+'

    def NAME(self, t):
        t.type = PCLLexer.keywords.get(t.value, 'NAME')
        return t

    # Increase line counts upon newlines and comments
    def ignore_comment(self, t):
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
            var x, y : integer;
        end.
        '''
    token_names = [x.value for x in lexer.tokenize(s)]
    token_types = [x.type for x in lexer.tokenize(s)]

    print(token_names)
    print(token_types)

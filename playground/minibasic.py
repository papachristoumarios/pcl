from sly import Lexer, Parser
from ctypes import CFUNCTYPE, c_double
from llvmlite import ir, binding
import os


class MinibasicLexer(Lexer):
    tokens = {
        PLUS,
        TIMES,
        MINUS,
        DIVIDE,
        MODULO,
        ASSIGN,
        LPAREN,
        RPAREN,
        FOR,
        PRINT,
        LET,
        IF,
        THEN,
        ELSE,
        DO,
        BEGIN,
        END,
        ID,
        CONST,
    }

    ignore = ' \t'

    # Tokens
    FOR = r'for'
    PRINT = r'print'
    LET = r'let'
    IF = r'if'
    THEN = r'then'
    ELSE = r'else'
    DO = r'do'
    BEGIN = r'begin'
    END = r'end'

    PLUS = r'\+'
    MINUS = r'-'
    TIMES = r'\*'
    DIVIDE = r'/'
    MODULO = r'%'
    ASSIGN = r'='
    LPAREN = r'\('
    RPAREN = r'\)'

    ID = r'[a-z]+'
    CONST = r'\d+'

    ignore_newline = '\n+'

    def ignore_newline(self, t):
        self.lineno += t.value.count('\n')

    def error(self, t):
        print(
            'Illegal character {} at line {}'.format(
                t.value[0],
                self.lineno))
        self.index += 1


class MinibasicParser(Parser):

    tokens = MinibasicLexer.tokens

    precedence = (
        ('left', 'PLUS', 'MINUS'),
        ('left', 'TIMES', 'DIVIDE', 'MODULO'),
    )

    @_('stmt_list')
    def program(self, p):
        return Program(p.stmt_list)

    @_('stmt')
    def stmt_list(self, p):
        return [p.stmt]

    @_('stmt_list stmt')
    def stmt_list(self, p):
        return p.stmt_list + [p.stmt]

    @_('LET ID ASSIGN expr')
    def stmt(self, p):
        return Let(p.ID, p.expr)

    @_('PRINT expr')
    def stmt(self, p):
        return Print(p.expr)

    @_('FOR expr DO stmt')
    def stmt(self, p):
        return For(p.expr, p.stmt)

    @_('IF expr THEN stmt')
    def stmt(self, p):
        print('STMT')
        return If(p.expr, p.stmt)

    @_('IF expr THEN stmt ELSE stmt')
    def stmt(self, p):
        return If(p.expr, p.stmt0, p.stmt1)

    @_('BEGIN stmt_list END')
    def stmt(self, p):
        return p.stmt_list

    @_('ID')
    def expr(self, p):
        return Id(p.ID)

    @_('CONST')
    def expr(self, p):
        return Constant(p.CONST)

    @_('expr PLUS expr')
    def expr(self, p):
        return BinOp('+', p.expr0, p.expr1)

    @_('expr MINUS expr')
    def expr(self, p):
        return BinOp('-', p.expr0, p.expr1)

    @_('expr TIMES expr')
    def expr(self, p):
        return BinOp('*', p.expr0, p.expr1)

    @_('expr DIVIDE expr')
    def expr(self, p):
        return BinOp('/', p.expr0, p.expr1)

    @_('expr MODULO expr')
    def expr(self, p):
        return BinOp('%', p.expr0, p.expr1)

    @_('LPAREN expr RPAREN')
    def expr(self, p):
        return p.expr


global_names = {}


class AST:
    def eval(self):
        pass


class Program(AST):

    def __init__(self, stmt_list):
        self.stmt_list = stmt_list

    def eval(self):
        for stmt in self.stmt_list:
            stmt.eval()


class Print(AST):

    def __init__(self, expr):
        self.expr = expr

    def eval(self):
        print(self.expr.eval())


class For(AST):

    def __init__(self, expr, stmt):
        self.expr = expr
        self.stmt = stmt

    def eval(self):
        times = expr.eval()
        i = 0
        while i < times:
            self.stmt.eval()
            times = expr.eval()


class If(AST):

    def __init__(self, expr, stmt, else_stmt=None):
        self.expr = expr
        self.stmt = stmt
        self.else_stmt = else_stmt

    def eval(self):
        flag = self.expr.eval()
        if flag == 1:
            self.stmt.eval()
        elif else_stmt:
            self.else_stmt.eval()


class Let(AST):

    def __init__(self, id_, expr):
        self.id = id_
        self.expr = expr

    def eval(self):
        global global_names
        global_names[self.id] = self.expr.eval()


class Block(AST):
    pass


class Id(AST):

    def __init__(self, id_):
        self.id = id_

    def eval(self):
        return global_names[self.id]


class Constant(AST):

    def __init__(self, value):
        self.value = int(value)

    def eval(self):
        return self.value


class BinOp(AST):

    def __init__(self, op, lhs, rhs):
        self.op = op
        self.lhs = lhs
        self.rhs = rhs

    def eval(self):
        if self.op == '+':
            return self.lhs.eval() + self.rhs.eval()
        if self.op == '-':
            return self.lhs.eval() - self.rhs.eval()
        if self.op == '*':
            return self.lhs.eval() * self.rhs.eval()
        if self.op == '/':
            return self.lhs.eval() // self.rhs.eval()
        if self.op == '%':
            return self.lhs.eval() % self.rhs.eval()


if __name__ == '__main__':
    minibasic_lexer = MinibasicLexer()
    minibasic_parser = MinibasicParser()

    while True:
        try:
            print('> ', end='')
            s = input()
            lexed = minibasic_lexer.tokenize(s)
            minibasic_parser.parse(lexed).eval()
        except EOFError:
            exit(0)
        except BaseException:
            print('Action "{}" not recognized'.format(s))

from sly import Parser
from collections import deque

from pcl.lexer import PCLLexer
from pcl.error import PCLParserError
from pcl.ast import *
from pcl.symbol_table import SymbolTable
from pcl.codegen import PCLCodegen


class PCLParser(Parser):
    '''
        Contains the main functionality of the PCL Parser
        built with the SLY tool
    '''

    def __init__(self):
        '''
            Constructor for the PCL Parser

            Args:
                builder: LLVM IR code builder through codegen. Defaults to None
                module: LLVM module object
                printf: LLVM printf function
        '''
        self.codegen = PCLCodegen()
        self.symbol_table = SymbolTable()
        self.builder = self.codegen.builder
        self.module = self.codegen.module


        self.the_nil = Nil(self.builder, self.module, self.symbol_table)

    # Tokens from PCLLexer
    tokens = PCLLexer.tokens

    # Associativity and priority of operators
    # precedence = (
    #     ('left', 'EQUAL', 'GT', 'LT', 'GTE', 'LTE', 'NEG'),
    #     ('left', 'PLUS', 'MINUS', 'OR'),
    #     ('left', 'TIMES', 'FRAC', 'DIV', 'MOD',
    #     ('nonassoc', 'UN_OP'),
    #     ('nonassoc', 'BRACKETS'),
    #     ('nonassoc', 'RVALUE'),
    #     ('nonassoc', 'SINGLE_IF'),
    #     ('nonassoc', 'ELSE'))
    # )

    @_('PROGRAM NAME SEMICOLON body COLON')
    def program(self, p):
        import pdb
        pdb.set_trace()
        return Program(
            p.NAME,
            p.body,
            self.builder,
            self.module,
            self.symbol_table)

    @_('local_list block')
    def body(self, p):
        return Body(
            p.local_list,
            p.block,
            self.builder,
            self.module,
            self.symbol_table)

    @_('')
    def local_list(self, p):
        return deque([])

    @_('local_list local'):
    def local_list(self, p):
        p.local_list.append(p.local)
        return p.local_list

    @_('INTEGER', 'REAL', 'BOOLEAN', 'CHAR')
    def type_(self, p):
        return Type(p[0], self.builder, self.module, self.symbol_table)

    @_('TRUE', 'FALSE')
    def rvalue(self, p):
        return BoolConst(p[0], self.builder, self.module, self.symbol_table)

    @_('INT_CONS')
    def rvalue(self, p):
        return IntegerConst(p[0], self.builder, self.module, self.symbol_table)

    @_('REAL_CONS')
    def rvalue(self, p):
        return RealConst(p[0], self.builder, self.module, self.symbol_table)

    @_('CHAR_CONS')
    def rvalue(self, p):
        return CharConst(p[0], self.builder, self.module, self.symbol_table)

    @_('LPAREN rvalue RPAREN')
    def rvalue(self, p):
        return p.rvalue

    @_('NIL')
    def rvalue(self, p):
        return self.the_nil

    @_('call')
    def rvalue(self, p):
        return p.call

    @_('PTR lvalue')
    def rvalue(self, p):
        return Ref(p[1], self.builder, self.module, self.symbol_table)

    @_('unop expr'):
    def rvalue(self, p):
        return UnOp(
            p.unop,
            p.expr,
            self.builder,
            self.module,
            self.symbol_table)

    @_('expr binop expr')
    def rvalue(self, p):
        return BinOp(
            p.binop,
            p.expr0,
            p.expr1,
            self.builder,
            self.module,
            self.symbol_table)

    @_('NAME LPAREN expr expr_list RPAREN')
    def call(self, p):
        exprs = p.expr_list.appendleft(p.expr)
        return Call(
            p.NAME,
            exprs,
            self.builder,
            self.module,
            self.symbol_table)

    @_('NOT', 'PLUS', 'MINUS')
    def unop(self, p):
        return p[0]

    @_('PLUS', 'MINUS', 'TIMES', 'FRAC', 'GT', 'LT', 'GTE',
       'LTE', 'DIV', 'MOD', 'OR', 'AND', 'EQUAL', 'NEG')
    def binop(self, p):
        return p[0]

    @_('')
    def expr_list(self, p):
        return deque([])

    @_('expr_list COMMA expr')
    def expr_list(self, p):
        p.expr_list.append(p.expr)
        return p.expr_list

    def error(self, p):
        msg = 'Illegal rule {}'.format(str(p))
        raise PCLParserError(msg)


if __name__ == '__main__':
    s = 'program hello ;'
    lexer = PCLLexer()
    parser = PCLParser()
    program = parser.parse(lexer.tokenize(s))

    import pdb
    pdb.set_trace()

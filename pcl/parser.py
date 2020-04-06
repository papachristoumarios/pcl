from sly import Parser
from collections import deque
import pprint

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

        self.the_nil = Nil(
            builder=self.builder,
            module=self.module,
            symbol_table=self.symbol_table)

    # Tokens from PCLLexer
    tokens = PCLLexer.tokens - {COMMENT}

    # Associativity and priority of operators
    precedence = (
        ('nonassoc', 'EQUAL', 'GT', 'LT', 'GTE', 'LTE', 'NEG'),
        ('left', 'PLUS', 'MINUS', 'OR'),
        ('left', 'TIMES', 'FRAC', 'DIV', 'MOD', 'AND'),
        ('nonassoc', 'UN_OP'),
        ('nonassoc', 'EXP'),
        ('nonassoc', 'ADDRESSOF'),
        ('nonassoc', 'BRACKETS'),
        ('nonassoc', 'RVALUE'),
        ('nonassoc', 'SINGLE_IF'),
        ('nonassoc', 'ELSE')
    )

    @_('PROGRAM NAME SEMICOLON body COLON')
    def program(self, p):
        return Program(
            id_=p.NAME,
            body=p.body,
            builder=self.builder,
            module=self.module,
            symbol_table=self.symbol_table)

    @_('local_list block')
    def body(self, p):
        return Body(
            locals_=p.local_list,
            block=p.block,
            builder=self.builder,
            module=self.module,
            symbol_table=self.symbol_table)

    @_('VAR var_list')
    def local(self, p):
        return VarList(vars=p.var_list, builder=self.builder,
                       module=self.module, symbol_table=self.symbol_table)

    @_('LABEL id_list SEMICOLON')
    def local(self, p):
        return Label(ids=p.id_list, builder=self.builder, module=self.module,
                     symbol_table=self.symbol_table)

    @_('header SEMICOLON body SEMICOLON')
    def local(self, p):
        return LocalHeader(header=p.header, body=p.body, builder=self.builder,
                           module=self.module, symbol_table=self.symbol_table)

    @_('FORWARD header SEMICOLON')
    def local(self, p):
        return Forward(header=p.header, builder=self.builder,
                       module=self.module, symbol_table=self.symbol_table)

    @_('')
    def local_list(self, p):
        return deque([])

    @_('local_list local')
    def local_list(self, p):
        p.local_list.append(p.local)
        return p.local_list

    @_('NAME id_list DCOLON type_ SEMICOLON')
    def var(self, p):
        return Var(ids_=p.id_list, type_=p.type_, builder=self.builder,
                   module=self.module, symbol_table=self.symbol_table)

    @_('NAME comma_id_list')
    def id_list(self, p):
        p.comma_id_list.appendleft(p.NAME)
        return p.comma_id_list

    @_('')
    def comma_id_list(self, p):
        return deque([])

    @_('comma_id_list COMMA NAME')
    def comma_id_list(self, p):
        p.id_list.append(p.NAME)
        return p_id_list

    @_('var')
    def var_list(self, p):
        return deque([p.var])

    @_('var_list var')
    def var_list(self, p):
        p.var_list.append(p.var)
        return p.var_list

    @_('PROCEDURE NAME LPAREN formal_list RPAREN')
    def header(self, p):
        return Header(header_type=p[0], id_=p.NAME, formals=p.formal_list,
                      func_type=None, builder=self.builder, module=self.module,
                      symbol_table=self.symbol_table)

    @_('PROCEDURE NAME LPAREN RPAREN')
    def header(self, p):
        return Header(header_type=p[0], id_=p.NAME, formals=deque([]),
                      func_type=None, builder=self.builder, module=self.module,
                      symbol_table=self.symbol_table)

    @_('FUNCTION NAME LPAREN formal_list RPAREN DCOLON type_')
    def header(self, p):
        return Header(header_type=p[0], id_=p.NAME,
                      formals=p.formal_list, func_type=p.type_,
                      builder=self.builder, module=self.module,
                      symbol_table=self.symbol_table)

    @_('FUNCTION NAME LPAREN RPAREN DCOLON type_')
    def header(self, p):
        return Header(header_type=p[0], id_=p.NAME, formals=deque([]),
                      func_type=p.type_, builder=self.builder,
                      module=self.module, symbol_table=self.symbol_table)

    @_('id_list DCOLON type_', 'VAR id_list DCOLON type_')
    def formal(self, p):
        return Formal(ids=p.id_list, type_=p.type_, builder=self.builder,
                      module=self.module, symbol_table=self.symbol_table)

    @_('formal semicolon_formal_list')
    def formal_list(self, p):
        p.semicolon_formal_list.append(formal)
        return p.semicolon_formal_list

    @_('')
    def semicolon_formal_list(self, p):
        return deque([])

    @_('semicolon_formal_list SEMICOLON formal')
    def semicolon_formal_list(self, p):
        p.semicolon_formal_list.append(p.formal)
        return p.semicolon_formal_list

    # FROM HERE
    @_('INTEGER', 'REAL', 'BOOLEAN', 'CHAR')
    def type_(self, p):
        return Type(type_=p[0], builder=self.builder, module=self.module,
                    symbol_table=self.symbol_table)

    @_('ARRAY LSQUARE INT_CONS RSQUARE OF type_')
    def type_(self, p):
        return ArrayType(length=p[2], type_=p.type_, builder=self.builder,
                         module=self.module, symbol_table=self.symbol_table)

    @_('ARRAY OF type_')
    def type_(self, p):
        # We do not know the length, so we use -1.
        return ArrayType(length=-1, type_=p.type_, builder=self.builder,
                         module=self.module, symbol_table=self.symbol_table)

    @_('EXP type_')
    def type_(self, p):
        return PointerType(type_=p.type_, builder=self.builder,
                           module=self.module, symbol_table=self.symbol_table)

    @_('BEGIN stmt semicolon_stmt_list END')
    def block(self, p):
        p.semicolon_stmt_list.appendleft(p.stmt)
        return p.semicolon_stmt_list

    @_('')
    def semicolon_stmt_list(self, p):
        return deque([])

    @_('semicolon_stmt_list SEMICOLON stmt')
    def semicolon_stmt_list(self, p):
        p.semicolon_stmt_list.append(p.stmt)
        return p.semicolon_stmt_list

    # STATEMENT
    @_('')
    def stmt(self, p):
        return Empty(
            builder=self.builder,
            module=self.module,
            symbol_table=self.symbol_table)

    @_('lvalue SET expr')
    def stmt(self, p):
        return SetExpression(
            lvalue=p.lvalue,
            expr=p.expr,
            builder=self.builder,
            module=self.module,
            symbol_table=self.symbol_table)

    @_('NEW lvalue')
    def stmt(self, p):
        return New(expr=None, lvalue=p.lvalue, builder=self.builder,
                   module=self.module, symbol_table=self.symbol_table)

    @_('NEW LSQUARE expr RSQUARE lvalue')
    def stmt(self, p):
        return New(expr=p.expr, lvalue=p.lvalue, builder=self.builder,
                   module=self.module, symbol_table=self.symbol_table)

    @_('DISPOSE LSQUARE RSQUARE lvalue', 'DISPOSE lvalue')
    def stmt(self, p):
        return Dispose(lvalue=p.lvalue, builder=self.builder,
                       module=self.module, symbol_table=self.symbol_table)

    @_('RETURN')
    def stmt(self, p):
        return Return(
            builder=self.builder,
            module=self.module,
            symbol_table=self.symbol_table)

    @_('GOTO NAME')
    def stmt(self, p):
        return Goto(id_=p.NAME, builder=self.builder, module=self.module,
                    symbol_table=self.symbol_table)

    @_('WHILE expr DO stmt')
    def stmt(self, p):
        return While(expr=p.expr, stmt=p.stms, builder=self.builder,
                     module=self.module, symbol_table=self.symbol_table)


    @_('NAME DCOLON stmt')
    def stmt(self, p):
        return Statement(name=p.NAME, builder=self.builder, module=self.module,
                         symbol_table=self.symbol_table)


    @_('IF expr THEN stmt %prec SINGLE_IF')
    def stmt(self, p):
        return If(expr=p.expr, stmt=p.stmt, else_stmt=None,
                  builder=self.builder, module=self.module,
                  symbol_table=self.symbol_table)

    @_('IF expr THEN stmt ELSE stmt')
    def stmt(self, p):
        return If(expr=p.expr, stmt=p[3], else_stmt=p[5],
                  builder=self.builder, module=self.module,
                  symbol_table=self.symbol_table)

    @_('call')
    def stmt(self, p):
        return p.call

    # EXPRESSION := lvalue | rvalue (precedence to r-value)
    @_('rvalue %prec RVALUE')
    def expr(self, p):
        return p.rvalue

    @_('lvalue')
    def expr(self, p):
        return p.lvalue

    # LVALUE
    @_('NAME')
    def lvalue(self, p):
        return NameLValue(id_=p.NAME, builder=self.builder, module=self.module,
                          symbol_table=self.symbol_table)

    @_('STRING')
    def lvalue(self, p):
        return StringLiteral(
            literal=p[0],
            builder=self.builder,
            module=self.module,
            symbol_table=self.symbol_table)

    @_('lvalue LSQUARE expr RSQUARE %prec BRACKETS')
    def lvalue(self, p):
        return LBrack(lvalue=p.lvalue, expr=p.expr, module=self.module,
                      builder=self.builder,
                      symbol_table=self.symbol_table)

    @_('expr EXP')
    def lvalue(self, p):
        return Deref(expr=p.expr, builder=self.builder, module=self.module,
                     symbol_table=self.symbol_table)

    @_('LPAREN lvalue RPAREN')
    def lvalue(self, p):
        return p.lvalue

    @_('RESULT')
    def lvalue(self, p):
        return Result(builder=self.builder, module=self.module,
                      symbol_table=self.symbol_table)

    # RVALUE
    @_('INT_CONS')
    def rvalue(self, p):
        return IntegerConst(
            value=p[0],
            builder=self.builder,
            module=self.module,
            symbol_table=self.symbol_table)

    @_('TRUE', 'FALSE')
    def rvalue(self, p):
        return BoolConst(value=p[0], builder=self.builder, module=self.module,
                         symbol_table=self.symbol_table)

    @_('REAL_CONS')
    def rvalue(self, p):
        return RealConst(value=p[0], builder=self.builder, module=self.module,
                         symbol_table=self.symbol_table)

    @_('CHARACTER')
    def rvalue(self, p):
        return CharConst(value=p[0], builder=self.builder, module=self.module,
                         symbol_table=self.symbol_table)

    @_('LPAREN rvalue RPAREN')
    def rvalue(self, p):
        return p.rvalue

    @_('ADDRESSOF expr')
    def rvalue(self, p):
        # TODO address of must impose lvalue!!!
        return AddressOf(lvalue=p[1], builder=self.builder, module=self.module,
                         symbol_table=self.symbol_table)

    @_('NIL')
    def rvalue(self, p):
        return self.the_nil

    # UNARY OPERATORS
    @_('unop expr %prec UN_OP')
    def rvalue(self, p):
        return UnOp(
            op=p.unop,
            rhs=p.expr,
            builder=self.builder,
            module=self.module,
            symbol_table=self.symbol_table)

    @_('expr PLUS expr',
       'expr MINUS expr',
       'expr TIMES expr',
       'expr FRAC expr',
       'expr GT expr',
       'expr LT expr',
       'expr GTE expr',
       'expr LTE expr',
       'expr DIV expr',
       'expr MOD expr',
       'expr OR expr',
       'expr AND expr',
       'expr EQUAL expr',
       'expr NEG expr',
       )
    def rvalue(self, p):
        return BinOp(
            op=p.expr0,
            lhs=p[0],
            rhs=p.expr1,
            builder=self.builder,
            module=self.module,
            symbol_table=self.symbol_table)

    @_('NOT', 'PLUS', 'MINUS')
    def unop(self, p):
        return p[0]

    # CALL
    @_('NAME LPAREN expr comma_expr_list RPAREN')
    def call(self, p):
        p.comma_expr_list.appendleft(p.expr)
        return Call(
            id_=p.NAME,
            exprs=p.comma_expr_list,
            builder=self.builder,
            module=self.module,
            symbol_table=self.symbol_table)

    @_('NAME LPAREN RPAREN')
    def call(self, p):
        return Call(
            id_=p.NAME,
            exprs=deque([]),
            builder=self.builder,
            module=self.module,
            symbol_table=self.symbol_table)

    @_('')
    def comma_expr_list(self, p):
        return deque([])

    @_('comma_expr_list COMMA expr')
    def comma_expr_list(self, p):
        p.comma_expr_list.append(p.expr)
        return p.comma_expr_list

    def error(self, p):
        msg = 'Illegal rule {}'.format(str(p))
        raise PCLParserError(msg)


if __name__ == '__main__':
    s = '''
        program hello;
        begin
            writeString("hello");
            x := 2;
        end.
        '''
    lexer = PCLLexer()
    parser = PCLParser()
    program = parser.parse(lexer.tokenize(s))

    program.pprint()

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
        self.arithmetic = ['+', '-', '*', '/', 'div', 'mod']
        self.comp = ['>=', '<=', '>', '<', '=', '<>']
        self.logical = ['and', 'or', 'not']
        self.codegen = PCLCodegen()
        self.builder = self.codegen.builder
        self.module = self.codegen.module
        self.symbol_table = SymbolTable(self.module)

        self.the_nil = Nil(
            builder=self.builder,
            module=self.module,
            symbol_table=self.symbol_table, lineno=-1)

    # Tokens from PCLLexer
    tokens = PCLLexer.tokens

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
        ('nonassoc', 'ELSE'),
    )

    def get_lineno(self, p):
        try:
            return p.lineno
        except AttributeError:
            return -1

    @_('PROGRAM NAME SEMICOLON body COLON')
    def program(self, p):
        return Program(
            id_=p.NAME,
            body=p.body,
            builder=self.builder,
            module=self.module,
            symbol_table=self.symbol_table, lineno=self.get_lineno(p))

    @_('local_list block')
    def body(self, p):
        return Body(
            locals_=p.local_list,
            block=p.block,
            builder=self.builder,
            module=self.module,
            symbol_table=self.symbol_table, lineno=-1)

    @_('VAR var_list')
    def local(self, p):
        return VarList(
            vars_=p.var_list,
            builder=self.builder,
            module=self.module,
            symbol_table=self.symbol_table,
            lineno=self.get_lineno(p))

    @_('LABEL id_list SEMICOLON')
    def local(self, p):
        return Label(ids=p.id_list, builder=self.builder, module=self.module,
                     symbol_table=self.symbol_table, lineno=self.get_lineno(p))

    @_('header SEMICOLON body SEMICOLON')
    def local(self, p):
        return LocalHeader(
            header=p.header,
            body=p.body,
            builder=self.builder,
            module=self.module,
            symbol_table=self.symbol_table,
            lineno=self.get_lineno(p))

    @_('FORWARD header SEMICOLON')
    def local(self, p):
        return Forward(
            header=p.header,
            builder=self.builder,
            module=self.module,
            symbol_table=self.symbol_table,
            lineno=self.get_lineno(p))

    @_('local_list local')
    def local_list(self, p):
        p.local_list.append(p.local)
        return p.local_list

    @_('')
    def local_list(self, p):
        return deque([])

    @_('id_list DCOLON vartype SEMICOLON')
    def var(self, p):
        return Var(
            ids=p.id_list,
            type_=p.vartype,
            builder=self.builder,
            module=self.module,
            symbol_table=self.symbol_table,
            lineno=self.get_lineno(p))

    @_('NAME comma_id_list')
    def id_list(self, p):
        p.comma_id_list.appendleft(p.NAME)
        return p.comma_id_list

    @_('')
    def comma_id_list(self, p):
        return deque([])

    @_('comma_id_list COMMA NAME')
    def comma_id_list(self, p):
        p.comma_id_list.append(p.NAME)
        return p.comma_id_list

    @_('var')
    def var_list(self, p):
        return deque([p.var])

    @_('var_list var')
    def var_list(self, p):
        p.var_list.append(p.var)
        return p.var_list

    @_('PROCEDURE NAME LPAREN formal_list RPAREN')
    def header(self, p):
        return Header(
            header_type=p[0],
            id_=p.NAME,
            formals=p.formal_list,
            func_type=None,
            builder=self.builder,
            module=self.module,
            symbol_table=self.symbol_table,
            lineno=self.get_lineno(p))

    @_('PROCEDURE NAME LPAREN RPAREN')
    def header(self, p):
        return Header(
            header_type=p[0],
            id_=p.NAME,
            formals=deque(
                []),
            func_type=None,
            builder=self.builder,
            module=self.module,
            symbol_table=self.symbol_table,
            lineno=self.get_lineno(p))

    @_('FUNCTION NAME LPAREN formal_list RPAREN DCOLON vartype')
    def header(self, p):
        return Header(
            header_type=p[0],
            id_=p.NAME,
            formals=p.formal_list,
            func_type=p.vartype,
            builder=self.builder,
            module=self.module,
            symbol_table=self.symbol_table,
            lineno=self.get_lineno(p))

    @_('FUNCTION NAME LPAREN RPAREN DCOLON vartype')
    def header(self, p):
        return Header(
            header_type=p[0],
            id_=p.NAME,
            formals=deque(
                []),
            func_type=p.vartype,
            builder=self.builder,
            module=self.module,
            symbol_table=self.symbol_table,
            lineno=self.get_lineno(p))

    @_('VAR id_list DCOLON vartype')
    def formal(self, p):
        return Formal(
            ids=p.id_list,
            type_=p.vartype,
            by_reference=True,
            builder=self.builder,
            module=self.module,
            symbol_table=self.symbol_table, lineno=self.get_lineno(p))

    @_('id_list DCOLON vartype')
    def formal(self, p):
        return Formal(
            ids=p.id_list,
            type_=p.vartype,
            by_reference=False,
            builder=self.builder,
            module=self.module,
            symbol_table=self.symbol_table, lineno=self.get_lineno(p))

    @_('formal semicolon_formal_list')
    def formal_list(self, p):
        p.semicolon_formal_list.appendleft(p.formal)
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
    def vartype(self, p):
        return Type(type_=p[0], builder=self.builder, module=self.module,
                    symbol_table=self.symbol_table, lineno=self.get_lineno(p))

    @_('ARRAY LSQUARE INT_CONS RSQUARE OF vartype')
    def vartype(self, p):
        return ArrayType(
            length=p[2],
            type_=p.vartype,
            builder=self.builder,
            module=self.module,
            symbol_table=self.symbol_table,
            lineno=self.get_lineno(p))

    @_('ARRAY OF vartype')
    def vartype(self, p):
        return ArrayType(
            length=0,
            type_=p.vartype,
            builder=self.builder,
            module=self.module,
            symbol_table=self.symbol_table,
            lineno=self.get_lineno(p))

    @_('EXP vartype')
    def vartype(self, p):
        return PointerType(
            type_=p.vartype,
            builder=self.builder,
            module=self.module,
            symbol_table=self.symbol_table,
            lineno=self.get_lineno(p))

    @_('BEGIN stmt semicolon_stmt_list END')
    def block(self, p):
        p.semicolon_stmt_list.appendleft(p.stmt)
        return Block(
            stmt_list=p.semicolon_stmt_list,
            builder=self.builder,
            module=self.module,
            symbol_table=self.symbol_table,
            lineno=self.get_lineno(p))

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
        # Initialize lineno later
        return Empty(
            builder=self.builder,
            module=self.module,
            symbol_table=self.symbol_table, lineno=-1)

    @_('block')
    def stmt(self, p):
        return p.block

    @_('lvalue SET expr')
    def stmt(self, p):
        return SetExpression(
            lvalue=p.lvalue,
            expr=p.expr,
            builder=self.builder,
            module=self.module,
            symbol_table=self.symbol_table, lineno=self.get_lineno(p))

    @_('NEW lvalue')
    def stmt(self, p):
        return New(
            expr=None,
            lvalue=p.lvalue,
            builder=self.builder,
            module=self.module,
            symbol_table=self.symbol_table,
            lineno=self.get_lineno(p))

    @_('NEW LSQUARE expr RSQUARE lvalue')
    def stmt(self, p):
        p.lvalue.load = True
        return New(
            expr=p.expr,
            lvalue=p.lvalue,
            builder=self.builder,
            module=self.module,
            symbol_table=self.symbol_table,
            lineno=self.get_lineno(p))

    @_('DISPOSE lvalue')
    def stmt(self, p):
        return Dispose(
            lvalue=p.lvalue,
            brackets=False,
            builder=self.builder,
            module=self.module,
            symbol_table=self.symbol_table,
            lineno=self.get_lineno(p))

    @_('DISPOSE LSQUARE RSQUARE lvalue')
    def stmt(self, p):
        return Dispose(
            lvalue=p.lvalue,
            brackets=True,
            builder=self.builder,
            module=self.module,
            symbol_table=self.symbol_table,
            lineno=self.get_lineno(p))

    @_('RETURN')
    def stmt(self, p):
        return Return(
            builder=self.builder,
            module=self.module,
            symbol_table=self.symbol_table, lineno=self.get_lineno(p))

    @_('GOTO NAME')
    def stmt(self, p):
        return Goto(id_=p.NAME, builder=self.builder, module=self.module,
                    symbol_table=self.symbol_table, lineno=self.get_lineno(p))

    @_('WHILE expr DO stmt')
    def stmt(self, p):
        return While(
            expr=p.expr,
            stmt=p.stmt,
            builder=self.builder,
            module=self.module,
            symbol_table=self.symbol_table,
            lineno=self.get_lineno(p))

    @_('IF expr THEN stmt else_stmt')
    def stmt(self, p):
        # import pdb; pdb.set_trace()
        return If(expr=p.expr, stmt=p[3], else_stmt=p.else_stmt,
                  builder=self.builder, module=self.module,
                  symbol_table=self.symbol_table, lineno=self.get_lineno(p))

    @_('ELSE stmt')
    def else_stmt(self, p):
        return p.stmt

    @_('%prec SINGLE_IF')
    def else_stmt(self, p):
        return None

    @_('NAME DCOLON stmt')
    def stmt(self, p):
        return Statement(
            name=p.NAME,
            stmt=p.stmt,
            builder=self.builder,
            module=self.module,
            symbol_table=self.symbol_table, lineno=self.get_lineno(p))

    @_('call')
    def stmt(self, p):
        return p.call

    # EXPRESSION := lvalue | rvalue (precedence to r-value)
    @_('rvalue %prec RVALUE')
    def expr(self, p):
        return p.rvalue

    @_('lvalue')
    def expr(self, p):
        p.lvalue.load = True
        return p.lvalue

    # LVALUE
    @_('NAME')
    def lvalue(self, p):
        return NameLValue(
            id_=p.NAME,
            builder=self.builder,
            module=self.module,
            symbol_table=self.symbol_table,
            lineno=self.get_lineno(p))

    @_('STRING')
    def lvalue(self, p):
        return StringLiteral(
            literal=p[0][1:-1],
            builder=self.builder,
            module=self.module,
            symbol_table=self.symbol_table, lineno=self.get_lineno(p))

    @_('lvalue LSQUARE expr RSQUARE %prec BRACKETS')
    def lvalue(self, p):
        return LBrack(
            lvalue=p.lvalue,
            expr=p.expr,
            module=self.module,
            builder=self.builder,
            symbol_table=self.symbol_table,
            lineno=self.get_lineno(p))

    @_('expr EXP')
    def lvalue(self, p):
        return Deref(expr=p.expr, builder=self.builder, module=self.module,
                     symbol_table=self.symbol_table, lineno=self.get_lineno(p))

    @_('LPAREN lvalue RPAREN')
    def lvalue(self, p):
        return p.lvalue

    @_('RESULT')
    def lvalue(self, p):
        return Result(
            builder=self.builder,
            module=self.module,
            symbol_table=self.symbol_table,
            lineno=self.get_lineno(p))

    # RVALUE
    @_('INT_CONS')
    def rvalue(self, p):
        return IntegerConst(
            value=p[0],
            builder=self.builder,
            module=self.module,
            symbol_table=self.symbol_table, lineno=self.get_lineno(p))

    @_('TRUE', 'FALSE')
    def rvalue(self, p):
        return BoolConst(
            value=p[0],
            builder=self.builder,
            module=self.module,
            symbol_table=self.symbol_table,
            lineno=self.get_lineno(p))

    @_('REAL_CONS')
    def rvalue(self, p):
        return RealConst(
            value=p[0],
            builder=self.builder,
            module=self.module,
            symbol_table=self.symbol_table,
            lineno=self.get_lineno(p))

    @_('CHARACTER')
    def rvalue(self, p):
        return CharConst(value=p[0][1:-1],
                         builder=self.builder,
                         module=self.module,
                         symbol_table=self.symbol_table,
                         lineno=self.get_lineno(p))

    @_('LPAREN rvalue RPAREN')
    def rvalue(self, p):
        return p.rvalue

    @_('ADDRESSOF expr')
    def rvalue(self, p):
        # TODO address of must impose lvalue!!!
        return AddressOf(
            lvalue=p[1],
            builder=self.builder,
            module=self.module,
            symbol_table=self.symbol_table,
            lineno=self.get_lineno(p))

    @_('NIL')
    def rvalue(self, p):
        return self.the_nil

    # UNARY OPERATORS
    @_('unop expr %prec UN_OP')
    def rvalue(self, p):
        if p.unop in self.arithmetic:
            return ArUnOp(
                op=p.unop,
                rhs=p.expr,
                builder=self.builder,
                module=self.module,
                symbol_table=self.symbol_table, lineno=self.get_lineno(p))
        else:
            return LogicUnOp(
                op=p.unop,
                rhs=p.expr,
                builder=self.builder,
                module=self.module,
                symbol_table=self.symbol_table, lineno=self.get_lineno(p))

    @_('expr PLUS expr',
       'expr MINUS expr',
       'expr TIMES expr',
       'expr FRAC expr',
       'expr DIV expr',
       'expr MOD expr',
       'expr GTE expr',
       'expr LTE expr',
       'expr GT expr',
       'expr LT expr',
       'expr AND expr',
       'expr OR expr',
       'expr EQUAL expr',
       'expr NEG expr',
       )
    def rvalue(self, p):
        if p[1] in self.arithmetic:
            return ArOp(
                op=p[1],
                lhs=p[0],
                rhs=p[-1],
                builder=self.builder,
                module=self.module,
                symbol_table=self.symbol_table, lineno=self.get_lineno(p))

        if p[1] in self.logical:
            return LogicOp(
                op=p[1],
                lhs=p[0],
                rhs=p[-1],
                builder=self.builder,
                module=self.module,
                symbol_table=self.symbol_table, lineno=self.get_lineno(p))

        if p[1] in self.comp:
            return CompOp(
                op=p[1],
                lhs=p[0],
                rhs=p[-1],
                builder=self.builder,
                module=self.module,
                symbol_table=self.symbol_table, lineno=self.get_lineno(p))

        raise ValueError('BinOp not parsed correctly.')

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
            symbol_table=self.symbol_table, lineno=self.get_lineno(p))

    @_('NAME LPAREN RPAREN')
    def call(self, p):
        return Call(
            id_=p.NAME,
            exprs=deque([]),
            builder=self.builder,
            module=self.module,
            symbol_table=self.symbol_table, lineno=self.get_lineno(p))

    @_('call')
    def expr(self, p):
        return p.call

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
    lexer = PCLLexer()
    parser = PCLParser()

    s = '''
        program toy;

        var number, limit: integer;

        begin
            limit := 100;
            number := 0;
            while number < limit do
            begin
                number := number + 1;

            end;

        end.

    '''

    tokens = list(lexer.tokenize(s))
    print([x.value for x in tokens])

    # tokens = lexer.tokenize(s)
    program = parser.parse(iter(tokens))
    program.sem()
    program.codegen()
    program.pprint()
    program.print_module()

    parser.codegen.postprocess_module()
    parser.codegen.generate_outputs('toy')

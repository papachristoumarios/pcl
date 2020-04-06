from abc import ABC
from collections import deque
import json

class AST(ABC):
    '''
        The Abstract Base Class for the AST Node
    '''

    def __init__(self, builder, module, symbol_table):
        '''
            AST Initializer
            Args:
                builder: LLVM IR builder module
                module: LLVM module
        '''
        self.builder = builder
        self.module = module
        self.symbol_table = symbol_table

    def eval(self):
        pass

    def sem(self):
        pass

    def type_check(self):
        pass

    def codegen(self):
        pass

    def pprint(self, indent=0):
        print(indent * ' ', end='')
        print(type(self))
        d = vars(self)
        for k, v in d.items():
            print(indent * ' ', end='')
            if k not in ['module', 'builder', 'symbol_table']:
                if isinstance(v, AST):
                    v.pprint(indent + 1)
                elif isinstance(v, deque):
                    for x in v:
                        x.pprint(indent + 1)
                else:
                    print('{} : {}'.format(k, v))



class Program(AST):
    def __init__(self, id_, body, builder, module, symbol_table):
        super(Program, self).__init__(builder, module, symbol_table)
        self.id_ = id_
        self.body = body


class Body(AST):

    def __init__(self, locals_, block, builder, module, symbol_table):
        super(Body, self).__init__(builder, module, symbol_table)
        self.locals = locals_
        self.block = block


class Local(AST):
    def __init__(self, builder, module, symbol_table):
        super(Local, self).__init__(builder, module, symbol_table)


class LocalHeader(Local):
    def __init__(self, header, body, builder, module, symbol_table):
        super(LocalHeader, self).__init__(builder, module, symbol_table)
        self.header = header
        self.body = body


class Var(Local):
    def __init__(self, ids, type_, builder, module, symbol_table):
        super(Var, self).__init__(builder, module, symbol_table)
        self.ids = ids
        self.type_ = type_


class VarList(Local):

    def __init__(self, vars_, builder, module, symbol_table):
        super(VarList, self).__init__(builder, module, symbol_table)
        self.vars_ = vars_


class Label(Local):

    def __init__(self, ids, builder, module, symbol_table):
        super(Label, self).__init__(builder, module, symbol_table)
        self.ids = ids

class Forward(Local):

    def __init__(self, header, builder, module, symbol_table):
        super(Forward, self).__init__(builder, module, symbol_table)
        self.header = header


class Header(AST):

    def __init__(
            self,
            header_type,
            id_,
            formals,
            func_type,
            builder,
            module,
            symbol_table):
        super(Header, self).__init__(builder, module, symbol_table)
        self.header_type = header_type
        self.id_ = id_
        self.formals = formals
        self.func_type = func_type


class Formal(AST):

    def __init__(self, ids, type_, builder, module, symbol_table):
        super(Formal, AST).__init__(builder, module, symbol_table)
        self.ids = ids
        self.type_ = type_


class Type(AST):

    def __init__(self, type_, builder, module, symbol_table):
        super(Type, self).__init__(builder, module, symbol_table)
        self.type_ = type_


class PointerType(Type):
    '''
        Declaration of a new pointer.
        Example: ^integer
    '''
    def __init__(self, type_, builder, module, symbol_table):
        super(PointerType, self).__init__(type_, builder, module, symbol_table)


class ArrayType(Type):

    def __init__(self, length, type_, builder, module, symbol_table):
        super(ArrayType, self).__init__(type_, builder, module, symbol_table)
        self.length = int(length)


class Statement(AST):
    def __init__(self, builder, module, symbol_table, **kwargs):
        super(Statement, self).__init__(builder, module, symbol_table)
        self.name = kwargs.get('name', None)


class Block(Statement):

    def __init__(self, stmt_list, builder, module, symbol_table):
        super(Block, self).__init__(builder, module, symbol_table)
        self.stmt_list = stmt_list


class Call(AST):

    def __init__(self, id_, exprs, builder, module, symbol_table):
        super(Call, self).__init__(builder, module, symbol_table)
        self.id_ = id_
        self.exprs = exprs


class If(Statement):

    def __init__(self, expr, stmt, else_stmt, builder, module, symbol_table):
        super(If, self).__init__(builder, module, symbol_table)
        self.expr = expr
        self.stmt = stmt
        self.else_stmt = else_stmt


class While(Statement):

    def __init__(self, expr, stmt, builder, module, symbol_table):
        super(While, self).__init__(builder, module, symbol_table)
        self.expr = expr
        self.stmt = stmt


class Goto(Statement):

    def __init__(self, id_, builder, module, symbol_table):
        super(Goto, self).__init__(builder, module, symbol_table)
        self.id_ = id_


class Return(Statement):
    pass

class Empty(Statement):
    pass

class New(Statement):

    def __init__(self, expr, lvalue, builder, module, symbol_table):
        super(New, self).__init__(builder, module, symbol_table)
        self.expr = expr
        self.lvalue = lvalue


class Dispose(Statement):

    def __init__(self, lvalue, builder, module, symbol_table):
        super(Dispose, self).__init__(builder, module, symbol_table)
        self.lvalue = lvalue


class Expr(AST):
    pass

class RValue(Expr):

    def __init__(self, builder, module, symbol_table):
        super(RValue, self).__init__(builder, module, symbol_table)


class IntegerConst(RValue):

    def __init__(self, value, builder, module, symbol_table):
        super(IntegerConst, self).__init__(builder, module, symbol_table)
        self.value = int(value)


class RealConst(RValue):

    def __init__(self, value, builder, module, symbol_table):
        super(RealConst, self).__init__(builder, module, symbol_table)
        self.value = float(value)


class CharConst(RValue):

    def __init__(self, value, builder, module, symbol_table):
        super(CharConst, self).__init__(builder, module, symbol_table)
        assert(len(value) == 1)
        self.value = value


class BoolConst(RValue):

    def __init__(self, value, builder, module, symbol_table):
        super(BoolConst, self).__init__(builder, module, symbol_table)
        assert(value in [True, False])
        self.value = value


class Ref(RValue):

    def __init__(self, lvalue, builder, module, symbol_table):
        super(Ref, self).__init__(builder, module, symbol_table)
        self.lvalue = lvalue


class Nil(RValue):

    def __init__(self, builder, module, symbol_table):
        super(Nil, self).__init__(builder, module, symbol_table)
        self.value = None


class UnOp(RValue):

    def __init__(self, op, rhs, builder, module, symbol_table):
        super(UnOp, self).__init__(builder, module, symbol_table)
        self.op = op
        self.rhs = rhs

class BinOp(RValue):

    def __init__(self, op, lhs, rhs, builder, module, symbol_table):
        super(UnOp, self).__init__(builder, module, symbol_table)
        self.op = op
        self.lhs = lhs
        self.rhs = rhs

class AddressOf(RValue):
    '''
        Declaration of address of an l-value
        with r-value = @l-value
    '''

    def __init__(self, lvalue, builder, module, symbol_table):
        super(AddressOf, self).__init__(builder, module, symbol_table)
        self.lvalue = lvalue

class LValue(Expr):
    def __init__(self, builder, module, symbol_table):
        super(LValue, self).__init__(builder, module, symbol_table)


class NameLValue(LValue):
    def __init__(self, id_, builder, module, symbol_table):
        super(NameLValue, self).__init__(builder, module, symbol_table)
        self.id_ = id_


class Result(LValue):
    def __init__(self, builder, module, symbol_table):
        super(Result, self).__init__(builder, module, symbol_table)

class StringLiteral(LValue):
    def __init__(self, literal, builder, module, symbol_table):
        super(StringLiteral, self).__init__(builder, module, symbol_table)
        self.literal = literal


class Deref(LValue):
    '''
        Declaration of dereference of a pointer
        If e = t^ then ^e = t
    '''

    def __init__(self, expr, builder, module, symbol_table):
        super(Deref, self).__init__(builder, module, symbol_table)
        self.expr = expr


class SetExpression(LValue):
    def __init__(self, lvalue, expr, builder, module, symbol_table):
        super(SetExpression, self).__init__(builder, module, symbol_table)
        self.lvalue = lvalue
        self.expr = expr


class LBrack(LValue):
    def __init__(self, lvalue, expr, builder, module, symbol_table):
        super(LBrack, self).__init__(builder, module, symbol_table)
        self.lvalue = lvalue
        self.expr = expr

import json
from abc import ABC, abstractmethod
from collections import deque
from error import PCLParserError, PCLSemError, PCLCodegenError


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
                symbol_table: The symbol table
        '''
        self.builder = builder
        self.module = module
        self.symbol_table = symbol_table
        self.stype = None

    # TODO add @abstractmethod
    def eval(self):
        pass

    def sem(self):
        pass

    def type_check(self, target):
        '''
            Checks if the inferred type of the node equals the
            desired type target
            Args:
                type: The desired type
        '''
        if self.stype == target:
            return True
        else:
            msg = '{}: Expected type {}, got type {}'.format(
                self.__class__.__name__, target, self.stype)
            raise PCLSemError(msg)

    def codegen(self):
        pass

    def pprint(self, indent=0):
        '''
            Pretty printing of a node's contents and
            its sucessors. Call it with root.pprint()
        '''
        print(indent * ' ', end='')
        print(type(self))
        d = vars(self)
        for k, v in d.items():

            if k not in ['module', 'builder', 'symbol_table']:
                if isinstance(v, AST):
                    print((indent - 1) * ' ', end='')
                    v.pprint(indent + 1)
                elif isinstance(v, deque):
                    for x in v:
                        print((indent - 1) * ' ', end='')
                        if isinstance(x, AST):
                            x.pprint(indent + 1)
                        else:
                            print((indent + 1) * ' ' + x)
                else:
                    print((indent + 2) * ' ', end='')
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
        super(Formal, self).__init__(builder, module, symbol_table)
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

    def sem(self):
        if self.name:
            self.symbol_table.insert


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
    '''
        If statement.
    '''

    def __init__(self, expr, stmt, else_stmt, builder, module, symbol_table):
        super(If, self).__init__(builder, module, symbol_table)
        self.expr = expr
        self.stmt = stmt
        self.else_stmt = else_stmt

    def sem(self):
        self.expr.sem()
        self.expr.type_check((CompositeType.T_NO_COMP, BaseType.T_BOOL))

        self.stmt.sem()
        if self.else_stmt:
            self.else_stmt.sem()


class While(Statement):
    '''
        While statement.
    '''

    def __init__(self, expr, stmt, builder, module, symbol_table):
        super(While, self).__init__(builder, module, symbol_table)
        self.expr = expr
        self.stmt = stmt

    def sem(self):
        self.expr.sem()
        self.expr.type_check((CompositeType.T_NO_COMP, BaseType.T_BOOL))

        self.stmt.sem()


class Goto(Statement):
    '''
        Goto statement.
    '''

    def __init__(self, id_, builder, module, symbol_table):
        super(Goto, self).__init__(builder, module, symbol_table)
        self.id_ = id_

    def sem(self):
        self.symbol_table.lookup(self.id_, last_scope=True)


class Return(Statement):
    '''
        Return statement.
    '''
    def sem(self):
        pass


class Empty(Statement):
    '''
        Empty Statement.
    '''
    def sem(self):
        pass


class New(Statement):
    '''
        New Statement.
    '''

    def __init__(self, expr, lvalue, builder, module, symbol_table):
        super(New, self).__init__(builder, module, symbol_table)
        self.expr = expr
        self.lvalue = lvalue



class Dispose(Statement):
    '''
        Dispose statement.
    '''

    def __init__(self, lvalue, builder, module, symbol_table):
        super(Dispose, self).__init__(builder, module, symbol_table)
        self.lvalue = lvalue


class Expr(AST):
    '''
        Base class for expressions.
    '''
    pass


class RValue(Expr):
    '''
        Base class for the RValue.
    '''

    def __init__(self, builder, module, symbol_table):
        super(RValue, self).__init__(builder, module, symbol_table)


class IntegerConst(RValue):
    '''
        Integer constant. Holds integer numbers.
    '''

    def __init__(self, value, builder, module, symbol_table):
        super(IntegerConst, self).__init__(builder, module, symbol_table)
        self.value = int(value)


class RealConst(RValue):
    '''
        Real constant. Holds floating point numbers.
    '''

    def __init__(self, value, builder, module, symbol_table):
        super(RealConst, self).__init__(builder, module, symbol_table)
        self.value = float(value)


class CharConst(RValue):
    '''
        Character constant. Contains exactly one literal.
    '''

    def __init__(self, value, builder, module, symbol_table):
        super(CharConst, self).__init__(builder, module, symbol_table)
        assert(len(value) == 1)
        self.value = value


class BoolConst(RValue):
    '''
        Boolean constant. Can be true or false.
    '''

    def __init__(self, value, builder, module, symbol_table):
        super(BoolConst, self).__init__(builder, module, symbol_table)
        self.value = value


class Ref(RValue):
    '''
        Declares a pointer to an LValue. That is if
        t is integer then ^t is a pointer to an integer
    '''

    def __init__(self, lvalue, builder, module, symbol_table):
        super(Ref, self).__init__(builder, module, symbol_table)
        self.lvalue = lvalue


class Nil(RValue):
    '''
        The null pointer. Must be declared as a singleton.
    '''

    def __init__(self, builder, module, symbol_table):
        super(Nil, self).__init__(builder, module, symbol_table)
        self.value = None


class UnOp(RValue):
    '''
        Unary operator. +x, -x and not x
    '''

    def __init__(self, op, rhs, builder, module, symbol_table):
        super(UnOp, self).__init__(builder, module, symbol_table)
        self.op = op
        self.rhs = rhs


class BinOp(RValue):
    '''
        Binary operation between two sides (lhs, rhs)
        Can be
            1. Arithmetic
            2. Logical
            3. Comparison
    '''

    def __init__(self, op, lhs, rhs, builder, module, symbol_table):
        super(BinOp, self).__init__(builder, module, symbol_table)
        self.op = op
        self.lhs = lhs
        self.rhs = rhs


class AddressOf(RValue):
    '''
        Declaration of address of an l-value
        with r-value = @l-value
    '''

    def __init__(self, lvalue, builder, module, symbol_table):
        if isinstance(lvalue, RValue):
            raise PCLParserError('Tried to access the address of an RValue')
        super(AddressOf, self).__init__(builder, module, symbol_table)
        self.lvalue = lvalue


class LValue(Expr):
    '''
        Base class for the LValue
    '''

    def __init__(self, builder, module, symbol_table):
        super(LValue, self).__init__(builder, module, symbol_table)


class NameLValue(LValue):
    '''
        Named LValue
    '''

    def __init__(self, id_, builder, module, symbol_table):
        super(NameLValue, self).__init__(builder, module, symbol_table)
        self.id_ = id_


class Result(LValue):
    '''
        Holds the result of a function
    '''

    def __init__(self, builder, module, symbol_table):
        super(Result, self).__init__(builder, module, symbol_table)


class StringLiteral(LValue):
    '''
        Holds a node for a string literal
    '''

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
    '''
        Assignment of an expression to a name
    '''
    def __init__(self, lvalue, expr, builder, module, symbol_table):
        super(SetExpression, self).__init__(builder, module, symbol_table)
        self.lvalue = lvalue
        self.expr = expr


class LBrack(LValue):
    def __init__(self, lvalue, expr, builder, module, symbol_table):
        super(LBrack, self).__init__(builder, module, symbol_table)
        self.lvalue = lvalue
        self.expr = expr

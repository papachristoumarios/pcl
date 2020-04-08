import json
from abc import ABC, abstractmethod
from collections import deque
from error import PCLParserError, PCLSemError, PCLCodegenError
from symbol_table import *

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
        raise NotImplementedError('sem method not implemented for this node')


    def type_check(self, target):
        '''
            Checks if the inferred type of the node equals the
            desired type target. target can be a type or a list of types.
            Args:
                type: type or list of types.
        '''
        assert self.stype is not None, 'Type check error, type not set.'
        if isinstance(target, list) and self.stype in target:
            return True

        if self.stype == target:
            return True

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

    def sem(self):
        # Open program scope
        self.symbol_table.open_scope()

        # Run sem on body
        self.body.sem()

        # Close main scope
        self.symbol_table.close_scope()


class Body(AST):

    def __init__(self, locals_, block, builder, module, symbol_table):
        super(Body, self).__init__(builder, module, symbol_table)
        self.locals = locals_
        self.block = block

    def sem(self):
        # Run semantic to locals
        for local in self.locals_:
            local.sem()

        # Run sem to block
        self.block.sem()

class Local(AST):
    def __init__(self, builder, module, symbol_table):
        super(Local, self).__init__(builder, module, symbol_table)

class LocalHeader(Local):
    def __init__(self, header, body, builder, module, symbol_table):
        super(LocalHeader, self).__init__(builder, module, symbol_table)
        self.header = header
        self.body = body

    def sem(self):
        # Register function or procedure
        header_entry_type = (ComposerType.T_NO_COMP, BaseType(self.header.header_type))
        header_entry = SymbolEntry(stype=self.header.type_.stype, name_type=header_entry_type)
        self.symbol_table.insert(self.id_, header_entry)

        # Open function scope
        self.symbol_table.open_scope()

        # Register header locals
        self.header.sem()

        # Sem the body
        self.body.sem()

        # Close function scope
        self.symbol_table.close_scope()


class VarList(Local):

    def __init__(self, vars_, builder, module, symbol_table):
        super(VarList, self).__init__(builder, module, symbol_table)
        self.vars_ = vars_

    def sem(self):
        for var in self.vars_:
            var.sem()

class Var(Local):
    def __init__(self, ids, type_, builder, module, symbol_table):
        super(Var, self).__init__(builder, module, symbol_table)
        self.ids = ids
        self.type_ = type_

    def sem(self):
        # Iterate over all names and register variables
        for id_ in self.ids:
            var_entry = SymbolEntry(stype=self.type_.stype, name_type=NameType.N_VAR)
            self.symbol_table.insert(id_, var_entry)

class Label(Local):

    def __init__(self, ids, builder, module, symbol_table):
        super(Label, self).__init__(builder, module, symbol_table)
        self.ids = ids

    def sem(self):
        # Iterate over all names and register variables
        for id_ in self.ids:
            label_entry = SymbolEntry(stype=self.type_.stype, name_type=NameType.N_LABEL)
            self.symbol_table.insert(id_, label_entry)


class Forward(Local):

    def __init__(self, header, builder, module, symbol_table):
        super(Forward, self).__init__(builder, module, symbol_table)
        self.header = header

    def sem(self):
        forward_entry = SymbolEntry(stype=self.header.type_.stype, name_type=NameType.N_FORWARD)
        self.symbol_table.insert('forward_' + self.header.id_, forward_entry)


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

    def sem(self):
        if self.func_type:
            result_entry = SymbolEntry(stype=self.func_type.stype, name_type=NameType.N_VAR)
            self.symbol_table.insert('result', result_entry)

        for formal in self.formals:
            for formal_id in formal.ids:
                formal_entry = SymbolEntry(stype=formal.stype, name_type=NameType.N_FORMAL)
                self.symbol_table.insert_formal(self.id_, formal_id, formal_entry)

class Formal(AST):

    def __init__(self, ids, type_, builder, module, symbol_table):
        super(Formal, self).__init__(builder, module, symbol_table)
        self.ids = ids
        self.type_ = type_

    def sem(self):
        self.stype = self.type_.stype


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
        self.type_ = type_

    def sem(self):
        base_type = self.type_.stype
        self.stype = (ComposerType.T_PTR, base_type)


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
    '''
        If statement.
    '''

    def __init__(self, expr, stmt, else_stmt, builder, module, symbol_table):
        super(If, self).__init__(builder, module, symbol_table)
        self.expr = expr
        self.stmt = stmt
        self.else_stmt = else_stmt


class While(Statement):
    '''
        While statement.
    '''

    def __init__(self, expr, stmt, builder, module, symbol_table):
        super(While, self).__init__(builder, module, symbol_table)
        self.expr = expr
        self.stmt = stmt


class Goto(Statement):
    '''
        Goto statement.
    '''

    def __init__(self, id_, builder, module, symbol_table):
        super(Goto, self).__init__(builder, module, symbol_table)
        self.id_ = id_


class Return(Statement):
    '''
        Return statement.
    '''


class Empty(Statement):
    '''
        Empty Statement.
    '''
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

    def sem(self):
        self.stype = (ComposerType.T_NO_COMP, BaseType.T_INT)


class RealConst(RValue):
    '''
        Real constant. Holds floating point numbers.
    '''

    def __init__(self, value, builder, module, symbol_table):
        super(RealConst, self).__init__(builder, module, symbol_table)
        self.value = float(value)

    def sem(self):
        self.stype = (ComposerType.T_NO_COMP, BaseType.T_REAL)


class CharConst(RValue):
    '''
        Character constant. Contains exactly one literal.
    '''

    def __init__(self, value, builder, module, symbol_table):
        super(CharConst, self).__init__(builder, module, symbol_table)
        assert(len(value) == 1)
        self.value = value

    def sem(self):
        self.stype = (ComposerType.T_NO_COMP, BaseType.T_CHAR)


class BoolConst(RValue):
    '''
        Boolean constant. Can be true or false.
    '''

    def __init__(self, value, builder, module, symbol_table):
        super(BoolConst, self).__init__(builder, module, symbol_table)
        self.value = value

    def sem(self):
        self.stype = (CompositeType.T_NO_COMP, BaseType.T_BOOL)


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

    def sem(self):
        self.stype = (CompositeType.T_NO_COMP, BaseType.T_NIL)


class UnOp(RValue):
    '''
        Unary operator. +x, -x and not x
    '''

    def __init__(self, op, rhs, builder, module, symbol_table):
        super(UnOp, self).__init__(builder, module, symbol_table)
        self.op = op
        self.rhs = rhs


class ArOp(RValue):
    '''
        Arithmetic operation between two sides (lhs, rhs)
    '''

    def __init__(self, op, lhs, rhs, builder, module, symbol_table):
        super(ArOp, self).__init__(builder, module, symbol_table)
        self.op = op
        self.lhs = lhs
        self.rhs = rhs
        self.arithmetic_types = [(ComposerType.T_NO_COMP, BasicType.T_INT),
                                 (ComposerType.T_NO_COMP, BasicType.T_REAL)]

    def sem(self):
        self.lhs.sem()
        self.rhs.sem()

        type_check(self.lhs.stype, self.arithmetic_types)
        type_check(self.rhs.stype, self.arithmetic_types)

        real_type = (ComposerType.T_NO_COMP, BasicType.T_REAL)
        int_type = (ComposerType.T_NO_COMP, BasicType.T_INT)

        if self.op == '/':
            self.stype = real_type
            return

        if self.op == 'div' or self.op == 'mod':
            type_check(self.lhs.stype, int_type)
            type_check(self.rhs.stype, int_type)

        if self.lhs.stype == real_type or self.rhs.stype == real_type:
            self.stype = real_type
            return

        self.stype = int_type


class CompOp(RValue):
    '''
        Comparison operation between two sides (lhs, rhs)
    '''

    def __init__(self, op, lhs, rhs, builder, module, symbol_table):
        super(CompOp, self).__init__(builder, module, symbol_table)
        self.op = op
        self.lhs = lhs
        self.rhs = rhs
        self.arithmetic_types = [(ComposerType.T_NO_COMP, BasicType.T_INT),
                                 (ComposerType.T_NO_COMP, BasicType.T_REAL)]

    def sem(self):
        self.lhs.sem()
        self.rhs.sem()

        if self.op == '=' or self.op == '<>':
            arithmetic = (self.lhs.stype in self.arithmetic_types) and (self.rhs.stype in self.arithmetic_types)
            if not_arithmetic:
                assert self.lhs.stype == self.rhs.stype, 'Comparison is only allowed between operands of same type'
                assert self.lhs.stype[0] != ComposerType.T_CONST_ARRAY and self.lhs.stype[0] != ComposerType.T_VAR_ARRAY, 'Arrays cannot be compared.'
        else:
            type_check(self.lhs.stype, self.arithmetic_types)
            type_check(self.rhs.stype, self.arithmetic_types)

        self.stype = (ComposerType.T_NO_COMP, BasicType.T_BOOL)


class LogicOp(RValue):
    '''
        Logic operation between two sides (lhs, rhs)
    '''

    def __init__(self, op, lhs, rhs, builder, module, symbol_table):
        super(LogicOp, self).__init__(builder, module, symbol_table)
        self.op = op
        self.lhs = lhs
        self.rhs = rhs

    def sem(self):
        self.lhs.sem()
        self.rhs.sem()
        bool_type = (ComposerType.T_NO_COMP, BasicType.T_BOOL)

        type_check(self.lhs.stype, bool_type)
        type_check(self.rhs.stype, bool_type)

        self.stype = bool_type



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

    def sem(self):
        self.lvalue.sem()
        self.stype = (ComposerType.T_PTR, self.lvalue.stype)


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

    def sem(self):
        result = self.symbol_table.lookup(self.id_)
        self.stype = result.stype


class Result(LValue):
    '''
        Holds the result of a function
    '''

    def __init__(self, builder, module, symbol_table):
        super(Result, self).__init__(builder, module, symbol_table)

    def sem(self):
        result = self.symbol_table.lookup('result')
        self.stype = result.stype


class StringLiteral(LValue):
    '''
        Holds a node for a string literal
    '''

    def __init__(self, literal, builder, module, symbol_table):
        super(StringLiteral, self).__init__(builder, module, symbol_table)
        self.literal = literal

    def sem(self):
        self.stype = (ComposerType.T_CONST_ARRAY, BaseType.T_CHAR)


class Deref(LValue):
    '''
        Declaration of dereference of a pointer
        If e = t^ then ^e = t
    '''

    def __init__(self, expr, builder, module, symbol_table):
        if isinstance(expr, Nil):
            raise PCLSemError('Cannot dereference nil')

        super(Deref, self).__init__(builder, module, symbol_table)
        self.expr = expr

    def sem(self):
        self.expr.sem()
        if self.expr.stype[0] != ComposerType.T_PTR:
            raise PCLSemError('Dereferencing non-pointer expression')

        self.stype = self.expr.stype[1]



class SetExpression(LValue):
    '''
        Assignment of an expression to a name
    '''
    def __init__(self, lvalue, expr, builder, module, symbol_table):
        super(SetExpression, self).__init__(builder, module, symbol_table)
        self.lvalue = lvalue
        self.expr = expr

    def sem(self):
        self.expr.sem()
        self.stype = self.expr.stype


class LBrack(LValue):
    def __init__(self, lvalue, expr, builder, module, symbol_table):
        super(LBrack, self).__init__(builder, module, symbol_table)
        self.lvalue = lvalue
        self.expr = expr

    def sem(self):
        self.expr.sem()
        self.expr.type_check((CompositeType.T_NO_COMP, BaseType.T_INT))
        self.lvalue.sem()
        self.stype = self.lvalue.stype[1]

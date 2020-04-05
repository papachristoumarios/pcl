from abc import ABC

class AST(ABC):
    '''
        The Abstract Base Class for the AST Node
    '''

    def __init__(self, builder, module):
        '''
            AST Initializer
            Args:
                builder: LLVM IR builder module
                module: LLVM module
        '''
        self.builder = builder
        self.module = module

    def eval(self):
        pass

    def sem(self):
        pass

    def type_check(self):
        pass

    def codegen(self):
        pass

class Program(AST):

    def __init__(self, id_, body, builder, module):
        super(Program, self).__init__(builder, module)
        self.id_ = id
        self.body = body

class Body(AST):

    def __init__(self, locals_, block, builder, module):
        super(Body, self).__init__(builder, module)
        self.locals = locals_
        self.block = block

class Local(AST):

    def __init__(self, builder, module):
        super(Local, self).__init__(builder, module)

class Var(Local):

    def __init__(self, ids, type_, builder, module):
        super(Var, self).__init__(builder, module)
        self.ids = ids
        self.type_ = type_

class VarList(Local):

    def __init__(self, vars_, builder, module):
        super(VarList, self).__init__(builder, module)
        self.vars_ = vars_

class Label(Local):

    def __init__(self, ids, header, body, builder, module):
        super(Label, self).__init__(builder, module)
        self.ids = ids
        self.header = header
        self.body = body

class Forward(Local):

    def __init__(self, header, builder, module):
        super(Forward, self).__init__(builder, module)
        self.header = header

class Header(AST):

    def __init__(self, header_type, id_, formals, builder, module, func_type=None):
        super(Header, self).__init__(builder, module)
        self.header_type = header_type
        self.id_ = id_
        self.formals = formals
        self.func_type = func_type

class Formal(AST):

    def __init__(self, ids, type_, builder, module):
        super(Formal, AST).__init__(builder, module)
        self.ids = ids
        self.type_ = type_

class Type(AST):
    T_INTEGER = 'int'
    T_REAL = 'real'
    T_BOOL = 'bool'
    T_CHAR = 'char'

    def __init__(self, type_, builder, module):
        super(Type, self).__init__(builder, module)
        assert(type_ in [T_INTEGER, T_REAL, T_BOOL, T_CHAR])
        self.type_ = type_

class DerefType(Type):

    def __init__(self, type_, builder, module):
        super(DerefType, self).__init__(type_, builder, module)

class ArrayType(Type):

    def __init__(self, length, type_, builder, module):
        super(ArrayType, self).__init__(type_, builder, module)
        self.length = int(length)

class Statement(AST):

    def __init__(self, name, builder, module, **kwargs):
        super(Statement, self).__init__(builder, module)
        self.name = kwargs.get('name', None)

class Block(Statement):

    def __init__(self, stmt_list, builder, module):
        super(Block, self).__init__(builder, module)
        self.stmt_list = stmt_list

class LValue(Statement):

    def __init__(self, l_value, expr, builder, module):
        super(LValue, self).__init__(builder, module)
        self.l_value = l_value
        self.expr = expr

class Call(AST):

    def __init__(self, id_, exprs, builder, module):
        super(Call, self).__init__(builder, module)
        self.id_ = id_
        self.exprs = exprs

class If(Statement):

    def __init__(self, expr, stmt, else_stmt, builder, module):
        super(If, self).__init__(builder, module)
        self.expr = expr
        self.stmt = stmt
        self.else_stmt = else_stmt

class While(Statement):

    def __init__(self, expr, stmt, builder, module):
        super(While, self).__init__(builder, module)
        self.expr = expr
        self.stmt = stmt

class Goto(Statement):

    def __init__(self, id_, builder, module):
        super(Goto, self).__init__(builder, module)
        self.id_ = id_

class Return(Statement):
    pass

class New(Statement):

    def __init__(self, expr, l_value, builder, module):
        super(New, self).__init__(builder, module)
        self.expr = expr
        self.l_value = l_value

class Dispose(Statement):

    def __init__(self, l_value, builder, module):
        super(Dispose, self).__init__(builder, module)
        self.l_value = l_value

class Expr(AST):
    pass

class RValue(Expr):

    def __init__(self, builder, module):
        super(RValue, self).__init__(builder, module)

class IntegerConst(RValue):

    def __init__(self, value, builder, module):
        super(IntegerConst, self).__init__(builder, module)
        self.value = int(value)

class RealConst(RValue):

    def __init__(self, value, builder, module):
        super(RealConst, self).__init__(builder, module)
        self.value = float(value)


class CharConst(RValue):

    def __init__(self, value, builder, module):
        super(CharConst, self).__init__(builder, module)
        assert(len(value) == 1)
        self.value = value

class BoolConst(RValue):

    def __init__(self, value, builder, module):
        super(BoolConst, self).__init__(builder, module)
        assert(value in [True, False])
        self.value = value

class RefConst(RValue):

    def __init__(self, l_value, builder, module):
        super(RefConst, self).__init__(builder, module)
        self.l_value = l_value

class Nil(RValue):

    def __init__(self, builder, module):
        super(RefConst, self).__init__(builder, module)
        self.value = None

class UnOp(RValue):

    def __init__(self, op, rhs, builder, module):
        super(UnOp, self).__init__(builder, module)
        self.op = op
        self.rhs = rhs

class BinOp(RValue):

    def __init__(self, op, lhs, rhs, builder, module):
        super(UnOp, self).__init__(builder, module)
        self.op = op
        self.rhs = rhs
        self.lhs = lhs

class LValue(Expr):

    def __init__(self, builder, module, **kwargs):
        super(LValue, self).__init__(builder, module)
        self.kwargs = kwargs

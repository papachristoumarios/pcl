from abc import ABC


class AST(ABC):
    '''
        The Abstract Base Class for the AST Node
    '''

    def __init__(self, builder=None, module=None, symbol_table=None):
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


class Program(AST):

    def __init__(self, id_, body, builder, module, symbol_table):
        super(Program, self).__init__(builder, module, symbol_table)
        self.id_ = id
        self.body = body


class Body(AST):

    def __init__(self, locals_, block, builder, module, symbol_table):
        super(Body, self).__init__(builder, module, symbol_table)
        self.locals = locals_
        self.block = block


class Local(AST):

    def __init__(self, builder, module, symbol_table):
        super(Local, self).__init__(builder, module, symbol_table)


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

    def __init__(self, ids, header, body, builder, module, symbol_table):
        super(Label, self).__init__(builder, module, symbol_table)
        self.ids = ids
        self.header = header
        self.body = body


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
            builder,
            module,
            symbol_table,
            func_type=None):
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


class DerefType(Type):

    def __init__(self, type_, builder, module, symbol_table):
        super(DerefType, self).__init__(type_, builder, module, symbol_table)


class ArrayType(Type):

    def __init__(self, length, type_, builder, module, symbol_table):
        super(ArrayType, self).__init__(type_, builder, module, symbol_table)
        self.length = int(length)


class Statement(AST):

    def __init__(self, name, builder, module, symbol_table, **kwargs):
        super(Statement, self).__init__(builder, module, symbol_table)
        self.name = kwargs.get('name', None)


class Block(Statement):

    def __init__(self, stmt_list, builder, module, symbol_table):
        super(Block, self).__init__(builder, module, symbol_table)
        self.stmt_list = stmt_list


class LValue(Statement):

    def __init__(self, l_value, expr, builder, module, symbol_table):
        super(LValue, self).__init__(builder, module, symbol_table)
        self.l_value = l_value
        self.expr = expr


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


class New(Statement):

    def __init__(self, expr, l_value, builder, module, symbol_table):
        super(New, self).__init__(builder, module, symbol_table)
        self.expr = expr
        self.l_value = l_value


class Dispose(Statement):

    def __init__(self, l_value, builder, module, symbol_table):
        super(Dispose, self).__init__(builder, module, symbol_table)
        self.l_value = l_value


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

    def __init__(self, l_value, builder, module, symbol_table):
        super(Ref, self).__init__(builder, module, symbol_table)
        self.l_value = l_value


class Nil(RValue):

    def __init__(self, builder, module, symbol_table):
        super(RefConst, self).__init__(builder, module, symbol_table)
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


class LValue(Expr):

    def __init__(self, builder, module, **kwargs):
        super(LValue, self).__init__(builder, module, symbol_table)
        self.kwargs = kwargs

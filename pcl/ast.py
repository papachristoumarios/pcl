import json
import sys
from abc import ABC, abstractmethod
from collections import deque
from llvmlite import ir, binding

from pcl.error import PCLParserError, PCLSemError, PCLCodegenError
from pcl.symbol_table import *
from pcl.codegen import *


class AST(ABC):
    '''
        The Abstract Base Class for the AST Node
    '''

    def __init__(self, builder, module, symbol_table, lineno=-1):
        '''
            AST Initializer
            Args:
                builder: LLVM IR builder module
                module: LLVM module
                symbol_table: The symbol table
        '''
        # LLVM Builder
        self.builder = builder

        # LLVM Module
        self.module = module

        # Reference to global symbol table
        self.symbol_table = symbol_table

        # Semantic type. If set, it is represented by (composer, stype_)
        self.stype = None

        # LLVM Value for codegen
        self.cvalue = None

        # Keep line number
        self.lineno = lineno

    def eval(self):
        pass

    def raise_exception_helper(self, msg, exception=PCLSemError):
        msg_new = '{} at line {}: {}'.format(self.__class__.__name__, self.lineno, msg)
        raise exception(msg_new)

    def sem(self):
        msg = 'sem method not implemented for {}'.format(
            self.__class__.__name__)
        raise NotImplementedError(msg)

    def _sem_decorator(sem_fn):
        def wrapper(self):
            if self.stype is None:
                sem_fn(self)
            return wrapper

    def codegen(self):
        msg = 'codegen method not implemented for {}'.format(
            self.__class__.__name__)
        raise NotImplementedError(msg)

    def _codegen_decorator(codegen_fn):
        def wrapper(self):
            if self.cvalue is None:
                codegen_fn(self)
            return wrapper

    def pipeline(self, *stages):
        for stage in stages:
            getattr(self, stage)()

    def type_check(self, target, *args):
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

        msg = '{}: Expected type {}, got type {}. {}'.format(
            self.__class__.__name__, target, self.stype, ' '.join(args))
        self.raise_exception_helper(msg, PCLSemError)

    def print_module(self):
        print(str(self.module))

    def pprint(self, indent=0):
        '''
            Pretty printing of a node's contents and
            its sucessors. Call it with root.pprint()
        '''
        sys.stdout.write('{}{}'.format(indent * ' ', type(self)))
        # print(indent * ' ', end='')
        # print(type(self))
        d = vars(self)
        for k, v in d.items():

            if k not in ['module', 'builder', 'symbol_table']:
                if isinstance(v, AST):
                    sys.stdout.write((indent - 1) * ' ')
                    v.pprint(indent + 1)
                elif isinstance(v, deque):
                    for x in v:
                        sys.stdout.write((indent - 1) * ' ')
                        if isinstance(x, AST):
                            x.pprint(indent + 1)
                        else:
                            sys.stdout.write((indent + 1) * ' ' + x + '\n')
                else:
                    sys.stdout.write((indent + 2) * ' ')
                    sys.stdout.write('{} : {}\n'.format(k, v))


class Program(AST):
    def __init__(self, id_, body, builder, module, symbol_table, lineno):
        super(Program, self).__init__(builder, module, symbol_table, lineno)
        self.id_ = id_
        self.body = body

    def sem(self):
        # Open program scope
        self.symbol_table.open_scope()

        # Run sem on body
        self.body.sem()

        # Close main scope
        self.symbol_table.close_scope()

    def codegen(self):
        # Open program scope
        self.symbol_table.open_scope()

        # Run codegen on body
        self.body.codegen()

        # Close scope
        self.symbol_table.close_scope()


class Body(AST):

    def __init__(self, locals_, block, builder, module, symbol_table, lineno):
        super(Body, self).__init__(builder, module, symbol_table, lineno)
        self.locals_ = locals_
        self.block = block

    def sem(self):
        # Run semantic to locals
        for local in self.locals_:
            local.sem()

        # Run sem to block
        self.block.sem()

    def codegen(self):
        # Run codegen to locals
        for local in self.locals_:
            local.codegen()

        self.block.codegen()


class Local(AST):
    def __init__(self, builder, module, symbol_table, lineno):
        super(Local, self).__init__(builder, module, symbol_table, lineno)


class LocalHeader(Local):
    def __init__(self, header, body, builder, module, symbol_table, lineno):
        super(LocalHeader, self).__init__(builder, module, symbol_table, lineno)
        self.header = header
        self.body = body

    def sem(self):
        # TODO add declaration mismatch with forward and localheader

        if self.header.func_type:
            # function
            self.header.func_type.sem()
            header_name_entry = SymbolEntry(
                stype=self.header.func_type.stype,
                name_type=NameType.N_FUNCTION)
        else:
            # procedure
            header_name_entry = SymbolEntry(
                stype=(
                    ComposerType.T_NO_COMP,
                    BaseType.T_PROC),
                name_type=NameType.N_PROCEDURE)

        self.symbol_table.insert(self.header.id_, header_name_entry)

        for formal in self.header.formals:
            formal.sem()
            for formal_id in formal.ids:
                formal_entry = SymbolEntry(
                    stype=formal.stype,
                    name_type=NameType.N_FORMAL,
                    by_reference=formal.by_reference)
                self.symbol_table.insert_formal(
                    self.header.id_, formal_id, formal_entry)

        # Open function scope
        self.symbol_table.open_scope(self.header.id_)

        # Register header locals
        self.header.sem()
        for formal in self.header.formals:
            formal.sem()
            for id_ in formal.ids:
                id_entry = SymbolEntry(
                    stype=formal.stype, name_type=NameType.N_VAR)
                self.symbol_table.insert(id_, id_entry)

        # Sem the body
        self.body.sem()

        # Close function scope
        self.symbol_table.close_scope()

    def codegen(self):

        # Infer function type (signature)
        if self.header.func_type:
            # function
            self.header.func_type.codegen()
            header_return_cvalue = self.header.func_type.cvalue
        else:
            header_return_cvalue = LLVMTypes.T_PROC

        formal_types_cvalues = []

        # Infer formal parameter types
        for formal in self.header.formals:
            formal.type_.codegen()
            for formal_id in formal.ids:
                if formal.by_reference:
                    formal_types_cvalues.append(
                        formal.type_.cvalue.as_pointer())
                else:
                    formal_types_cvalues.append(formal.type_.cvalue)

        header_type_cvalue = ir.FunctionType(
            header_return_cvalue, formal_types_cvalues, var_arg=False)

        try:
            header_entry = self.symbol_table.lookup('forward_' + self.header.id_)
            header_cvalue = header_entry.cvalue
        except PCLSymbolTableError:
            header_cvalue = ir.Function(
                self.module,
                header_type_cvalue,
                name=self.header.id_)

            if self.header.func_type:
                header_entry = SymbolEntry(
                    stype=self.header.func_type.stype,
                    name_type=NameType.N_FUNCTION,
                    cvalue=header_cvalue)
            else:
                header_entry = SymbolEntry(
                    stype=(
                        ComposerType.T_NO_COMP,
                        BaseType.T_PROC),
                    name_type=NameType.N_PROCEDURE,
                    cvalue=header_cvalue)

            self.symbol_table.insert(self.header.id_, header_entry)

        header_args = header_cvalue.args

        header_block = header_cvalue.append_basic_block(
            self.header.id_ + '_entry')

        with self.builder.goto_block(header_block):
            # Register args to symbol table as formals
            counter = 0
            for formal in self.header.formals:
                for formal_id in formal.ids:
                    arg = header_args[counter]
                    arg_formal_entry = SymbolEntry(
                        stype=formal.stype,
                        name_type=NameType.N_FORMAL,
                        cvalue=arg,
                        by_reference=formal.by_reference)
                    self.symbol_table.insert_formal(
                        self.header.id_, formal_id, arg_formal_entry)
                    counter += 1
                    # arg_ptr_cvalue = self.builder.alloca(formal_types_cvalues[counter])
                    # arg_entry_cvalue = self.builder.load(arg)
                    # arg_entry = SymbolEntry(stype=formal.stype, name_type=NameType.N_VAR, cvalue=arg_entry_cvalue)
                    # counter += 1
            self.symbol_table.open_scope(self.header.id_)

            self.header.codegen()


            counter = 0
            for formal in self.header.formals:
                for formal_id in formal.ids:
                    arg = header_args[counter]
                    if not formal.by_reference:
                        arg_cvalue = self.builder.alloca(arg.type)
                        self.builder.store(arg, arg_cvalue)
                    else:
                        arg_cvalue = arg
                    arg_entry = SymbolEntry(
                        stype=formal.stype,
                        name_type=NameType.N_VAR,
                        cvalue=arg_cvalue)
                    self.symbol_table.insert(formal_id, arg_entry)
                    counter += 1

            self.body.codegen()


            # Guardian return (return is not specified at the end of fcn/proc)
            # guardian_return_block = header_cvalue.append_basic_block(
                # self.header.id_ + '_return')

            # self.builder.position_at_start(guardian_return_block)

            try:
                # Function
                result_cvalue_ptr = self.symbol_table.lookup('result').cvalue
                result_cvalue = self.builder.load(result_cvalue_ptr)
                self.builder.ret(result_cvalue)
            except PCLSymbolTableError:
                # Procedure
                self.builder.ret_void()


            self.symbol_table.close_scope()


class VarList(Local):

    def __init__(self, vars_, builder, module, symbol_table, lineno):
        super(VarList, self).__init__(builder, module, symbol_table, lineno)
        self.vars_ = vars_

    def sem(self):
        for var in self.vars_:
            var.sem()

    def codegen(self):
        for var in self.vars_:
            var.codegen()


class Var(Local):
    def __init__(self, ids, type_, builder, module, symbol_table, lineno):
        super(Var, self).__init__(builder, module, symbol_table, lineno)
        self.ids = ids
        self.type_ = type_

    def sem(self):
        self.type_.sem()
        # Iterate over all names and register variables
        for id_ in self.ids:
            var_entry = SymbolEntry(
                stype=self.type_.stype,
                name_type=NameType.N_VAR)
            self.symbol_table.insert(id_, var_entry)

    def codegen(self):
        self.type_.codegen()
        for id_ in self.ids:
            # Local symbol
            # id_cvalue = self.builder.alloca(self.type_.cvalue)
            # var_entry = SymbolEntry(
            #     stype=self.type_.stype,
            #     name_type=NameType.N_VAR,
            #     cvalue=id_cvalue)
            # self.symbol_table.insert(id_, var_entry)

            # Global symbol

            # Name is needed for initialization
            # Should not be used by the programmer
            global_id_name = '{}_{}'.format(id_, len(self.symbol_table.scopes)-1)
            global_id_cvalue = ir.GlobalVariable(self.module, self.type_.cvalue, name=global_id_name)

            # Set initializer to zeroinitializer ir.Constant(typ, None)
            global_id_cvalue.initializer = ir.Constant(self.type_.cvalue, None)

            var_entry = SymbolEntry(
                stype=self.type_.stype,
                name_type=NameType.N_VAR,
                cvalue=global_id_cvalue)

            # Register global symbol to symbol table
            self.symbol_table.insert(id_, var_entry)

class Label(Local):
    def __init__(self, ids, builder, module, symbol_table, lineno):
        super(Label, self).__init__(builder, module, symbol_table, lineno)
        self.ids = ids

    def sem(self):
        # Iterate over all names and register variables
        for id_ in self.ids:
            label_entry = SymbolEntry(
                stype=(
                    ComposerType.T_NO_COMP,
                    BaseType.T_LABEL),
                name_type=NameType.N_LABEL)
            self.symbol_table.insert(id_, label_entry)

    def codegen(self):
        pass


class Forward(Local):

    def __init__(self, header, builder, module, symbol_table, lineno):
        super(Forward, self).__init__(builder, module, symbol_table, lineno)
        self.header = header

    def sem(self):
        if self.header.func_type:
            self.header.func_type.sem()
            header_type = self.header.func_type.stype
        else:
            header_type = (ComposerType.T_NO_COMP, BaseType.T_PROC)
        forward_entry = SymbolEntry(
            stype=header_type,
            name_type=NameType.N_FORWARD)
        self.symbol_table.insert('forward_' + self.header.id_, forward_entry)

        for formal in self.header.formals:
            formal.sem()
            for formal_id in formal.ids:
                formal_entry = SymbolEntry(
                    stype=formal.stype,
                    name_type=NameType.N_FORMAL,
                    by_reference=formal.by_reference)
                self.symbol_table.insert_formal(
                    'forward_' + self.header.id_, formal_id, formal_entry)

    def codegen(self):
        # Infer function type (signature)
        if self.header.func_type:
            # function
            self.header.func_type.codegen()
            header_return_cvalue = self.header.func_type.cvalue
        else:
            header_return_cvalue = LLVMTypes.T_PROC

        formal_types_cvalues = []

        # Infer formal parameter types
        for formal in self.header.formals:
            formal.type_.codegen()
            for formal_id in formal.ids:
                if formal.by_reference:
                    formal_types_cvalues.append(
                        formal.type_.cvalue.as_pointer())
                else:
                    formal_types_cvalues.append(formal.type_.cvalue)

        header_type_cvalue = ir.FunctionType(
            header_return_cvalue, formal_types_cvalues, var_arg=False)

        header_cvalue = ir.Function(
            self.module,
            header_type_cvalue,
            name=self.header.id_)

        if self.header.func_type:
            header_entry = SymbolEntry(
                stype=self.header.func_type.stype,
                name_type=NameType.N_FUNCTION,
                cvalue=header_cvalue)
        else:
            header_entry = SymbolEntry(
                stype=(
                    ComposerType.T_NO_COMP,
                    BaseType.T_PROC),
                name_type=NameType.N_PROCEDURE,
                cvalue=header_cvalue)

        self.symbol_table.insert('forward_' + self.header.id_, header_entry)



class Header(AST):
    def __init__(
            self,
            header_type,
            id_,
            formals,
            func_type,
            builder,
            module,
            symbol_table,
            lineno):
        '''
            header_type: [function, procedure]
            formals: function / procedure inputs
            func_type: return type
        '''
        super(Header, self).__init__(builder, module, symbol_table, lineno)
        self.header_type = header_type
        self.id_ = id_
        self.formals = formals
        self.func_type = func_type

    def sem(self):
        if self.func_type:
            result_entry = SymbolEntry(
                stype=self.func_type.stype,
                name_type=NameType.N_VAR)
            self.symbol_table.insert('result', result_entry)

    def codegen(self):
        if self.func_type:
            self.func_type.codegen()
            result_ptr = self.builder.alloca(self.func_type.cvalue)
            result_entry = SymbolEntry(
                stype=self.func_type.stype,
                name_type=NameType.N_VAR, cvalue=result_ptr)
            self.symbol_table.insert('result', result_entry)


class Formal(AST):

    def __init__(
            self,
            ids,
            type_,
            by_reference,
            builder,
            module,
            symbol_table,
            lineno):
        super(Formal, self).__init__(builder, module, symbol_table, lineno)
        self.ids = ids
        self.type_ = type_
        self.by_reference = by_reference

    def sem(self):
        self.type_.sem()
        if self.type_.stype[0] in [ComposerType.T_CONST_ARRAY, ComposerType.T_VAR_ARRAY] and (not self.by_reference):
            msg = 'Arrays are not allowed to pass by value'
            self.raise_exception_helper(msg, PCLSemError)

        self.stype = self.type_.stype


class Type(AST):

    def __init__(self, type_, builder, module, symbol_table, lineno):
        super(Type, self).__init__(builder, module, symbol_table, lineno)
        self.type_ = type_

    def sem(self):
        self.stype = (ComposerType.T_NO_COMP, BaseType(self.type_))

    def codegen(self):
        self.cvalue = LLVMTypes.mapping[self.type_]


class PointerType(Type):
    '''
        Declaration of a new pointer.
        Example: ^integer
    '''

    def __init__(self, type_, builder, module, symbol_table, lineno):
        super(PointerType, self).__init__(type_, builder, module, symbol_table, lineno)
        self.type_ = type_

    def sem(self):
        self.type_.sem()
        base_type = self.type_.stype
        self.stype = (ComposerType.T_PTR, base_type)

    def codegen(self):
        self.type_.codegen()
        self.cvalue = ir.PointerType(self.type_.cvalue)


class ArrayType(Type):

    def __init__(self, length, type_, builder, module, symbol_table, lineno):
        super(ArrayType, self).__init__(type_, builder, module, symbol_table, lineno)
        self.length = int(length)

    def sem(self):
        self.type_.sem()
        if self.length > 0:
            self.stype = (ComposerType.T_CONST_ARRAY, self.type_.stype)
        elif self.length == 0:
            self.stype = (ComposerType.T_VAR_ARRAY, self.type_.stype)
        else:
            msg = 'Negative length specified'
            self.raise_exception_helper(msg, PCLSemError)

    def codegen(self):
        self.type_.codegen()
        self.cvalue = ir.ArrayType(self.type_.cvalue, self.length)


class Statement(AST):

    def __init__(self, builder, module, symbol_table, lineno, **kwargs):
        super(Statement, self).__init__(builder, module, symbol_table, lineno)
        self.name = kwargs.get('name', None)
        self.stmt = kwargs.get('stmt', None)

    def sem(self):
        if self.name:
            self.symbol_table.lookup(self.name)
            self.stmt.sem()

    def codegen(self):
        if self.name:
            self.cvalue = self.builder.append_basic_block(self.name)
            self.builder.branch(self.cvalue)
            label_entry = SymbolEntry(
                stype=(
                    ComposerType.T_NO_COMP,
                    BaseType.T_LABEL),
                name_type=NameType.N_LABEL,
                cvalue=self.cvalue)
            self.symbol_table.insert(self.name, label_entry)
            # TODO FIX
            # with self.builder.goto_block(self.cvalue):
            self.builder.position_at_start(self.cvalue)
            next_block = self.builder.append_basic_block()
            self.stmt.codegen()
            self.builder.branch(next_block)
            self.builder.position_at_start(next_block)


class Block(Statement):

    def __init__(self, stmt_list, builder, module, symbol_table, lineno):
        super(Block, self).__init__(builder, module, symbol_table, lineno)
        self.stmt_list = stmt_list

    def sem(self):
        for stmt in self.stmt_list:
            stmt.sem()

    def codegen(self):
        #helper_block = self.builder.append_basic_block()
        #with self.builder.goto(helper_block):
        for stmt in self.stmt_list:
            stmt.codegen()


class Call(Statement):
    def __init__(self, id_, exprs, builder, module, symbol_table, lineno):
        super(Call, self).__init__(builder, module, symbol_table, lineno)
        self.id_ = id_
        self.exprs = exprs

    def sem(self):

        # Assert that if call is recursive (calee calls himself) then fcn must
        # be forward
        self.symbol_table.needs_forward_declaration(self.id_)

        try:
            call_entry = self.symbol_table.lookup(self.id_)
        except PCLSymbolTableError:
            call_entry = self.symbol_table.lookup('forward_' + self.id_)
        except:
            msg = 'Name {} not found'.format(self.id_)
            self.raise_exception_helper(msg, PCLSemError)

        formals = self.symbol_table.formal_generator(self.id_)
        self.stype = call_entry.stype

        # Check arguments
        for expr, (formal_name, formal) in zip(self.exprs, formals):
            expr.sem()
            try:
                expr.type_check(formal.stype)
            except PCLSemError as e:
                if expr.stype == formal.stype and is_composite(expr.stype):
                    continue
                elif formal.stype[1] == BaseType.T_REAL and expr.stype[1] == BaseType.T_INT:
                    continue
                elif formal.stype[0] == ComposerType.T_VAR_ARRAY and expr.stype[0] == ComposerType.T_CONST_ARRAY:
                    continue
                else:
                    msg = 'Incompatible assignment type: {}'.format(formal_name)
                    self.raise_exception_helper(msg, PCLSemError)

    def codegen(self):
        # WIP
        real_params = []

        try:
            call_entry_cvalue = self.symbol_table.lookup(self.id_).cvalue
        except PCLSymbolTableError:
            call_entry_cvalue = self.symbol_table.lookup('forward_' + self.id_).cvalue
        except:
            # Should never be reached
            msg = 'Unknown name: {}'.format(self.id_)
            self.raise_exception_helper(msg, PCLSemError)


        formals = self.symbol_table.formal_generator(self.id_)
        for expr, formal_type, (_, formal) in zip(self.exprs, call_entry_cvalue.args, formals):
            expr.codegen()
            if formal.by_reference:
                if expr.gep:
                    ptr = expr.gep
                    # import pdb; pdb.set_trace()
                    if ptr.type != formal_type.type:
                        ptr = self.builder.bitcast(ptr, formal_type.type)

                    real_params.append(ptr)
                else:
                    raise NotImplementedError()
            else:
                if isinstance(expr, StringLiteral):
                    ptr = expr.gep
                    real_params.append(ptr)
                else:
                    real_params.append(expr.cvalue)

        self.cvalue = self.builder.call(call_entry_cvalue, real_params)


class If(Statement):
    '''
        If statement.
    '''

    def __init__(self, expr, stmt, else_stmt, builder, module, symbol_table, lineno):
        super(If, self).__init__(builder, module, symbol_table, lineno)
        self.expr = expr
        self.stmt = stmt
        self.else_stmt = else_stmt

    def sem(self):
        self.expr.sem()
        self.expr.type_check((ComposerType.T_NO_COMP, BaseType.T_BOOL))

        self.stmt.sem()
        if self.else_stmt:
            self.else_stmt.sem()

    def codegen(self):
        self.expr.codegen()

        if self.else_stmt:
            with self.builder.if_else(self.expr.cvalue) as (then, otherwise):
                with then:
                    self.stmt.codegen()
                with otherwise:
                    self.else_stmt.codegen()
        else:
            with self.builder.if_then(self.expr.cvalue):
                self.stmt.codegen()


class While(Statement):
    '''
        While statement.
    '''

    def __init__(self, expr, stmt, builder, module, symbol_table, lineno):
        super(While, self).__init__(builder, module, symbol_table, lineno)
        self.expr = expr
        self.stmt = stmt

    def sem(self):
        self.expr.sem()
        self.expr.type_check((ComposerType.T_NO_COMP, BaseType.T_BOOL))
        self.stmt.sem()

    def codegen(self):
        w_body_block = self.builder.append_basic_block()
        w_after_block = self.builder.append_basic_block()
        self.expr.codegen()
        self.builder.cbranch(self.expr.cvalue, w_body_block, w_after_block)
        self.builder.position_at_start(w_body_block)
        self.stmt.codegen()
        self.expr.codegen()
        self.builder.cbranch(self.expr.cvalue, w_body_block, w_after_block)
        self.builder.position_at_start(w_after_block)


class Goto(Statement):
    '''
        Goto statement.
    '''

    def __init__(self, id_, builder, module, symbol_table, lineno):
        super(Goto, self).__init__(builder, module, symbol_table, lineno)
        self.id_ = id_

    def sem(self):
        self.symbol_table.lookup(self.id_, last_scope=True)

    def codegen(self):
        # TODO fix non terminating block
        helper_block = self.builder.append_basic_block()
        self.builder.branch(helper_block)
        self.builder.position_at_start(helper_block)
        goto_block = self.symbol_table.lookup(self.id_).cvalue
        self.builder.branch(goto_block)
        next_block = self.builder.append_basic_block()
        self.builder.position_at_start(next_block)

class Return(Statement):
    '''
        Return statement.
    '''

    def sem(self):
        try:
            result_entry = self.symbol_table.lookup('result')
            # TODO Is this needed?
            if result_entry.num_queries == 1:
                msg = 'Result must be set once'
                self.raise_exception_helper(msg, PCLSemError)
        except PCLSymbolTableError:
            pass

    def codegen(self):
        return_block = self.builder.append_basic_block()
        self.builder.branch(return_block)
        self.builder.position_at_start(return_block)
        try:
            # Function
            result_cvalue_ptr = self.symbol_table.lookup('result').cvalue
            result_cvalue = self.builder.load(result_cvalue_ptr)
            self.builder.ret(result_cvalue)
        except PCLSymbolTableError:
            # Procedure
            self.builder.ret_void()
        next_block = self.builder.append_basic_block()
        self.builder.position_at_start(next_block)


class Empty(Statement):
    '''
        Empty Statement.
    '''

    def sem(self):
        pass

    def codegen(self):
        pass


class New(Statement):
    '''
        New Statement.
    '''

    def __init__(self, expr, lvalue, builder, module, symbol_table, lineno):
        super(New, self).__init__(builder, module, symbol_table, lineno)
        self.expr = expr
        self.lvalue = lvalue

    def sem(self):
        self.lvalue.sem()
        if self.expr:
            if self.lvalue.stype[0] != ComposerType.T_PTR or self.lvalue.stype[1][0] != ComposerType.T_VAR_ARRAY:
                msg = 'Cannot create new instance of {}'.format(self.lvalue.stype)
                self.raise_exception_helper(msg, PCLSemError)

            self.expr.sem()
            self.expr.type_check((ComposerType.T_NO_COMP, BaseType.T_INT))

            # ^array of t -> array [n] of t
            self.stype = (
                ComposerType.T_CONST_ARRAY,
                self.lvalue.stype[1][1][1])

        else:
            if self.lvalue.stype[0] != ComposerType.T_PTR or not is_composite(
                    self.lvalue.stype[1]):
                msg = 'Cannot create new instance of {}'.format(self.lvalue.stype)
                self.raise_exception_helper(msg, PCLSemError)

            # ^t -> t
            self.stype = self.lvalue.stype[1]

    def codegen(self):
        self.lvalue.codegen()
        # alloca_type = self.lvalue.gep.type.pointee.pointee

        # if self.expr:
        #     self.expr.codegen()
        #     self.cvalue = self.builder.alloca(self.lvalue.gep.type.pointee.pointee.pointee, self.expr.cvalue)
        #     # import pdb; pdb.set_trace()
        #     self.builder.store(self.cvalue, self.lvalue.cvalue)
        # else:
        self.cvalue = self.builder.alloca(self.lvalue.gep.type.pointee.pointee)
        self.builder.store(self.cvalue, self.lvalue.gep)


class Dispose(Statement):
    '''
        Dispose statement.
    '''

    def __init__(self, lvalue, brackets, builder, module, symbol_table, lineno):
        super(Dispose, self).__init__(builder, module, symbol_table, lineno)
        self.lvalue = lvalue
        self.brackets = brackets

    def sem(self):
        self.lvalue.sem()

        if self.brackets:
            if self.lvalue.stype[0] != ComposerType.T_PTR or self.lvalue.stype[1][0] != ComposerType.T_VAR_ARRAY:
                msg = 'Cannot dispose instance of {}'.format(self.lvalue.stype)
                self.raise_exception_helper(msg, PCLSemError)
        else:
            if self.lvalue.stype[0] != ComposerType.T_PTR or not is_composite(
                    self.lvalue.stype[1]):
                msg = 'Cannot dispose instance of {}'.format(self.lvalue.stype)
                self.raise_exception_helper(msg, PCLSemError)

        self.stype = (ComposerType.T_NO_COMP, BaseType.T_NIL)

    def codegen(self):
        self.lvalue.codegen()
        self.lvalue.set_nil()

class Expr(AST):
    '''
        Base class for expressions.
    '''
    pass


class RValue(Expr):
    '''
        Base class for the RValue.
    '''

    def __init__(self, builder, module, symbol_table, lineno):
        super(RValue, self).__init__(builder, module, symbol_table, lineno)

    def type_check(self, target, *args):
        if isinstance(target, list):
            target_types = [x[1] for x in target]
            if self.stype[1] == BaseType.T_NIL or BaseType.T_NIL in target_types:
                return True
        else:
            if self.stype[1] == BaseType.T_NIL or BaseType.T_NIL == target[1]:
                return True

        super(RValue, self).type_check(target, *args)


class IntegerConst(RValue):
    '''
        Integer constant. Holds integer numbers.
    '''

    def __init__(self, value, builder, module, symbol_table, lineno):
        super(IntegerConst, self).__init__(builder, module, symbol_table, lineno)
        self.value = int(value)

    def sem(self):
        self.stype = (ComposerType.T_NO_COMP, BaseType.T_INT)

    def codegen(self):
        self.cvalue = ir.Constant(LLVMTypes.T_INT, self.value)


class RealConst(RValue):
    '''
        Real constant. Holds floating point numbers.
    '''

    def __init__(self, value, builder, module, symbol_table, lineno):
        super(RealConst, self).__init__(builder, module, symbol_table, lineno)
        self.value = float(value)

    def sem(self):
        self.stype = (ComposerType.T_NO_COMP, BaseType.T_REAL)

    def codegen(self):
        self.cvalue = ir.Constant(LLVMTypes.T_REAL, self.value)


class CharConst(RValue):
    '''
        Character constant. Contains exactly one literal.
    '''

    def __init__(self, value, builder, module, symbol_table, lineno):
        super(CharConst, self).__init__(builder, module, symbol_table, lineno)
        self.value = ord(value)

    def sem(self):
        self.stype = (ComposerType.T_NO_COMP, BaseType.T_CHAR)

    def codegen(self):
        self.cvalue = ir.Constant(LLVMTypes.T_CHAR, self.value)


class BoolConst(RValue):
    '''
        Boolean constant. Can be true or false.
    '''

    def __init__(self, value, builder, module, symbol_table, lineno):
        super(BoolConst, self).__init__(builder, module, symbol_table, lineno)
        self.value = int(value == 'true')

    def sem(self):
        self.stype = (ComposerType.T_NO_COMP, BaseType.T_BOOL)

    def codegen(self):
        self.cvalue = ir.Constant(LLVMTypes.T_BOOL, self.value)


class Ref(RValue):
    '''
        Declares a pointer to an LValue. That is if
        t is integer then ^t is a pointer to an integer
    '''

    def __init__(self, lvalue, builder, module, symbol_table, lineno):
        super(Ref, self).__init__(builder, module, symbol_table, lineno)
        self.lvalue = lvalue

    def sem(self):
        self.lvalue.sem()
        self.stype = (ComposerType.T_PTR, self.lvalue.stype)


class Nil(RValue):
    '''
        The null pointer. Must be declared as a singleton.
    '''

    def __init__(self, builder, module, symbol_table, lineno):
        super(Nil, self).__init__(builder, module, symbol_table, lineno)

    def sem(self):
        self.stype = (ComposerType.T_NO_COMP, BaseType.T_NIL)

    def codegen(self):
        pass

class ArUnOp(RValue):
    '''
        Unary operator. +x, -x
    '''

    def __init__(self, op, rhs, builder, module, symbol_table, lineno):
        super(ArUnOp, self).__init__(builder, module, symbol_table, lineno)
        self.op = op
        self.rhs = rhs

    def sem(self):
        self.rhs.sem()
        self.rhs.type_check(arithmetic_types)
        self.stype = self.rhs.stype

    def codegen(self):
        self.rhs.codegen()

        if self.op == '+':
            self.cvalue = self.rhs.cvalue
        elif self.op == '-':
            if self.stype[1] == BaseType.T_INT:
                self.cvalue = self.builder.neg(self.rhs.cvalue)
            elif self.stype[1] == BaseType.T_REAL:
                self.cvalue = self.builder.fsub(
                    LLVMConstants.ZERO_REAL, self.rhs.cvalue)


class LogicUnOp(RValue):
    '''
        Unary operator. +x, -x
    '''

    def __init__(self, op, rhs, builder, module, symbol_table, lineno):
        super(LogicUnOp, self).__init__(builder, module, symbol_table, lineno)
        self.op = op
        self.rhs = rhs

    def sem(self):
        self.rhs.sem()
        self.rhs.type_check((ComposerType.T_NO_COMP, BaseType.T_BOOL))
        self.stype = self.rhs.stype

    def codegen(self):
        self.rhs.codegen()
        self.cvalue = self.builder.not_(self.rhs.cvalue)


class ArOp(RValue):
    '''
        Arithmetic operation between two sides (lhs, rhs)
    '''

    def __init__(self, op, lhs, rhs, builder, module, symbol_table, lineno):
        super(ArOp, self).__init__(builder, module, symbol_table, lineno)
        self.op = op
        self.lhs = lhs
        self.rhs = rhs

    def sem(self):
        self.lhs.sem()
        self.rhs.sem()

        self.lhs.type_check(arithmetic_types)
        self.rhs.type_check(arithmetic_types)

        if self.op == '/':
            self.stype = real_type
            return

        if self.op == 'div' or self.op == 'mod':
            self.lhs.type_check(int_type)
            self.rhs.type_check(int_type)

        if self.lhs.stype == real_type or self.rhs.stype == real_type:
            self.stype = real_type
            return

        self.stype = int_type

    def codegen(self):
        self.lhs.codegen()
        self.rhs.codegen()

        if self.lhs.stype == real_type and self.rhs.stype == int_type:
            lhs_cvalue = self.lhs.cvalue
            rhs_cvalue = self.builder.sitofp(self.rhs.cvalue, LLVMTypes.T_REAL)
        elif self.lhs.stype == int_type and self.rhs.stype == real_type:
            lhs_cvalue = self.builder.sitofp(self.lhs.cvalue, LLVMTypes.T_REAL)
            rhs_cvalue = self.rhs.cvalue
        elif self.op == '/':
            lhs_cvalue = self.builder.sitofp(self.lhs.cvalue, LLVMTypes.T_REAL)
            rhs_cvalue = self.builder.sitofp(self.rhs.cvalue, LLVMTypes.T_REAL)
        else:
            lhs_cvalue = self.lhs.cvalue
            rhs_cvalue = self.rhs.cvalue

        if self.lhs.stype == int_type and self.rhs.stype == int_type:
            if self.op == '+':
                self.cvalue = self.builder.add(lhs_cvalue, rhs_cvalue)
            elif self.op == '-':
                self.cvalue = self.builder.sub(lhs_cvalue, rhs_cvalue)
            elif self.op == '*':
                self.cvalue = self.builder.mul(lhs_cvalue, rhs_cvalue)
            elif self.op == '/':
                self.cvalue = self.builder.fdiv(lhs_cvalue, rhs_cvalue)
            elif self.op == 'div':
                self.cvalue = self.builder.sdiv(lhs_cvalue, rhs_cvalue)
            elif self.op == 'mod':
                self.cvalue = self.builder.srem(lhs_cvalue, rhs_cvalue)
        else:
            if self.op == '+':
                self.cvalue = self.builder.fadd(lhs_cvalue, rhs_cvalue)
            elif self.op == '-':
                self.cvalue = self.builder.fsub(lhs_cvalue, rhs_cvalue)
            elif self.op == '*':
                self.cvalue = self.builder.fmul(lhs_cvalue, rhs_cvalue)
            elif self.op == '/':
                self.cvalue = self.builder.fdiv(lhs_cvalue, rhs_cvalue)


class CompOp(RValue):
    '''
        Comparison operation between two sides (lhs, rhs)
    '''

    def __init__(self, op, lhs, rhs, builder, module, symbol_table, lineno):
        super(CompOp, self).__init__(builder, module, symbol_table, lineno)
        self.op = op
        self.lhs = lhs
        self.rhs = rhs

    def sem(self):
        self.lhs.sem()
        self.rhs.sem()

        if self.op == '=' or self.op == '<>':
            arithmetic = (
                self.lhs.stype in arithmetic_types) and (
                self.rhs.stype in arithmetic_types)
            if not arithmetic:
                assert self.lhs.stype == self.rhs.stype, 'Comparison is only allowed between operands of same type'
                assert self.lhs.stype[0] != ComposerType.T_CONST_ARRAY and self.lhs.stype[
                    0] != ComposerType.T_VAR_ARRAY, 'Arrays cannot be compared.'
        else:
            self.lhs.type_check(arithmetic_types)
            self.rhs.type_check(arithmetic_types)

        self.stype = (ComposerType.T_NO_COMP, BaseType.T_BOOL)

    def codegen(self):
        self.lhs.codegen()
        self.rhs.codegen()

        arithmetic = (
            self.lhs.stype in arithmetic_types) and (
            self.rhs.stype in arithmetic_types)

        boolean = (
            self.lhs.stype == (ComposerType.T_NO_COMP, BaseType.T_BOOL)) and (
            self.rhs.stype == (ComposerType.T_NO_COMP, BaseType.T_BOOL))


        cmp_op = LLVMOperators.get_op(self.op)

        if arithmetic:
            if self.lhs.stype == real_type and self.rhs.stype == int_type:
                lhs_cvalue = self.lhs.cvalue
                rhs_cvalue = self.builder.sitofp(
                    self.rhs.cvalue, LLVMTypes.T_REAL)
            elif self.lhs.stype == int_type and self.rhs.stype == real_type:
                lhs_cvalue = self.builder.sitofp(
                    self.lhs.cvalue, LLVMTypes.T_REAL)
                rhs_cvalue = self.rhs.cvalue
            else:
                lhs_cvalue = self.lhs.cvalue
                rhs_cvalue = self.rhs.cvalue

            if (self.lhs.stype == int_type and self.rhs.stype == int_type) or boolean:
                self.cvalue = self.builder.icmp_signed(
                    cmp_op, lhs_cvalue, rhs_cvalue)
            else:
                self.cvalue = self.builder.fcmp_ordered(
                    cmp_op, lhs_cvalue, rhs_cvalue)
        elif self.op in ['=', '<>']:
                # lhs_cvalue = self.builder.ptrtoint(self.lhs.cvalue, LLVMTypes.T_INT)
                # rhs_cvalue = self.builder.ptrtoint(self.rhs.cvalue, LLVMTypes.T_INT)
                self.cvalue = self.builder.icmp_signed(cmp_op, self.lhs.cvalue, self.rhs.cvalue)


class LogicOp(RValue):
    '''
        Logic operation between two sides (lhs, rhs)
    '''

    def __init__(self, op, lhs, rhs, builder, module, symbol_table, lineno):
        super(LogicOp, self).__init__(builder, module, symbol_table, lineno)
        self.op = op
        self.lhs = lhs
        self.rhs = rhs

    def sem(self):
        self.lhs.sem()
        self.rhs.sem()
        bool_type = (ComposerType.T_NO_COMP, BaseType.T_BOOL)

        self.lhs.type_check(bool_type)
        self.rhs.type_check(bool_type)

        self.stype = bool_type

    def codegen(self):
        self.lhs.codegen()
        self.rhs.codegen()

        if self.op == 'and':
            self.cvalue = self.builder.and_(self.lhs.cvalue, self.rhs.cvalue)
        elif self.op == 'or':
            self.cvalue = self.builder.or_(self.lhs.cvalue, self.rhs.cvalue)


class AddressOf(RValue):
    '''
        Declaration of address of an l-value
        with r-value = @l-value
    '''

    def __init__(self, lvalue, builder, module, symbol_table, lineno):
        if isinstance(lvalue, RValue):
            msg = 'Tried to access the address of an RValue'
            self.raise_exception_helper(msg, PCLParserError)
        super(AddressOf, self).__init__(builder, module, symbol_table, lineno)
        self.lvalue = lvalue

    def sem(self):
        self.lvalue.sem()
        self.stype = (ComposerType.T_PTR, self.lvalue.stype)

    def codegen(self):
        self.lvalue.codegen()
        self.cvalue = self.symbol_table.lookup(self.lvalue.id_).cvalue

class LValue(Expr):
    '''
        Base class for the LValue
    '''

    def __init__(self, builder, module, symbol_table, lineno):
        super(LValue, self).__init__(builder, module, symbol_table, lineno)
        self.load = False
        self.gep = None


class NameLValue(LValue):
    '''
        Named LValue: variable name (i.e. x)
    '''

    def __init__(self, id_, builder, module, symbol_table, lineno):
        super(NameLValue, self).__init__(builder, module, symbol_table, lineno)
        self.id_ = id_

    def sem(self):
        result = self.symbol_table.lookup(self.id_)
        self.stype = result.stype
        # if self.load and result.num_queries == 1:
        # msg = 'Uniitialized lvalue: {}'.format(self.id_)
        # raise PCLSemError(msg)

    def codegen(self):
        self.gep = self.symbol_table.lookup(self.id_).cvalue
        # OPTIMIZE remove redundant loads
        if self.load:
            # if isinstance(self.gep, ir.GlobalVariable):

            self.cvalue = self.builder.load(self.gep)

    def set_nil(self):
        # Result is a pointer to our type e.g. for integer variable i32 it is *i32
        result = self.symbol_table.lookup(self.id_).cvalue

        # Convert 0 to the pointee of the pointer (the actual type)
        nil = self.builder.inttoptr(LLVMConstants.ZERO_INT, result.type.pointee)

        # Store value to pointee
        self.builder.store(nil, result)



class Result(NameLValue):
    '''
        Holds the result of a function
    '''

    def __init__(self, builder, module, symbol_table, lineno):
        super(Result, self).__init__('result', builder, module, symbol_table, lineno)

    def sem(self):
       result = self.symbol_table.lookup('result')
       self.stype = result.stype

    def codegen(self):
       self.gep = self.symbol_table.lookup('result').cvalue

       if self.load:
           self.cvalue = self.builder.load(self.gep)

class StringLiteral(LValue):
    '''
        Holds a node for a string literal
    '''

    def __init__(self, literal, builder, module, symbol_table, lineno):
        super(StringLiteral, self).__init__(builder, module, symbol_table, lineno)
        self.literal = literal + '\0'
        self.length = len(self.literal)

    def sem(self):
        self.stype = (
            ComposerType.T_CONST_ARRAY,
            (ComposerType.T_NO_COMP,
             BaseType.T_CHAR))

    def codegen(self):
        self.cvalue = ir.Constant(
            ir.ArrayType(
                LLVMTypes.T_CHAR, self.length), bytearray(
                self.literal.encode("utf-8")))
        self.gep = self.builder.alloca(self.cvalue.type)
        self.builder.store(self.cvalue, self.gep)


class Deref(LValue):
    '''
        Declaration of dereference of a pointer
        If e = t^ then ^e = t
    '''

    def __init__(self, expr, builder, module, symbol_table, lineno):
        super(Deref, self).__init__(builder, module, symbol_table, lineno)
        if isinstance(expr, Nil):
            msg = 'Cannot dereference nil'
            self.raise_exception_helper(msg, PCLSemError)

        self.expr = expr

    def sem(self):
        self.expr.sem()
        if self.expr.stype[0] != ComposerType.T_PTR:
            msg = 'Dereferencing non-pointer expression'
            self.raise_exception_helper(msg, PCLSemError)
        elif self.expr.stype[1] == BaseType.T_NIL:
            msg = 'Cannot dereference nil'
            self.raise_exception_helper(msg, PCLSemError)

        self.stype = self.expr.stype[1]

    def codegen(self):
        self.expr.codegen()
        self.gep = self.expr.cvalue
        self.cvalue = self.builder.load(self.expr.cvalue)


class SetExpression(LValue):
    '''
        Assignment of an expression to a name
    '''

    def __init__(self, lvalue, expr, builder, module, symbol_table, lineno):
        super(SetExpression, self).__init__(builder, module, symbol_table, lineno)
        self.lvalue = lvalue
        self.expr = expr

    def sem(self):
        self.expr.sem()
        self.lvalue.sem()

        if self.expr.stype == self.lvalue.stype and is_composite(
                self.expr.stype):
            return
        elif self.lvalue.stype[1] == BaseType.T_REAL and self.expr.stype[1] == BaseType.T_INT:
            return
        elif self.lvalue.stype[0] == ComposerType.T_VAR_ARRAY and self.expr.stype[0] == ComposerType.T_CONST_ARRAY:
            return
        elif self.expr.stype[1] == BaseType.T_NIL:
            return
        elif self.expr.stype == (ComposerType.T_CONST_ARRAY, (ComposerType.T_NO_COMP, BaseType.T_CHAR)):
            return
        else:
            msg = 'Invalid set expression {} := {}'.format(self.lvalue.stype, self.expr.stype)
            self.raise_exception_helper(msg, PCLSemError)

    def codegen(self):
        self.expr.codegen()
        self.lvalue.codegen()

        if self.expr.stype[1] == BaseType.T_NIL:
            self.lvalue.set_nil()
        elif self.lvalue.gep:
            self.builder.store(self.expr.cvalue, self.lvalue.gep)


class LBrack(LValue):
    '''
        ArrayElement
    '''

    def __init__(self, lvalue, expr, builder, module, symbol_table, lineno):
        super(LBrack, self).__init__(builder, module, symbol_table, lineno)
        self.lvalue = lvalue
        self.expr = expr

    def sem(self):
        self.expr.sem()
        self.expr.type_check((ComposerType.T_NO_COMP, BaseType.T_INT))
        self.lvalue.sem()
        self.stype = self.lvalue.stype[1]

    def codegen(self):
        self.expr.codegen()
        self.lvalue.codegen()

        self.gep = self.builder.gep(self.lvalue.gep, [LLVMConstants.ZERO_INT, self.expr.cvalue])

        self.cvalue = self.builder.load(self.gep)

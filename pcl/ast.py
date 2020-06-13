import json
import sys
import warnings
from abc import ABC, abstractmethod
from collections import deque
from llvmlite import ir, binding

from pcl.error import *
from pcl.symbol_table import *
from pcl.codegen import *

def fix_escape(literal):
    mapping = {
        '\\n' : '\n',
        '\\t' : '\t',
        '\\r' : '\r',
        '\\0' : '\0',
        '\\\\' : '\\',
        '\'' : "'",
        '\"' : '"'
    }
    for key, val in mapping.items():
        literal = literal.replace(key, val)
    return literal


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


    def raise_exception_helper(self, msg, exception=PCLSemError):
        ''' Helper function to raise Exceptions including line numbers '''
        msg_new = '{} at line {}: {}'.format(
            self.__class__.__name__, self.lineno, msg)
        raise exception(msg_new)

    def raise_warning_helper(self, msg):
        ''' Helper function to raise warnings including line numbers '''
        msg_new = 'WARNING {} at line {}: {}\n'.format(
            self.__class__.__name__, self.lineno, msg)
        warnings.warn(msg_new, PCLWarning)

    @abstractmethod
    def sem(self):
        ''' Abstract method for semantic analysis '''
        msg = 'sem method not implemented for {}'.format(
            self.__class__.__name__)
        raise NotImplementedError(msg)

    @staticmethod
    def sem_decorator(sem_fn):
        ''' Decorator that allows memoization on semantic analysis '''

        def wrapper(self):
            if self.stype is None:
                sem_fn(self)
        return wrapper

    @abstractmethod
    def codegen(self):
        ''' Abstract method for code generation '''
        msg = 'codegen method not implemented for {}'.format(
            self.__class__.__name__)
        raise NotImplementedError(msg)

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

        if isinstance(target, list):
            target_str = ', '.join([str_type(t) for t in target])
        else:
            target_str = str_type(target)
        msg = '{}: Expected type {}, got type {}. {}'.format(
            self.__class__.__name__, target_str, str_type(self.stype), ', '.join([str_type(arg) for arg in args]))
        self.raise_exception_helper(msg, PCLSemError)

    def print_module(self):
        ''' Prints (non-verified) LLVM code at the given node '''
        print(str(self.module))

    def pprint(self, indent=0):
        '''
            Pretty printing of a node's contents and
            its sucessors. Call it with root.pprint()
            Output to stderr.
        '''
        sys.stderr.write('{}{}'.format(indent * ' ', type(self)))
        d = vars(self)
        for k, v in d.items():

            if k not in ['module', 'builder', 'symbol_table']:
                if isinstance(v, AST):
                    sys.stderr.write((indent - 1) * ' ')
                    v.pprint(indent + 1)
                elif isinstance(v, deque):
                    for x in v:
                        sys.stderr.write((indent - 1) * ' ')
                        if isinstance(x, AST):
                            x.pprint(indent + 1)
                        else:
                            sys.stderr.write((indent + 1) * ' ' + x + '\n')
                else:
                    sys.stderr.write((indent + 2) * ' ')
                    sys.stderr.write('{} : {}\n'.format(k, v))


class Program(AST):
    '''
        Main program AST node. Contains the body of the program
    '''

    def __init__(self, id_, body, builder, module, symbol_table, lineno):
        super(Program, self).__init__(builder, module, symbol_table, lineno)
        self.id_ = id_
        self.body = body

    @AST.sem_decorator
    def sem(self):
        '''
            Creates the main scope of the program and
            proceeds to the program body.
        '''
        # Open program scope
        self.symbol_table.open_scope()

        # Run sem on body
        self.body.sem()

        # Close main scope
        self.symbol_table.close_scope()

    def codegen(self):
        '''
            Creates the main scope of the program and
            proceeds to the program body.
        '''
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

    @AST.sem_decorator
    def sem(self):
        '''
            Runs semantic to locals and then to block.
        '''

        # Run semantic to locals
        for local in self.locals_:
            local.sem()

        # Run sem to block
        self.block.sem()

    def codegen(self):
        '''
            Runs codegen to locals and then to block.
        '''
        # Run codegen to locals
        for local in self.locals_:
            local.codegen()

        self.block.codegen()


class Local(AST):
    def __init__(self, builder, module, symbol_table, lineno):
        super(Local, self).__init__(builder, module, symbol_table, lineno)


class LocalHeader(Local):
    def __init__(self, header, body, builder, module, symbol_table, lineno):
        super(
            LocalHeader,
            self).__init__(
            builder,
            module,
            symbol_table,
            lineno)
        self.header = header
        self.body = body

    @AST.sem_decorator
    def sem(self):
        '''
            Perform semantic analysis on a header accompanied by a body
            The discrete steps are the following:
                1. Infer the semantic type of the function/procedure
                2. Register header to the symbol table
                3. Register formals to the symbol table
                4. Open a scope
                5. Register formals as local variables
                6. Perform semantic analysis on the body
                7. Close the scope
        '''

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

        self.symbol_table.insert(self.header.id_, header_name_entry, lineno=self.lineno)

        for formal in self.header.formals:
            formal.sem()
            for formal_id in formal.ids:
                formal_entry = SymbolEntry(
                    stype=formal.stype,
                    name_type=NameType.N_FORMAL,
                    by_reference=formal.by_reference)
                self.symbol_table.insert_formal(
                    self.header.id_, formal_id, formal_entry, lineno=self.lineno)

        # Open function scope
        self.symbol_table.open_scope(self.header.id_)

        # Register header locals
        self.header.sem()
        for formal in self.header.formals:
            formal.sem()
            for id_ in formal.ids:
                id_entry = SymbolEntry(
                    stype=formal.stype, name_type=NameType.N_VAR)
                self.symbol_table.insert(id_, id_entry, lineno=self.lineno)

        # Sem the body
        self.body.sem()

        # Close function scope
        self.symbol_table.close_scope()

    def codegen(self):
        '''
            Run codegen on a header accompanied by a body. The
            discrete steps are:
                1. Infer header and formal types (in llvmlite)
                    1a. A parameter x with type t that passes by value is accompanied
                    by an ir.Argument of type t
                    1b. A parameter x with type t that passes by reference is accompanied
                    by an ir.Argument of type t*
                2. Register the function signature (ir.FunctionType)
                    2a. Check if forward f(...) : type is defined
                3. Register the function to the symbol table (codegen value)
                4. Open a scope
                5. Register arguments as local variables (which are global wrt to
                    the inside scopes)
                    5a. A parameter x with type t that passes by value is copied
                    within the ir.Function body
                    5b. A parameter x with type t that passes by value has its pointer
                    stored
                6. Close scope
        '''

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
            header_entry = self.symbol_table.lookup(
                'forward_' + self.header.id_, lineno=self.lineno)
            header_cvalue = header_entry.cvalue
        except PCLSymbolTableError:
            header_counter = self.symbol_table.auto_header(self.header.id_)
            header_cvalue = ir.Function(
                self.module,
                header_type_cvalue,
                name=self.header.id_ + '_' + str(header_counter))

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

            self.symbol_table.insert(self.header.id_, header_entry, lineno=self.lineno)

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
                        self.header.id_, formal_id, arg_formal_entry, lineno=self.lineno)
                    counter += 1

            # Open a named scope
            self.symbol_table.open_scope(self.header.id_)

            # Process the header
            self.header.codegen()

            # Process arguments inside the function / proc.
            counter = 0
            for formal in self.header.formals:
                for formal_id in formal.ids:
                    arg = header_args[counter]
                    if not formal.by_reference:
                        arg_name = '{}_{}'.format(formal_id, self.symbol_table.auto(formal_id))
                        arg_cvalue = ir.GlobalVariable(
                            self.module, arg.type, name=arg_name)

                        # If variable needs only local storage we can use alloca
                        # arg_cvalue = self.builder.alloca(arg.type)

                        # Set initializer to zeroinitializer ir.Constant(typ, None)
                        arg_cvalue.initializer = ir.Constant(arg.type, None)
                        arg_cvalue.linkage = 'internal'

                        # Make a copy of the variable
                        self.builder.store(arg, arg_cvalue)
                    else:
                        # Pass the variable pointer
                        arg_cvalue = arg
                    arg_entry = SymbolEntry(
                        stype=formal.stype,
                        name_type=NameType.N_VAR,
                        cvalue=arg_cvalue)
                    self.symbol_table.insert(formal_id, arg_entry, lineno=self.lineno)
                    counter += 1

            # Run codegen to body
            self.body.codegen()

            # Guardian return statements
            try:
                # Function
                result_cvalue_ptr = self.symbol_table.lookup('result', lineno=self.lineno).cvalue
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

    @AST.sem_decorator
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

    @AST.sem_decorator
    def sem(self):
        '''
            Infer type of variable list and register all identifiers
            to the symbol table/
        '''
        self.type_.sem()
        # Iterate over all names and register variables
        for id_ in self.ids:
            var_entry = SymbolEntry(
                stype=self.type_.stype,
                name_type=NameType.N_VAR)
            self.symbol_table.insert(id_, var_entry, lineno=self.lineno)

    def codegen(self):
        '''
            Registers all the variables (as ir.GlobalVariable) at the
            symbol table. The variable initializers are set to
            zeroinitializer, provided by LLVM.
        '''
        self.type_.codegen()
        for id_ in self.ids:
            # Global symbols

            # Name is needed for initialization
            # Should not be used by the programmer
            # Naming convention is by definition unique
            global_id_name = '{}_{}'.format(id_, self.symbol_table.auto(id_))
            global_id_cvalue = ir.GlobalVariable(
                self.module, self.type_.cvalue, name=global_id_name)

            # Set initializer to zeroinitializer ir.Constant(typ, None)
            global_id_cvalue.initializer = ir.Constant(self.type_.cvalue, None)

            # Internal linkage means that these variables are not accessible if
            # the module is imported
            global_id_cvalue.linkage = 'internal'

            var_entry = SymbolEntry(
                stype=self.type_.stype,
                name_type=NameType.N_VAR,
                cvalue=global_id_cvalue)

            # Register global symbol to symbol table
            self.symbol_table.insert(id_, var_entry, lineno=self.lineno)


class Label(Local):
    def __init__(self, ids, builder, module, symbol_table, lineno):
        super(Label, self).__init__(builder, module, symbol_table, lineno)
        self.ids = ids

    @AST.sem_decorator
    def sem(self):
        '''
            Register labels at the symbol table
        '''
        # Iterate over all names and register variables
        for id_ in self.ids:
            label_entry = SymbolEntry(
                stype=(
                    ComposerType.T_NO_COMP,
                    BaseType.T_LABEL),
                name_type=NameType.N_LABEL)
            self.symbol_table.insert(id_, label_entry, lineno=self.lineno)

    def codegen(self):
        pass


class Forward(Local):

    def __init__(self, header, builder, module, symbol_table, lineno):
        super(Forward, self).__init__(builder, module, symbol_table, lineno)
        self.header = header

    @AST.sem_decorator
    def sem(self):
        '''
            Registers forward declaration on symbol table
        '''
        if self.header.func_type:
            self.header.func_type.sem()
            header_type = self.header.func_type.stype
        else:
            header_type = (ComposerType.T_NO_COMP, BaseType.T_PROC)
        forward_entry = SymbolEntry(
            stype=header_type,
            name_type=NameType.N_FORWARD)
        self.symbol_table.insert('forward_' + self.header.id_, forward_entry, lineno=self.lineno)

        for formal in self.header.formals:
            formal.sem()
            for formal_id in formal.ids:
                formal_entry = SymbolEntry(
                    stype=formal.stype,
                    name_type=NameType.N_FORMAL,
                    by_reference=formal.by_reference)
                self.symbol_table.insert_formal(
                    'forward_' + self.header.id_, formal_id, formal_entry, lineno=self.lineno)

    def codegen(self):
        '''
            Registers declaration on the symbol table as a global function (ir.Function)
        '''
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

        header_counter = self.symbol_table.auto_header(self.header.id_)
        header_cvalue = ir.Function(
            self.module,
            header_type_cvalue,
            name=self.header.id_ + '_' + str(header_counter))

        header_cvalue.is_declaration = True

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

        self.symbol_table.insert('forward_' + self.header.id_, header_entry, lineno=self.lineno)


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

    @AST.sem_decorator
    def sem(self):
        '''
            Register function result at symbol table.
        '''
        if self.func_type:
            result_entry = SymbolEntry(
                stype=self.func_type.stype,
                name_type=NameType.N_VAR)
            self.symbol_table.insert('result', result_entry, lineno=self.lineno)

    def codegen(self):
        '''
            Register function result at symbol table.
        '''
        if self.func_type:
            self.func_type.codegen()
            result_ptr = self.builder.alloca(self.func_type.cvalue)
            result_entry = SymbolEntry(
                stype=self.func_type.stype,
                name_type=NameType.N_VAR, cvalue=result_ptr)
            self.symbol_table.insert('result', result_entry, lineno=self.lineno)

    def __eq__(self, other):
        if self.id_ != other.id_ or self.stype != other.stype:
            return False

        for formal_1, formal_2 in zip(self.formals, other.formals):
            if len(formal_1.ids) != len(formal_2.ids):
                return False

            if formal_1.type.stype != formal_2.type.stype:
                return False

        return True


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

    @AST.sem_decorator
    def sem(self):
        '''
            Check if formal parameter(s) are well defined.
            Arrays are not allowed to pass by value
        '''
        self.type_.sem()
        if self.type_.stype[0] in [
                ComposerType.T_CONST_ARRAY,
                ComposerType.T_VAR_ARRAY] and (
                not self.by_reference):
            msg = 'Arrays: {} are not allowed to pass by value'.format(', '.join(self.ids))
            self.raise_exception_helper(msg, PCLSemError)

        self.stype = self.type_.stype

    def codegen(self):
        pass


class Type(AST):

    def __init__(self, type_, builder, module, symbol_table, lineno):
        super(Type, self).__init__(builder, module, symbol_table, lineno)
        self.type_ = type_

    @AST.sem_decorator
    def sem(self):
        '''
            Set the semantic type to the provided signature.
        '''
        self.stype = (ComposerType.T_NO_COMP, BaseType(self.type_))

    def codegen(self):
        '''
            Generate type signature
        '''
        self.cvalue = LLVMTypes.mapping[self.type_]


class PointerType(Type):
    '''
        Declaration of a new pointer.
        Example: ^integer
    '''

    def __init__(self, type_, builder, module, symbol_table, lineno):
        super(
            PointerType,
            self).__init__(
            type_,
            builder,
            module,
            symbol_table,
            lineno)
        self.type_ = type_

    @AST.sem_decorator
    def sem(self):
        self.type_.sem()
        base_type = self.type_.stype
        self.stype = (ComposerType.T_PTR, base_type)

    def codegen(self):
        self.type_.codegen()
        self.cvalue = ir.PointerType(self.type_.cvalue)


class ArrayType(Type):

    def __init__(self, length, type_, builder, module, symbol_table, lineno):
        super(
            ArrayType,
            self).__init__(
            type_,
            builder,
            module,
            symbol_table,
            lineno)
        # Const array has length > 0 and var array has length = 0
        self.length = int(length)

    @AST.sem_decorator
    def sem(self):
        '''
            Infer type of array
            1. If length = 0 then declare a variable array
            2. If length > 0 then declare a constant array
        '''
        self.type_.sem()
        if self.length > 0:
            self.stype = (ComposerType.T_CONST_ARRAY, self.type_.stype)
        elif self.length == 0:
            self.stype = (ComposerType.T_VAR_ARRAY, self.type_.stype)
        else:
            msg = 'Negative length specified'
            self.raise_exception_helper(msg, PCLSemError)

    def codegen(self):
        '''
            Declare an LLVM type of [length x type]
        '''
        self.type_.codegen()
        self.cvalue = ir.ArrayType(self.type_.cvalue, self.length)


class Statement(AST):

    def __init__(self, builder, module, symbol_table, lineno, **kwargs):
        super(Statement, self).__init__(builder, module, symbol_table, lineno)
        self.name = kwargs.get('name', None)
        self.stmt = kwargs.get('stmt', None)

    @AST.sem_decorator
    def sem(self):
        '''
            Assert that label exists (if statement is named)
            and perform semantic analysis inside.
        '''
        if self.name:
            self.symbol_table.lookup(self.name, lineno=self.lineno)
            self.stmt.sem()

    def codegen(self):
        '''
            Register label inside the module (if statement is named)
            and generate code inside the statement.
        '''
        if self.name:
            # Declare labeled statement as a basic block
            self.cvalue = self.builder.append_basic_block(self.name)
            self.builder.branch(self.cvalue)
            label_entry = SymbolEntry(
                stype=(
                    ComposerType.T_NO_COMP,
                    BaseType.T_LABEL),
                name_type=NameType.N_LABEL,
                cvalue=self.cvalue)
            self.symbol_table.insert(self.name, label_entry, lineno=self.lineno)
            self.builder.position_at_start(self.cvalue)
            next_block = self.builder.append_basic_block()
            self.stmt.codegen()

            # Branch to next block
            self.builder.branch(next_block)
            self.builder.position_at_start(next_block)


class Block(Statement):

    def __init__(self, stmt_list, builder, module, symbol_table, lineno):
        super(Block, self).__init__(builder, module, symbol_table, lineno)
        self.stmt_list = stmt_list

    @AST.sem_decorator
    def sem(self):
        '''
            Perform semantic analysis on statements inside the block
            OPTIMIZATION NOTE: No scope need should be opened because
            every scope that contains local is the result of the following
            actions in PCL
                1. program
                2. function / procedure declaration
            If locals were allowed before every block then
            we should open an additional scope here.
        '''
        for stmt in self.stmt_list:
            stmt.sem()

    def codegen(self):
        '''
            Run codegen on statements.
        '''
        for stmt in self.stmt_list:
            stmt.codegen()


class Call(Statement):
    def __init__(self, id_, exprs, builder, module, symbol_table, lineno):
        super(Call, self).__init__(builder, module, symbol_table, lineno)
        self.id_ = id_
        self.exprs = exprs

    @AST.sem_decorator
    def sem(self):
        '''
            Search for function name and assert that the real parameters
            are compatible with the formal parameters.
        '''
        try:
            call_entry = self.symbol_table.lookup(self.id_, lineno=self.lineno)
        except PCLSymbolTableError:
            call_entry = self.symbol_table.lookup('forward_' + self.id_, lineno=self.lineno)
        except BaseException:
            msg = 'Name {} not found'.format(self.id_)
            self.raise_exception_helper(msg, PCLSemError)

        formals = list(self.symbol_table.formal_generator(self.id_))
        self.stype = call_entry.stype

        if len(formals) != len(self.exprs):
            msg = 'Invalid number of arguments: {}'.format(self.id_)
            self.raise_exception_helper(msg, PCLSemError)

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
                    msg = 'Incompatible assignment type: {}'.format(
                        formal_name)
                    self.raise_exception_helper(msg, PCLSemError)

    def codegen(self):
        '''
            Register the real parameters (flattened) and pass the required
            real parameters according to the formal parameters definitions
            and compatibility.
                1. Call by reference passes pointer (performs bitcast if needed
                    for example *[n x type] -> *[0 x type])
                2. Call by value passes expression codegen value
        '''
        real_params = []
        counter = 0
        try:
            call_entry_cvalue = self.symbol_table.lookup(self.id_, lineno=self.lineno).cvalue
        except PCLSymbolTableError:
            call_entry_cvalue = self.symbol_table.lookup(
                'forward_' + self.id_, lineno=self.lineno).cvalue,
        except BaseException:
            # Should never be reached
            msg = 'Unknown name: {}'.format(self.id_)
            self.raise_exception_helper(msg, PCLSemError)

        formals = self.symbol_table.formal_generator(self.id_)
        for expr, formal_type, (_, formal) in zip(
                self.exprs, call_entry_cvalue.args, formals):
            expr.codegen()
            if formal.by_reference:
                if not hasattr(expr, 'ptr'):
                    msg = 'Expression at position {} cannot be passed by reference'.format(counter)
                    self.raise_exception_helper(msg, PCLCodegenError)
                if expr.ptr:
                    ptr = expr.ptr
                    if ptr.type != formal_type.type:
                        ptr = self.builder.bitcast(ptr, formal_type.type)

                    real_params.append(ptr)
                else:
                    raise NotImplementedError()
            else:
                if isinstance(expr, StringLiteral):
                    ptr = expr.ptr
                    real_params.append(ptr)
                else:
                    real_params.append(expr.cvalue)

            counter += 1
        self.cvalue = self.builder.call(call_entry_cvalue, real_params)


class If(Statement):
    '''
        If statement.
    '''

    def __init__(
            self,
            expr,
            stmt,
            else_stmt,
            builder,
            module,
            symbol_table,
            lineno):
        super(If, self).__init__(builder, module, symbol_table, lineno)
        self.expr = expr
        self.stmt = stmt
        self.else_stmt = else_stmt

    @AST.sem_decorator
    def sem(self):
        '''
            Checks that the condition is a valid boolean and perform semantic
            analysis on then (and else if defined) statements.
        '''
        self.expr.sem()
        self.expr.type_check((ComposerType.T_NO_COMP, BaseType.T_BOOL))

        self.stmt.sem()
        if self.else_stmt:
            self.else_stmt.sem()

    def codegen(self):
        '''
            Creates code for the if statement using ir.IRBuilder's if_else or
            if_then commands.
        '''
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

    @AST.sem_decorator
    def sem(self):
        '''
            Similar to the if statement.
        '''
        self.expr.sem()
        self.expr.type_check((ComposerType.T_NO_COMP, BaseType.T_BOOL))
        self.stmt.sem()

    def codegen(self):
        '''
            Similar to the if statement.
            Phi nodes are not needed.
        '''
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

    @AST.sem_decorator
    def sem(self):
        '''
            Asserts that label is declared.
        '''
        label = self.symbol_table.lookup(self.id_, self.lineno, lineno=self.lineno, last_scope=True)
        if label.num_queries <= 1:
            self.raise_exception_helper('Undeclared Label: {}'.format(self.id_), PCLSemError)


    def codegen(self):
        '''
            Jumps to the declared label.
        '''
        # TODO fix non terminating block
        helper_block = self.builder.append_basic_block()
        self.builder.branch(helper_block)
        self.builder.position_at_start(helper_block)
        goto_block = self.symbol_table.lookup(self.id_, lineno=self.lineno).cvalue
        self.builder.branch(goto_block)
        next_block = self.builder.append_basic_block()
        self.builder.position_at_start(next_block)


class Return(Statement):
    '''
        Return statement.
    '''

    @AST.sem_decorator
    def sem(self):
        '''
            Asserts that in case of a function the result is set
            at least once.
        '''
        try:
            result_entry = self.symbol_table.lookup('result', lineno=self.lineno)
            if result_entry.num_queries <= 1:
                msg = 'Result must be set at least once'
                self.raise_warning_helper(msg)
        except PCLSymbolTableError:
            pass

    def codegen(self):
        '''
            Adds the return command (ret_void) for a function and
            returns "result" (with ret) for a function.
        '''
        return_block = self.builder.append_basic_block()
        self.builder.branch(return_block)
        self.builder.position_at_start(return_block)
        try:
            # Function
            result_cvalue_ptr = self.symbol_table.lookup('result', lineno=self.lineno).cvalue
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

    @AST.sem_decorator
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

    @AST.sem_decorator
    def sem(self):
        '''
            Assert that created types are compatible.
        '''
        self.lvalue.sem()
        if self.expr:
            if self.lvalue.stype[0] != ComposerType.T_PTR or self.lvalue.stype[1][0] != ComposerType.T_VAR_ARRAY:
                msg = 'Cannot create new instance of {}'.format(
                    self.lvalue.stype)
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
                msg = 'Cannot create new instance of {}'.format(
                    self.lvalue.stype)
                self.raise_exception_helper(msg, PCLSemError)

            # ^t -> t
            self.stype = self.lvalue.stype[1]

    def codegen(self):
        '''
            Creates a new value and sets lvalue's pointer to point there.
        '''
        self.lvalue.codegen()
        if self.expr:
            # Creates n x [0 x type]
            self.expr.codegen()
            self.cvalue = self.builder.alloca(self.lvalue.ptr.type.pointee.pointee, self.expr.cvalue)
        else:
            self.cvalue = self.builder.alloca(self.lvalue.ptr.type.pointee.pointee)
        self.builder.store(self.cvalue, self.lvalue.ptr)


class Dispose(Statement):
    '''
        Dispose statement.
    '''

    def __init__(
            self,
            lvalue,
            brackets,
            builder,
            module,
            symbol_table,
            lineno):
        super(Dispose, self).__init__(builder, module, symbol_table, lineno)
        self.lvalue = lvalue
        self.brackets = brackets

    @AST.sem_decorator
    def sem(self):
        '''
            Asserts that disposal is correct.
        '''
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
        '''
            Set lvalue to nil.
        '''
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
        super(
            IntegerConst,
            self).__init__(
            builder,
            module,
            symbol_table,
            lineno)
        self.value = int(value)

    @AST.sem_decorator
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

    @AST.sem_decorator
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
        self.value = ord(fix_escape(value))

    @AST.sem_decorator
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

    @AST.sem_decorator
    def sem(self):
        self.stype = (ComposerType.T_NO_COMP, BaseType.T_BOOL)

    def codegen(self):
        self.cvalue = ir.Constant(LLVMTypes.T_BOOL, self.value)


class Ref(RValue):
    '''
        Declares a pointer to an LValue. That is if
        t is integer then ^t is a pointer to an integer.
        Should not be reached
    '''

    def __init__(self, lvalue, builder, module, symbol_table, lineno):
        super(Ref, self).__init__(builder, module, symbol_table, lineno)
        self.lvalue = lvalue

    @AST.sem_decorator
    def sem(self):
        self.lvalue.sem()
        self.stype = (ComposerType.T_PTR, self.lvalue.stype)

    def codegen(self):
        self.builder.unreachable()

class Nil(RValue):
    '''
        The null pointer. Declared as a singleton.
    '''

    def __init__(self, builder, module, symbol_table, lineno):
        super(Nil, self).__init__(builder, module, symbol_table, lineno)

    @AST.sem_decorator
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

    @AST.sem_decorator
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

    @AST.sem_decorator
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

    @AST.sem_decorator
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

    @AST.sem_decorator
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
                # lhs_cvalue = self.builder.geptoint(self.lhs.cvalue, LLVMTypes.T_INT)
                # rhs_cvalue = self.builder.geptoint(self.rhs.cvalue, LLVMTypes.T_INT)
            self.cvalue = self.builder.icmp_signed(
                cmp_op, self.lhs.cvalue, self.rhs.cvalue)


class LogicOp(RValue):
    '''
        Logic operation between two sides (lhs, rhs)
    '''

    def __init__(self, op, lhs, rhs, builder, module, symbol_table, lineno):
        super(LogicOp, self).__init__(builder, module, symbol_table, lineno)
        self.op = op
        self.lhs = lhs
        self.rhs = rhs

    @AST.sem_decorator
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

    @AST.sem_decorator
    def sem(self):
        self.lvalue.sem()
        self.stype = (ComposerType.T_PTR, self.lvalue.stype)

    def codegen(self):
        self.lvalue.codegen()
        self.cvalue = self.symbol_table.lookup(self.lvalue.id_, lineno=self.lineno).cvalue


class LValue(Expr):
    '''
        Base class for the LValue
    '''

    def __init__(self, builder, module, symbol_table, lineno):
        super(LValue, self).__init__(builder, module, symbol_table, lineno)
        self.load = False
        self.ptr = None


class NameLValue(LValue):
    '''
        Named LValue: variable name (i.e. x)
    '''

    def __init__(self, id_, builder, module, symbol_table, lineno):
        super(NameLValue, self).__init__(builder, module, symbol_table, lineno)
        self.id_ = id_

    @AST.sem_decorator
    def sem(self):
        result = self.symbol_table.lookup(self.id_, lineno=self.lineno)
        self.stype = result.stype
        if self.load and result.num_queries <= 1:
            msg = 'Uniitialized lvalue: {}'.format(self.id_)
            self.raise_warning_helper(msg)

    def codegen(self):
        self.ptr = self.symbol_table.lookup(self.id_, lineno=self.lineno).cvalue
        # OPTIMIZE remove redundant loads
        if self.load:
            self.cvalue = self.builder.load(self.ptr)

    def set_nil(self):
        # Result is a pointer to our type e.g. for integer variable i32 it is
        # *i32
        result = self.symbol_table.lookup(self.id_, lineno=self.lineno).cvalue

        # Convert 0 to the pointee of the pointer (the actual type)
        nil = self.builder.inttoptr(
            LLVMConstants.ZERO_INT,
            result.type.pointee)

        # Store value to pointee
        self.builder.store(nil, result)


class Result(NameLValue):
    '''
        Holds the result of a function
    '''

    def __init__(self, builder, module, symbol_table, lineno):
        super(
            Result,
            self).__init__(
            'result',
            builder,
            module,
            symbol_table,
            lineno)

    @AST.sem_decorator
    def sem(self):
        result = self.symbol_table.lookup('result', lineno=self.lineno)
        self.stype = result.stype

    def codegen(self):
        self.ptr = self.symbol_table.lookup('result', lineno=self.lineno).cvalue

        if self.load:
            self.cvalue = self.builder.load(self.ptr)


class StringLiteral(LValue):
    '''
        Holds a node for a string literal
    '''

    def __init__(self, literal, builder, module, symbol_table, lineno):
        super(
            StringLiteral,
            self).__init__(
            builder,
            module,
            symbol_table,
            lineno)

        self.literal = fix_escape(literal) + '\0'
        self.length = len(self.literal)

    @AST.sem_decorator
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
        self.ptr = self.builder.alloca(self.cvalue.type)
        self.builder.store(self.cvalue, self.ptr)


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

    @AST.sem_decorator
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
        self.ptr = self.expr.cvalue
        self.cvalue = self.builder.load(self.expr.cvalue)


class SetExpression(LValue):
    '''
        Assignment of an expression to a name
    '''

    def __init__(self, lvalue, expr, builder, module, symbol_table, lineno):
        super(
            SetExpression,
            self).__init__(
            builder,
            module,
            symbol_table,
            lineno)
        self.lvalue = lvalue
        self.expr = expr

    @AST.sem_decorator
    def sem(self):
        self.expr.sem()
        self.lvalue.sem()

        # import pdb; pdb.set_trace()
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
            msg = 'Invalid set expression {} := {}'.format(
                str_type(self.lvalue.stype), str_type(self.expr.stype))
            self.raise_exception_helper(msg, PCLSemError)

    def codegen(self):
        self.expr.codegen()
        self.lvalue.codegen()

        if self.expr.stype[1] == BaseType.T_NIL:
            self.lvalue.set_nil()
        elif self.lvalue.ptr:
            if self.lvalue.stype == (
                    ComposerType.T_NO_COMP,
                    BaseType.T_REAL) and self.expr.stype == (
                    ComposerType.T_NO_COMP,
                    BaseType.T_INT):
                expr_cvalue = self.builder.sitofp(
                    self.expr.cvalue, LLVMTypes.T_REAL)
            else:
                expr_cvalue = self.expr.cvalue
            self.builder.store(expr_cvalue, self.lvalue.ptr)


class LBrack(LValue):
    '''
        ArrayElement
    '''

    def __init__(self, lvalue, expr, builder, module, symbol_table, lineno):
        super(LBrack, self).__init__(builder, module, symbol_table, lineno)
        self.lvalue = lvalue
        self.expr = expr

    @AST.sem_decorator
    def sem(self):
        self.expr.sem()
        self.expr.type_check((ComposerType.T_NO_COMP, BaseType.T_INT))
        self.lvalue.sem()

        if not isinstance(self.lvalue.stype[1], tuple):
            msg = 'Missing composer error {}[{}]'.format(
                self.lvalue.stype, self.expr.stype)
            self.raise_exception_helper(msg, PCLSemError)

        self.stype = self.lvalue.stype[1]

    def codegen(self):
        self.expr.codegen()
        self.lvalue.codegen()

        self.ptr = self.builder.gep(
            self.lvalue.ptr, [
                LLVMConstants.ZERO_INT, self.expr.cvalue])

        self.cvalue = self.builder.load(self.ptr)

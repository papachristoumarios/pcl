from enum import Enum
from itertools import product
from llvmlite import ir
from collections import deque, defaultdict, OrderedDict
from pcl.error import PCLSymbolTableError
from pcl.codegen import LLVMTypes


class BaseType(Enum):
    T_INT = 'integer'
    T_BOOL = 'boolean'
    T_REAL = 'real'
    T_CHAR = 'char'
    T_NIL = 'nil'
    T_PROC = 'procedure'
    T_FCN = 'function'
    T_LABEL = 'label'


class ComposerType(Enum):
    T_NO_COMP = 'T_NO_COMP'
    T_CONST_ARRAY = 'T_CONST_ARRAY'
    T_VAR_ARRAY = 'T_VAR_ARRAY'
    T_PTR = 'T_PTR'

def str_type(typ):
    if isinstance(typ, tuple):
        s = str_type(typ[1])
        if typ[0] == ComposerType.T_NO_COMP:
            return s
        if typ[0] == ComposerType.T_CONST_ARRAY:
            return 'array [] of ' + s
        elif typ[0] == ComposerType.T_VAR_ARRAY:
            return 'array of ' + s
        elif typ[0] == ComposerType.T_PTR:
            return '^ ' + s
    else:
        return typ.value

def is_composite(stype):
    return stype[0] != ComposerType.T_VAR_ARRAY


arithmetic_types = [(ComposerType.T_NO_COMP, BaseType.T_INT),
                    (ComposerType.T_NO_COMP, BaseType.T_REAL)]
real_type = (ComposerType.T_NO_COMP, BaseType.T_REAL)
int_type = (ComposerType.T_NO_COMP, BaseType.T_INT)


class MetaType:
    T_COMPLETE = 'complete'
    T_INCOMPLETE = 'incomplete'


class NameType(Enum):
    N_VAR = 'n_var'  # var x, result
    # label declaration (you define that a line will have this label)
    N_LABEL = 'n_label'
    # procedure declaration (does not return anything)
    N_PROCEDURE = 'n_procedure'
    # function declaration (returns at least something)
    N_FUNCTION = 'n_function'
    # forward header declaration (declare that function is recursive (in
    # header))
    N_FORWARD = 'n_forward'
    N_FORMAL = 'n_formal'


class SymbolEntry:
    def __init__(self, stype, name_type, cvalue=None, by_reference=False):
        self.stype = stype
        self.name_type = name_type
        self.offset = None
        self.num_queries = 0
        self.cvalue = cvalue
        self.by_reference = by_reference


class Builtin:

    def __init__(self, name, stype, func_type, name_type, arg_stypes=[]):
        self.name = name
        self.stype = stype
        self.func_type = func_type
        self.arg_stypes = arg_stypes
        self.name_type = name_type
        self.builtin_entry = SymbolEntry(
            stype=self.stype, name_type=self.name_type)
        self.builtin_formals = []
        for arg_stype in arg_stypes:
            by_reference = arg_stype[0] == ComposerType.T_VAR_ARRAY
            entry = SymbolEntry(
                stype=arg_stype,
                name_type=NameType.N_FORMAL,
                by_reference=by_reference)
            self.builtin_formals.append(entry)

    def __iter__(self):
        return iter([self.name, self.builtin_entry,
                     self.func_type, self.builtin_formals])

    @staticmethod
    def write_builtins():
        types = [
            'integer',
            'char',
            'real',
            'boolean',
        ]
        builtins = []

        for type_ in types:
            name = 'write' + type_.capitalize()
            name_type = NameType.N_PROCEDURE
            stype = (ComposerType.T_NO_COMP, BaseType.T_PROC)
            func_type = (LLVMTypes.T_PROC, [LLVMTypes.mapping[type_]])
            arg_stypes = [(ComposerType.T_NO_COMP, BaseType(type_))]
            builtin = Builtin(
                name=name,
                name_type=name_type,
                stype=stype,
                func_type=func_type,
                arg_stypes=arg_stypes)
            builtins.append(builtin)

        builtins.append(
            Builtin(
                name='writeString', stype=(
                    ComposerType.T_NO_COMP, BaseType.T_PROC), name_type=NameType.N_PROCEDURE, func_type=(
                    LLVMTypes.T_PROC, [
                        ir.ArrayType(
                            LLVMTypes.T_CHAR, 0).as_pointer()]), arg_stypes=[
                    (ComposerType.T_VAR_ARRAY, (ComposerType.T_NO_COMP, BaseType.T_CHAR))]))

        return builtins

    @staticmethod
    def read_builtins():
        types = [
            'integer',
            'char',
            'real',
            'boolean',
        ]
        builtins = []

        for type_ in types:
            name = 'read' + type_.capitalize()
            name_type = NameType.N_FUNCTION
            stype = (ComposerType.T_NO_COMP, BaseType(type_))
            func_type = (LLVMTypes.mapping[type_], [])
            arg_stypes = []
            builtin = Builtin(
                name=name,
                name_type=name_type,
                stype=stype,
                func_type=func_type,
                arg_stypes=arg_stypes)
            builtins.append(builtin)

        builtins.append(
            Builtin(
                name='readString', stype=(
                    ComposerType.T_NO_COMP, BaseType.T_PROC), name_type=NameType.N_PROCEDURE, func_type=(
                    LLVMTypes.T_PROC, [
                        LLVMTypes.T_INT, ir.ArrayType(
                            LLVMTypes.T_CHAR, 0).as_pointer()]), arg_stypes=[
                    (ComposerType.T_NO_COMP, BaseType.T_INT), (ComposerType.T_VAR_ARRAY, (ComposerType.T_NO_COMP, BaseType.T_CHAR))]))

        return builtins

    @staticmethod
    def math_builtins():
        math_fns = {
            ('real', 'real'): ['fabs', 'sqrt', 'sin', 'cos', 'tan', 'arctan', 'exp', 'ln'],
            ('integer', 'integer'): ['abs'],
            ('real', 'integer'): ['trunc', 'round'],
            ('char', 'integer'): ['ord'],
            ('integer', 'char'): ['chr'],
            (None, 'real'): ['pi']
        }
        builtins = []

        for func_type_names, func_names in math_fns.items():
            arg_type, ret_type = func_type_names
            for name in func_names:
                name_type = NameType.N_FUNCTION
                stype = (ComposerType.T_NO_COMP, BaseType(ret_type))
                try:
                    func_type = (
                        LLVMTypes.mapping[ret_type], [
                            LLVMTypes.mapping[arg_type]])
                except BaseException:
                    func_type = (LLVMTypes.mapping[ret_type], [])

                if arg_type:
                    arg_stypes = [(ComposerType.T_NO_COMP, BaseType(arg_type))]
                else:
                    arg_stypes = []

                builtin = Builtin(
                    name=name,
                    name_type=name_type,
                    stype=stype,
                    func_type=func_type,
                    arg_stypes=arg_stypes)

                builtins.append(builtin)

        return builtins


builtins = Builtin.write_builtins() + \
    Builtin.read_builtins() + \
    Builtin.math_builtins()


class Scope:
    def __init__(self, name):
        self.locals_ = {}
        self.globals = {}
        self.name = name

    def lookup(self, c, lineno=-1):
        return self.locals_.get(c, None)

    def insert(self, c, st, lineno=-1):
        if self.lookup(c, lineno=lineno):
            msg = 'Duplicate name {} {}'.format(c, 'at line {}'.format(lineno) if lineno > 0 else '')
            raise PCLSymbolTableError(msg)
        else:
            self.locals_[c] = st


class FormalScope:
    def __init__(self, name, offset=-1, size=0):
        self.locals_ = defaultdict(OrderedDict)
        self.name = name

    def lookup(self, h, c, lineno=-1):
        return self.locals_[h].get(c, None)

    def insert(self, h, c, st, lineno=-1):
        if self.lookup(h, c, lineno=lineno):
            msg = 'Duplicate name {} {}'.format(c, 'at line {}'.format(lineno) if lineno > 0 else '')
            raise PCLSymbolTableError(msg)
        else:
            self.locals_[h][c] = st


class SymbolTable:
    def __init__(self, module):
        self.module = module
        self.scopes = deque([])
        self.formals = deque([])
        self.scope_names_indices = deque([])
        self.autos = defaultdict(int)
        self.auto_headers = defaultdict(int)

        # scope for builtins
        self.open_scope()

        for builtin_name, builtin_entry, builtin_signature, formal_entries in builtins:
            if isinstance(builtin_signature[0], ir.VoidType):
                builtin_signature = (
                    ir.IntType(8).as_pointer(),
                    builtin_signature[1])

            builtin_signature_type = ir.FunctionType(*builtin_signature)
            builtin_fn = ir.Function(
                self.module,
                builtin_signature_type,
                name=builtin_name)
            builtin_entry.cvalue = builtin_fn
            self.insert(builtin_name, builtin_entry)

            for i, formal_entry in enumerate(formal_entries):
                self.insert_formal(builtin_name, '_{}'.format(i), formal_entry)

    def __del__(self):
        if len(self.scopes) > 1:
            raise PCLSymbolTableError('Open scope(s) not closed.')

        # close built-in scopes
        self.close_scope()

    def open_scope(self, name=None):
        scope = Scope(name=name)
        formal = FormalScope(name=name)
        self.scopes.append(scope)
        self.formals.append(formal)
        if name is not None:
            self.scope_names_indices.append(len(self.scopes) - 1)
        return scope

    def close_scope(self):
        if len(self.scopes) == 0:
            raise PCLSymbolTableError('Tried to pop nonexistent scope')
        if self.scopes[-1].name is not None:
            self.scope_names_indices.pop()
        self.scopes.pop()
        self.formals.pop()

    def lookup(self, c, lineno=-1, last_scope=False):
        if len(self.scopes) == 0:
            raise PCLSymbolTableError('Scopes do not exist')

        if last_scope:
            entry = self.scopes[-1].lookup(c, lineno=lineno)
            if entry:
                entry.num_queries += 1
                return entry
        else:
            for scope in reversed(self.scopes):
                entry = scope.lookup(c, lineno=lineno)
                if entry:
                    entry.num_queries += 1
                    return entry

        msg = 'Unknown name: {} at line {}'.format(c, lineno)
        raise PCLSymbolTableError(msg)

    def insert(self, c, t, lineno=-1):
        if len(self.scopes) == 0:
            raise PCLSymbolTableError('Scopes do not exist')

        self.scopes[-1].insert(c, t, lineno=lineno)

    def insert_formal(self, header, formal, t, lineno=-1):
        if len(self.formals) == 0:
            raise PCLSymbolTableError('Formals lists do not exist')
        self.formals[-1].insert(header, formal, t, lineno=lineno)

    def lookup_formal(self, header, formal, lineno=-1, last_scope=False):
        if len(self.formals) == 0:
            raise PCLSymbolTableError('Formal scopes do not exist')

        if last_scope:
            entry = self.formals[-1].lookup(header, formal, lineno=lineno)
            if entry:
                return entry
        else:
            for formal in reversed(self.formals):
                entry = formal.lookup(header, formal, lineno=lineno)
                if entry:
                    return entry

        msg = 'Unknown formal {} in header {} at line {}'.format(formal, header, lineno)
        raise PCLSymbolTableError(msg)

    def formal_generator(self, header_name):
        for formals_entry in reversed(self.formals):
            if header_name in formals_entry.locals_:
                for elem in formals_entry.locals_[header_name].items():
                    yield elem

    def auto(self, name):
        self.autos[name] += 1
        return self.autos[name]

    def auto_header(self, name):
        self.auto_headers[name] += 1
        return self.auto_headers[name]

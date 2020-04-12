from enum import Enum
from itertools import product
from collections import deque, defaultdict, OrderedDict
from pcl.error import PCLSymbolTableError


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

def is_composite(stype):
    return stype[0] != ComposerType.T_VAR_ARRAY

arithmetic_types = [(ComposerType.T_NO_COMP, BaseType.T_INT),
                         (ComposerType.T_NO_COMP, BaseType.T_REAL)]


class MetaType:
    T_COMPLETE = 'complete'
    T_INCOMPLETE = 'incomplete'

class NameType(Enum):
    N_VAR = 'n_var' # var x, result
    N_LABEL = 'n_label' # label declaration (you define that a line will have this label)
    N_PROCEDURE = 'n_procedure' # procedure declaration (does not return anything)
    N_FUNCTION = 'n_function' # function declaration (returns at least something)
    N_FORWARD = 'n_forward' # forward header declaration (declare that function is recursive (in header))
    N_FORMAL = 'n_formal'

class SymbolEntry:
    def __init__(self, stype, name_type):
        self.stype = stype
        self.name_type = name_type
        self.offset = None
        self.num_queries = 0


builtins = [('writeInteger',
             SymbolEntry(stype=(ComposerType.T_NO_COMP, BaseType.T_PROC),
                         name_type=NameType.N_PROCEDURE)),
            ('writeString',
             SymbolEntry(stype=(ComposerType.T_NO_COMP, BaseType.T_PROC),
                         name_type=NameType.N_PROCEDURE)),
            ('writeBoolean',
             SymbolEntry(stype=(ComposerType.T_NO_COMP, BaseType.T_PROC),
                         name_type=NameType.N_PROCEDURE)),
            ('writeChar',
             SymbolEntry(stype=(ComposerType.T_NO_COMP, BaseType.T_PROC),
                         name_type=NameType.N_PROCEDURE)),
           ]




class Scope:
    def __init__(self, name, offset=-1, size=0):
        self.locals_ = {}
        self.offset = offset
        self.size = size
        self.name = name

    def lookup(self, c):
        return self.locals_.get(c, None)

    def insert(self, c, st):
        if self.lookup(c):
            msg = 'Duplicate name {}'.format(c)
            raise PCLSymbolTableError(msg)
        else:
            st.offset = self.offset
            self.offset += 1
            self.locals_[c] = st
            self.size += 1

class FormalScope:
    def __init__(self, name, offset=-1, size=0):
        self.locals_ = defaultdict(OrderedDict)
        self.offset = offset
        self.size = size
        self.name = name

    def lookup(self, h, c):
        return self.locals_[h].get(c, None)

    def insert(self, h, c, st):
        if self.lookup(h, c):
            msg = 'Duplicate formal {}'.format(c)
            raise PCLSymbolTableError(msg)
        else:
            st.offset = self.offset
            self.offset += 1
            self.locals_[h][c] = st
            self.size += 1

class SymbolTable:
    def __init__(self):
        self.scopes = deque([])
        self.formals = deque([])
        self.scope_names_indices = deque([])

        # scope for builtins
        self.open_scope()

        for builtin_name, builtin_entry in builtins:
            self.insert(builtin_name, builtin_entry)

    def __del__(self):
        if len(self.scopes) > 1:
            raise PCLSymbolTableError('Open scope(s) not closed.')

        # close built-in scopes
        self.close_scope()

    def open_scope(self, name=None):
        if len(self.scopes) == 0:
            ofs = 0
            ofs_formal = 0
        else:
            ofs = self.scopes[-1].offset
            ofs_formal = self.formals[-1].offset
        scope = Scope(name=name, offset=ofs)
        formal = FormalScope(name=name, offset=ofs_formal)
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

    def lookup(self, c, last_scope=False):
        if len(self.scopes) == 0:
            raise PCLSymbolTableError('Scopes do not exist')

        if last_scope:
            entry = self.scopes[-1].lookup(c)
            if entry:
                entry.num_queries += 1
                return entry
        else:
            for scope in reversed(self.scopes):
                entry = scope.lookup(c)
                if entry:
                    entry.num_queries += 1
                    return entry

        msg = 'Unknown name: {}'.format(c)
        raise PCLSymbolTableError(msg)

    def insert(self, c, t):
        if len(self.scopes) == 0:
            raise PCLSymbolTableError('Scopes do not exist')

        self.scopes[-1].insert(c, t)

    def insert_formal(self, header, formal, t):
        if len(self.formals) == 0:
            raise PCLSymbolTableError('Formals lists do not exist')
        self.formals[-1].insert(header, formal, t)


    def lookup_formal(self, header, formal):
        if len(self.formals) == 0:
            raise PCLSymbolTableError('Formal scopes do not exist')

        if last_scope:
            entry = self.formals[-1].lookup(header, formal)
            if entry:
                return entry
        else:
            for formal in reversed(self.formals):
                entry = formal.lookup(header, formal)
                if entry:
                    return entry

        msg = 'Unknown formal {} in header {}'.format(formal, header)
        raise PCLSymbolTableError(msg)

    def formal_generator(self, header_name):
        for formals_entry in reversed(self.formals):
            if header_name in formals_entry.locals_:
                for elem in formals_entry.locals_[header_name].items():
                    yield elem

    def needs_forward_declaration(self, header):
        if len(self.scope_names_indices) == 0:
            return
        scope_index = self.scope_names_indices[-1]
        if self.scopes[scope_index].name == header:
            try:
                self.lookup('forward_' + header)
            except PCLSymbolTableError:
                msg = 'Expected forward declaration for header: {}'.format(header)
                raise PCLSymbolTableError(msg)

if __name__ == '__main__':
    pass

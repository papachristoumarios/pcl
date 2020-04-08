from enum import Enum
from itertools import product
from collections import deque, defaultdict
from error import PCLSymbolTableError


class BaseType(Enum):
    T_INT = 'integer'
    T_BOOL = 'boolean'
    T_REAL = 'real'
    T_CHAR = 'char'
    T_NIL = 'nil'
    T_PROC = 'procedure'
    T_FCN = 'function'


class ComposerType(Enum):
    T_NO_COMP = 'T_NO_COMP'
    T_CONST_ARRAY = 'T_CONST_ARRAY'
    T_VAR_ARRAY = 'T_VAR_ARRAY'
    T_PTR = 'T_PTR'


class MetaType:
    T_COMPLETE = 'complete'
    T_INCOMPLETE = 'incomplete'

class NameType(Enum):
    N_VAR = 'n_var'
    N_LABEL = 'n_label'
    N_PROCEDURE = 'n_procedure'
    N_FORWARD = 'n_forward'
    N_FORMAL = 'n_formal'



class SymbolEntry:
    def __init__(self, stype, name_type):
        self.stype = stype
        self.name_type = name_type
        self.offset = None

class Scope:
    def __init__(self, offset=-1, size=0):
        self.locals_ = {}
        self.offset = offset
        self.size = size

    def lookup(self, c):
        return self.locals_.get(c, None)

    def insert(self, c, st):
        if self.lookup(c):
            msg = 'Duplicate variable {}'.format(c)
            raise PCLSymbolTableError(msg)
        else:
            st.offset = self.offset
            self.offset += 1
            self.locals_[c] = st
            self.size += 1


class SymbolTable:
    def __init__(self):
        self.scopes = deque([])
        self.formals = defaultdict(dict)

    def open_scope(self):
        if len(self.scopes) == 0:
            ofs = 0
        else:
            ofs = self.scopes[-1].offset
        scope = Scope(offset=ofs)
        self.scopes.append(scope)
        return scope

    def close_scope(self):
        if len(self.scopes) == 0:
            raise PCLSymbolTableError('Tried to pop nonexistent scope')
        return self.scopes.pop()

    def lookup(self, c):
        if len(self.scopes) == 0:
            raise PCLSymbolTableError('Scopes do not exist')

        for scope in reversed(self.scopes):
            entry = scope.lookup(c)
            if entry:
                return entry

        msg = 'Unknown variable: {}'.format(c)
        raise PCLSymbolTableError(msg)

    def insert(self, c, t):
        if len(self.scopes) == 0:
            raise PCLSymbolTableError('Scopes do not exist')

        self.scopes[-1].insert(c, t)

    def insert_formal(self, header, formal, t):
        if not self.formals[header].get(formal, None):
            raise PCLSymbolTableError('Duplicate formal {} in header {}'.format(formal_name, header))

        self.formals[header][formal_name] = t

    def lookup_formal(self, header, formal):
        result = self.formals[header].get(formal, None)

        if result:
            return result
        else:
            raise PCLSymbolTableError('Unknown formal {} in header {}'.format(formal_name, header))


if __name__ == '__main__':
    pass

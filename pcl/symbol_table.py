from enum import Enum
from collections import deque

from pcl.error import PCLSymbolTableError

class BasicType(Enum):
    T_INT = 'int'
    T_BOOL = 'boolean'
    T_REAL = 'real'
    T_CHAR = 'char'

class Composer(Enum):
    T_NO_COMP = 'no_composer'
    T_CONST_ARRAY = 'const_array'
    T_VAR_ARRAY = 'var_array'
    T_PTR = 'ptr'

class SType:

    def __init__(self, basic_type, composer=Composer.T_NO_COMP):
        if not isinstance(basic_type, BasicType) or not isinstance(composer, Composer):
            raise PCLSymbolTableError('Invalid type')
        self.basic_type = basic_type
        self.composer = composer

    def __eq__(self, other):
        return self.basic_type == other.basic_type and self.composer == other.composer

class SymbolEntry:

    def __init__(self, stype, offset):
        self.stype = stype
        self.offset = offset

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
            self.locals_[c] = st
            self.offset += 1
            self.size += 1

class SymbolTable:

    def __init__(self):
        self.scopes = deque([])

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

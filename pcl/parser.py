from sly import Parser
from pcl.lexer import PCLLexer
from pcl.error import PCLParserError
from pcl.ast import *
from pcl.symbol_table import SymbolTable

class PCLParser(Parser):
    '''
        Contains the main functionality of the PCL Parser
        built with the SLY tool
    '''

    def __init__(self, builder=None, module=None, printf=None):
        '''
            Constructor for the PCL Parser

            Args:
                builder: LLVM IR code builder through codegen. Defaults to None
                module: LLVM module object
                printf: LLVM printf function
        '''
        self.builder = builder
        self.module = module
        self.printf = printf
        self.symbol_table = SymbolTable()

    # Tokens from PCLLexer
    tokens = PCLLexer.tokens

    O_equals O_greater O_less O_leq O_geq O_nequals

    # Associativity and priority of operators
    precedence = (
        ('left', 'EQUAL', 'GT', 'LT', 'GTE', 'LTE', 'NEG'),
        ('left', 'PLUS', 'MINUS', 'OR'),
        ('left', 'TIMES', 'FRAC', 'DIV', 'MOD',
        ('nonassoc', 'UN_OP'),
        ('nonassoc', 'BRACKETS'),
        ('nonassoc', 'RVALUE'),
        ('nonassoc', 'SINGLE_IF'),
        ('nonassoc', 'ELSE'))
    )

    def set_node_params(self, rule):
        '''
            Decorator to avoid writing tedious rules.
            Sets the module, builder and symbol_table of
            a node to the parser symbols (by ref)
        '''
        def wrapper():
            node = rule()
            node.builder = self.builder
            node.module = self.module
            node.symbol_table = self.symbol_table
            return node
        return wrapper

    def error(self, p):
        msg = 'Illegal rule {}'.format(str(p))
        raise PCLParserError(msg)

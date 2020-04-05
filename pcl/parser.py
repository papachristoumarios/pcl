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

    # Tokens from PCLLexer
    tokens = PCLLexer.tokens

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


    def error(self, p):
        msg = 'Illegal rule {}'.format(str(p))
        raise PCLParserError(msg)

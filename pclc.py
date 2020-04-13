import argparse
import sys

from pcl import PCLCError
from pcl import PCLLexer
from pcl import PCLParser
from pcl import PCLCodegen

__version__ = '0.0.1'

ABOUT_MSG = '''
    The PCL Language Compiler
    😷 Made with <3 during quarantine by (alphabetically)
        1. Giannis Daras <daras.giannhs@gmail.com>
        2. Marios Papachristou <papachristoumarios@gmail.com>
    Version: {}
    Repo 🌟 : https://github.com/papachristoumarios/pcl
    Docs 📖 : https://github.com/papachristoumarios/pcl/wiki
'''.format(__version__)


def get_argparser():
    argparser = argparse.ArgumentParser(usage=ABOUT_MSG)
    argparser.add_argument(
        'filename',
        nargs='?',
        default='',
        type=str,
        help='Input filename')
    argparser.add_argument('-O', default=0, type=int, help='Optimization level')
    argparser.add_argument(
        '-f',
        action='store_true',
        help='Input from stdin, bin output to stdout')
    argparser.add_argument(
        '-i',
        action='store_true',
        help='Input from stdin, IR output to stdout')
    argparser.add_argument(
        '-v',
        action='store_true',
        help='Output version'
    )
    return argparser

class PCLCDriver:

    def __init__(self, program):
        self.program = program
        self.lexer = PCLLexer()
        self.parser = PCLParser()

    def lex(self):
        self.tokens = self.lexer.tokenize(self.program)

    def parse(self):
        self.parsed = self.parser.parse(self.tokens)

    def pprint(self):
        self.parsed.pprint()

    def sem(self):
        self.parsed.sem()

    def codegen(self):
        self.parsed.codegen()

    def print_module(self):
        self.parsed.print_module()

if __name__ == '__main__':
    argparser = get_argparser()
    args = argparser.parse_args()

    if args.v:
        print(__version__)
        exit(0)
    else:
        if (args.filename != '') ^ args.i ^ args.f:
            if args.filename != '':
                with open(args.filename) as f:
                    program = f.read()
            else:
                program = sys.stdin.read()
        else:
            raise PCLCError('Multiple Inputs defined')
            exit(1)

    driver = PCLCDriver(program)

    pipeline = ['lex', 'parse', 'sem', 'pprint', 'print_module', 'pprint']


    pipeline_funcs = {
        'lex' : driver.lex,
        'parse' : driver.parse,
        'sem' : driver.sem,
        'pprint' : driver.pprint,
        'codegen' : driver.codegen,
        'print_module': driver.print_module
    }


    for stage in pipeline:
        pipeline_funcs[stage]()

    if args.f ^ args.i:
        exit(0)

    exit(0)

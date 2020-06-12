import argparse
import sys
import os
import warnings
from pcl import PCLCError, PCLError, exception_handler
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
    argparser.add_argument('-O', default=0, type=int,
                           help='Optimization level')
    argparser.add_argument(
        '--pipeline',
        nargs='+',
        default=[
            'lex',
            'parse',
            'sem',
            'codegen'])
    argparser.add_argument('-W', action='store_true', help='Enable warnings')
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
    argparser.add_argument(
        '--enable-traceback',
        action='store_true',
        help='Print the whole traceback (useful for debugging)'
    )
    return argparser


class PCLCDriver:

    def __init__(self, program):
        self.program = program
        self.lexer = PCLLexer()
        self.parser = PCLParser()
        self.parsed = None
        self.tokens = None

    def lex(self):
        self.tokens = self.lexer.tokenize(self.program)

    def parse(self):
        self.parsed = self.parser.parse(self.tokens)

    def pprint(self):
        if self.parsed:
            self.parsed.pprint()
        else:
            for token in self.tokens:
                print(token)

    def sem(self):
        self.parsed.sem()

    def codegen(self):
        self.parsed.codegen()

    def print_module(self):
        self.parsed.print_module()


if __name__ == '__main__':
    argparser = get_argparser()
    args = argparser.parse_args()

    if not args.enable_traceback:
        sys.tracebacklimit = 0

    if not args.W:
        warnings.simplefilter("ignore")

    if args.v:
        print(__version__)
        exit(0)
    else:
        if (args.filename != '') ^ args.i ^ args.f:
            if args.filename != '':
                with open(args.filename, encoding='unicode-escape') as f:
                    program = f.read()
            else:
                sys.stdin.reconfigure(encoding='unicode-escape')
                program = sys.stdin.read()
                args.filename = 'a.pcl'
        else:
            sys.stderr.write('Multiple Inputs defined\n')
            exit(1)

    driver = PCLCDriver(program)

    pipeline_funcs = {
        'lex': driver.lex,
        'parse': driver.parse,
        'sem': driver.sem,
        'pprint': driver.pprint,
        'codegen': driver.codegen,
    }

    for stage in args.pipeline:
        try:
            pipeline_funcs[stage]()

        except PCLError:
            msg = 'Invalid pipeline'
            raise PCLCError(msg)

    if 'codegen' == args.pipeline[-1]:
        driver.parser.codegen.postprocess_module(level=args.O)
        name = os.path.splitext(args.filename)[0]
        if args.i:
            # IR to stdout
            print(driver.parser.codegen.module)
        elif args.f:
            # Object file to stdout
            driver.parser.codegen.generate_outputs(name, llc_to_stdout=True)
        else:
            driver.parser.codegen.generate_outputs(name, llc_to_stdout=False)

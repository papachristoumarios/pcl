import argparse
import sys

from pcl.error import PCLCError
from pcl.lexer import PCLLexer
# from pcl.parser import PCLParser
from pcl.codegen import PCLCodegen

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
    argparser.add_argument(
        '--pipeline',
        nargs='+',
        default=['lex', 'parse', 'sem', 'codegen', 'bin'],
        help='Optional pipeline [lex, parse, sem, codegen, bin]')
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
        '-p',
        action='store_true',
        help='Input from stdin, pipeline output to stdout')
    argparser.add_argument(
        '-v',
        action='store_true',
        help='Output version'
    )
    return argparser


if __name__ == '__main__':
    argparser = get_argparser()
    args = argparser.parse_args()

    if args.v:
        print(__version__)
        exit(0)
    else:
        if (args.filename != '') ^ args.p ^ args.i ^ args.f:
            if args.filename != '':
                with open(args.filename) as f:
                    program = f.read()
            else:
                program = sys.stdin.read()
        else:
            raise PCLCError('Multiple Inputs defined')
            exit(1)

    lexer = PCLLexer()
    # parser = PCLParser()

    order = {
        'lex' : 0,
        'parse' : 1,
        'sem' : 2,
        'codegen' : 3,
        'bin' : 4
    }

    pipeline_funcs = {
        'lex' : lexer.tokenize,
        # 'parse' : parser.parse
    }

    args.pipeline.sort(key=lambda x: order[x])

    if any([order[args.pipeline[i]] != order[args.pipeline[i+1]] + 1 for i in range(len(args.pipeline) - 1)]):
        raise PCLCError('Broken Pipeline')


    program_stage = {-1: program}

    for component in args.pipeline:
        program_stage[component] = pipeline_funcs[component](program)
        program = program_stage[component]
        # verbose for now
        # print(str(list(program)))


    if args.p ^ args.f ^ args.i:
        print(str(list(program)))
        exit(0)

    exit(0)

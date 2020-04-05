import argparse
import sys

__version__ = '0.0.1'

ABOUT_MSG = '''
    The PCL Language Compiler
    Made with <3 during quarantine by (alphabetically)
        1. Giannis Daras <daras.giannhs@gmail.com>
        2. Marios Papachristou <papachristoumarios@gmail.com>
    Version: {}
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
        if args.filename != '' ^ args.p ^ args.i ^ args.f:
            if args.filename != '':
                with open(args.filename) as f:
                    program = f.read()
            else:
                program = sys.stdin.read()
        else:
            raise PCLCError('Multiple Inputs defined')
            exit(1)

    lexer = PCLLexer()
    parser = PCLParser()

    order = {
        'lex' : 0,
        'parse' : 1,
        'sem' : 2,
        'codegen' : 4,
        'bin' : 5
    }

    pipeline_funcs = {
        'lex' : lexer.tokenize
        'parse' : parser.parse
    }

    args.pipeline.sort(key=lambda x: order[x])

    program_stage = {-1: program}

    for component, func in args.pipeline:
        program_stage[component] = func(program)
        program = program_stage[component]
        # verbose for now
        print(program)

    #
    # if args.p ^ args.o ^ args.i:
    #     print(program)
    #     exit(0)

    exit(0)

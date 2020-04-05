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
    argparser.add_argument('-O', default=0, help='Optimization level')
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

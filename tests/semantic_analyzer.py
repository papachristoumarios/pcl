import os
import pytest
from pcl import PCLParser as Parser
from pcl import PCLLexer as Lexer
from pcl import PCLError, PCLSemError, PCLParserError, PCLSymbolTableError
import glob
import logging
lexer = Lexer()
parser = Parser()


pos_examples_folder = '../examples/pos/'
neg_examples_folder = '../examples/neg/'

valid_examples = glob.iglob(os.path.join(pos_examples_folder, "*.pcl"))

invalid_examples = glob.iglob(os.path.join(neg_examples_folder, "*.pcl"))


@pytest.mark.parametrize("filename", valid_examples)
def test_valid(filename):
    print('Running example: {}'.format(filename))
    with open(filename, 'r', encoding='ascii') as f:
        example = f.read()
    if example == '':
        return
    tokens = lexer.tokenize(example)
    program = parser.parse(tokens)
    program.pipeline()


@pytest.mark.parametrize("filename", invalid_examples)
def test_invalid(filename):
    print('Running example: {}'.format(filename))
    with open(filename, 'r', encoding='ascii') as f:
        example = f.read()
    if example == '':
        return
    try:
        tokens = lexer.tokenize(example)
        program = parser.parse(tokens)
        program.sem()
        assert 1 == 0, 'Negative program passed'
        print(example)
    except PCLSemError as e:
        print(e)
    except PCLSymbolTableError as e:
        print(e)
    except PCLError as e:
        raise e


if __name__ == '__main__':
    pytest.main(args=[os.path.abspath(__file__)])

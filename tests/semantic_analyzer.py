import os
import pytest
from pcl import PCLParser as Parser
from pcl import PCLLexer as Lexer
from pcl import PCLError, PCLSemError, PCLParserError
import glob
import logging
lexer = Lexer()
parser = Parser()


valid_examples = []
pos_examples_folder = '../examples/pos/'

invalid_examples = []
neg_examples_folder = '../examples/neg/'

for filename in glob.iglob(os.path.join(pos_examples_folder, "*.pcl")):
    with open(filename, 'r') as f:
        valid_examples.append(f.read())

for filename in glob.iglob(os.path.join(neg_examples_folder, "*.pcl")):
    with open(filename, 'r') as f:
        invalid_examples.append(f.read())




# def test_valid():
#     for example in valid_examples:
#         logging.log(logging.INFO, 'Running example: {}'.format(example))
#         tokens = lexer.tokenize(example)
#         program = parser.parse(tokens)
#         program.sem()

@pytest.mark.parametrize("example", invalid_examples)
def test_invalid(example):
    if example == '':
        return
    logging.log(logging.INFO, 'Running example: {}'.format(example))
    try:
        tokens = lexer.tokenize(example)
        program = parser.parse(tokens)
        program.sem()
        assert 1 == 0, 'Negative program passed'
    except PCLSemError as e:
        logging.log(logging.DEBUG, e)
    except PCLParserError as e:
        logging.log(logging.CRITICAL, e)
        assert 1 == 0, "Parser error"

if __name__ == '__main__':
    pytest.main(args=[os.path.abspath(__file__)])

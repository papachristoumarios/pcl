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



@pytest.mark.parametrize("example", valid_examples)
def test_valid(example):
    if example == '':
        return
    print('Running example: {}'.format(example))
    tokens = lexer.tokenize(example)
    program = parser.parse(tokens)
    program.pipeline()

@pytest.mark.parametrize("example", invalid_examples)
def test_invalid(example):
    if example == '':
        return
    print('Running example: {}'.format(example))
    try:
        tokens = lexer.tokenize(example)
        program = parser.parse(tokens)
        program.sem()
        assert 1 == 0, 'Negative program passed'
    except PCLError as e:
        print(e)

if __name__ == '__main__':
    pytest.main(args=[os.path.abspath(__file__)])

import os
import pytest
from pcl import PCLParser as Parser
from pcl import PCLLexer as Lexer
import glob
import logging
lexer = Lexer()
parser = Parser()


valid_examples = []
examples_folder = '../examples/'

for filename in glob.iglob(os.path.join(examples_folder, "*.pcl")):
    with open(filename, 'r') as f:
        valid_examples.append(f.read())


def test_valid():
    for example in valid_examples:
        logging.log(logging.INFO, 'Running example: {}'.format(example))
        tokens = lexer.tokenize(example)
        program = parser.parse(tokens)
        program.sem()
        program.pprint()

if __name__ == '__main__':
    pytest.main(args=[os.path.abspath(__file__)])

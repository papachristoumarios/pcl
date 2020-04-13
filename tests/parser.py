import pytest
import glob
import os
from pcl import PCLParser as Parser
from pcl import PCLLexer as Lexer
import pytest

lexer = Lexer()
parser = Parser()

valid_examples = []
examples_folder = '../examples/'

for filename in glob.iglob(os.path.join(examples_folder, "*.pcl")):
    with open(filename, 'r', encoding='unicode-escape') as f:
        valid_examples.append(f.read())


def test_valid():
    for example in valid_examples:
        tokens = lexer.tokenize(example)
        program = parser.parse(tokens)
        program.pprint()


if __name__ == '__main__':
    pytest.main(args=[os.path.abspath(__file__)])

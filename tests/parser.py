import pytest
import glob
import os
from pcl.parser import PCLParser as Parser
from pcl.lexer import PCLLexer as Lexer

lexer = Lexer()
parser = Parser()

valid_examples = []
examples_folder = '../examples/'

for filename in glob.iglob(os.path.join(examples_folder, "*.pcl")):
    with open(filename, 'r') as f:
        valid_examples.append(f.read())


def test_valid():
    for example in valid_examples:
        print(example)
        tokens = lexer.tokenize(example)
        print([x.value for x in tokens])
        program = parser.parse(tokens)
        program.pprint()

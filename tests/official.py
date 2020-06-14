import os
import pytest
from pcl import PCLParser as Parser
from pcl import PCLLexer as Lexer
from pcl import PCLError, PCLSemError, PCLParserError, PCLSymbolTableError
import glob
import logging
import subprocess
lexer = Lexer()
parser = Parser()


pos_examples_folder = '../examples/Correct/'
neg_examples_folder = '../examples/Wrong/'

valid_examples = glob.iglob(os.path.join(pos_examples_folder, "*.pcl"))

invalid_examples = glob.iglob(os.path.join(neg_examples_folder, "*.pcl"))


@pytest.mark.parametrize("filename", valid_examples)
def test_valid(filename):
    print('Running example: {}'.format(filename))
    result = subprocess.run(['pclc.py', filename], stderr=subprocess.DEVNULL, input=None, stdin=subprocess.DEVNULL)
    assert (result.returncode == 0)


@pytest.mark.parametrize("filename", invalid_examples)
def test_invalid(filename):
    print('Running example: {}'.format(filename))
    result = subprocess.run(['pclc.py', filename], stderr=subprocess.DEVNULL)
    assert (result.returncode != 0)

if __name__ == '__main__':
    pytest.main(args=[os.path.abspath(__file__)])

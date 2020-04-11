import pytest
from pcl import PCLLexer as Lexer
import pytest
import os


lexer = Lexer()

def tokenize(s):
    return [x.type for x in lexer.tokenize(s)]

def test_hello():
    s = '''
        program hello;
        begin
        writeString("hello")
        end.
        '''
    assert (tokenize(s) == ['PROGRAM', 'NAME', 'SEMICOLON', 'BEGIN', 'NAME', 'LPAREN', 'STRING', 'RPAREN', 'END', 'COLON'])


def test_collatz():
    # TODO: pass this test
    s = '''
    program collatz;

    label x, y;
    forward procedure hello();
    var x : integer;

    begin
      x := 6;
      while x > 1 do
      begin
        writeInteger(x);
        if x mod 2 = 0 then x := x div 2
        else x := 3 * x + 1;
      end;

    end.
    '''
    assert(tokenize(s) == ['PROGRAM', 'NAME', 'SEMICOLON', 'LABEL', 'NAME',
                           'COMMA', 'NAME', 'SEMICOLON', 'FORWARD',
                           'PROCEDURE', 'NAME', 'LPAREN', 'RPAREN',
                           'SEMICOLON', 'VAR', 'NAME', 'DCOLON', 'INTEGER',
                           'SEMICOLON', 'BEGIN', 'NAME', 'SET', 'INT_CONS',
                           'SEMICOLON', 'WHILE', 'NAME', 'GT', 'INT_CONS',
                           'DO', 'BEGIN', 'NAME', 'LPAREN', 'NAME', 'RPAREN',
                           'SEMICOLON', 'IF', 'NAME', 'MOD', 'INT_CONS',
                           'EQUAL', 'INT_CONS', 'THEN', 'NAME', 'SET', 'NAME',
                           'DIV', 'INT_CONS', 'ELSE', 'NAME', 'SET',
                           'INT_CONS', 'TIMES', 'NAME', 'PLUS', 'INT_CONS',
                           'SEMICOLON', 'END', 'SEMICOLON', 'END', 'COLON'])

def test_reverse():
    s = '''
        program reverse;
            function strlen (var s : array of char) : integer;
            begin
                result := 0;
                while s[result] <> 'c' do result := result + 1
            end;

            var r : array [32] of char;
            procedure reverse (var s : array of char);
            var i, l : integer;
            begin
                l := strlen(s);
                i := 0;
                while i < l do
                    begin
                        r[i] := s[l-i-1];
                        i := i+1
                    end;
                r[i] := "\0"
            end;

            begin
                reverse("\n!dlrow olleH");
                writeString(r)
            end.
    '''
    assert(tokenize(s) == ['PROGRAM', 'NAME', 'SEMICOLON', 'FUNCTION', 'NAME',
                           'LPAREN', 'VAR', 'NAME', 'DCOLON', 'ARRAY', 'OF',
                           'CHAR', 'RPAREN', 'DCOLON', 'INTEGER', 'SEMICOLON',
                           'BEGIN', 'RESULT', 'SET', 'INT_CONS', 'SEMICOLON',
                           'WHILE', 'NAME', 'LSQUARE', 'RESULT', 'RSQUARE',
                           'NEG', 'CHARACTER', 'DO', 'RESULT',
                           'SET', 'RESULT', 'PLUS', 'INT_CONS', 'END',
                           'SEMICOLON', 'VAR', 'NAME', 'DCOLON', 'ARRAY',
                           'LSQUARE', 'INT_CONS', 'RSQUARE', 'OF', 'CHAR',
                           'SEMICOLON', 'PROCEDURE', 'NAME', 'LPAREN', 'VAR',
                           'NAME', 'DCOLON', 'ARRAY', 'OF', 'CHAR', 'RPAREN',
                           'SEMICOLON', 'VAR', 'NAME', 'COMMA', 'NAME',
                           'DCOLON', 'INTEGER', 'SEMICOLON', 'BEGIN', 'NAME',
                           'SET', 'NAME', 'LPAREN', 'NAME', 'RPAREN',
                           'SEMICOLON', 'NAME', 'SET', 'INT_CONS', 'SEMICOLON',
                           'WHILE', 'NAME', 'LT', 'NAME', 'DO', 'BEGIN',
                           'NAME', 'LSQUARE', 'NAME', 'RSQUARE', 'SET',
                           'NAME', 'LSQUARE', 'NAME', 'MINUS', 'NAME',
                           'MINUS', 'INT_CONS', 'RSQUARE', 'SEMICOLON', 'NAME',
                           'SET', 'NAME', 'PLUS', 'INT_CONS', 'END',
                           'SEMICOLON', 'NAME', 'LSQUARE', 'NAME', 'RSQUARE',
                           'SET', 'STRING', 'END', 'SEMICOLON', 'BEGIN',
                           'NAME', 'LPAREN', 'STRING', 'RPAREN', 'SEMICOLON',
                           'NAME', 'LPAREN', 'NAME', 'RPAREN', 'END', 'COLON'])



if __name__ == '__main__':
    pytest.main(args=[os.path.abspath(__file__)])

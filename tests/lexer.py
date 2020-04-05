from pcl.lexer import PCLLexer as Lexer

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
    assert 1 == 0

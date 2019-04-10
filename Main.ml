
let main =
  let lexbuf = Lexing.from_channel stdin in
  try
    Parser.program Lexer.lexer lexbuf;
    exit 0
  with Parser.Error ->
    Printf.eprintf "PARSER ERROR: Syntax error at line: \n" ;
    exit 1

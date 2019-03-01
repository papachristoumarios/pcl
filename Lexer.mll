{
type token =
    | T_eof | T_integer_constant | T_real_constant | T_name
    | T_and | T_do | T_if | T_of | T_then
    | T_array | T_else | T_integer | T_or | T_true
    | T_begin | T_end | T_label | T_procedure | T_var
    | T_boolean | T_false | T_mod | T_program | T_while
    | T_char | T_forward | T_new | T_real
    | T_dispose | T_function | T_nil | T_result
    | T_div | T_goto | T_not | T_return
}

(* Building blocks for regular expressions *)
let digit = ['0'-'9']
let lowercase_letter = ['a' - 'z']
let upercase_letter = ['A' - 'Z']
let letter = ['a' - 'z' 'A'  - 'Z' ]
let white  = [' ' '\t' '\r' '\n']
let real_constant = digit+ ('.' digit+ (['E' 'e'] ['+' '-']? digit+)? )?
let name = letter (letter|digit|'_')*


(* Lexer *)
rule lexer = parse
    "and"         { T_and }
  | "do"          { T_do }
  | "if"          { T_if }
  | "of"          { T_of }
  | "then"        { T_then }
  | "array"       { T_array }
  | "else"        { T_else }
  | "integer"     { T_integer }
  | "or"          { T_or }
  | "true"        { T_true }
  | "begin"       { T_begin }
  | "end"         { T_end }
  | "label"       { T_label }
  | "procedure"   { T_procedure }
  | "var"         { T_var }
  | "boolean"     { T_boolean }
  | "false"       { T_false }
  | "mod"         { T_mod }
  | "program"     { T_program }
  | "while"       { T_while }
  | "char"        { T_char }
  | "forward"     { T_forward }
  | "new"         { T_new }
  | "real"        { T_real }
  | "dispose"     { T_dispose }
  | "function"    { T_function }
  | "nil"         { T_nil }
  | "result"      { T_result }
  | "div"         { T_div }
  | "goto"        { T_goto }
  | "not"         { T_not }
  | "return"      { T_return }

  (* Constants *)
  | digit+ { T_integer_constant }
  | real_constant { T_real_constant }

  (* Names *)
  | name         { T_name }

  | white+        { lexer lexbuf }

  | eof           { T_eof }

  |  _ as chr     { Printf.eprintf "invalid character: '%c' (ascii: %d)"
                      chr (Char.code chr);
                    lexer lexbuf }

{
  let string_of_token token =
    match token with
    | T_eof     -> "T_eof"
    | T_and     -> "T_and"
    | T_do      -> "T_do"
    | T_if      -> "T_if"
    | T_of      -> "T_of"
    | T_then    -> "T_then"
    | T_array   -> "T_array"
    | T_else    -> "T_else"
    | T_integer -> "T_integer"
    | T_or      -> "T_or"
    | T_true    -> "T_true"
    | T_begin   -> "T_begin"
    | T_end     -> "T_end"
    | T_label   -> "T_label"
    | T_procedure -> "T_procedure"
    | T_var     -> "T_var"
    | T_boolean -> "T_boolean"
    | T_false   -> "T_false"
    | T_mod     -> "T_mod"
    | T_program -> "T_program"
    | T_while   -> "T_while"
    | T_char    -> "T_char"
    | T_forward -> "T_forward"
    | T_new     -> "T_new"
    | T_real    -> "T_real"
    | T_dispose -> "T_dispose"
    | T_function-> "T_function"
    | T_nil     -> "T_nil"
    | T_result  -> "T_result"
    | T_div     -> "T_div"
    | T_goto    -> "T_goto"
    | T_not     -> "T_not"
    | T_return  -> "T_return"
    | T_integer_constant -> "T_integer_constant"
    | T_name -> "T_name"
    | T_real_constant -> "T_real_constant"

  let main =
    let lexbuf = Lexing.from_channel stdin in
    let rec loop () =
      let token = lexer lexbuf in
      Printf.printf "token=%s, lexeme=\"%s\"\n"
        (string_of_token token) (Lexing.lexeme lexbuf);
      if token <> T_eof then loop () in
    loop ()
}

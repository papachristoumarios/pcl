(*
  (C) Copyright 2019- Marios Papachristou and Ioannis Daras

  This file is part of PCL

  PCL is free software: you can redistribute it and/or modify
  it under the terms of the MIT License.

  PCL is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  LICENSE for more details.

  This file hosts the Lexer of PCL
*)

{
type token =
    | T_eof | T_integer_constant | T_real_constant | T_name | T_character | T_string
    | T_and | T_do | T_if | T_of | T_then
    | T_array | T_else | T_integer | T_or | T_true
    | T_begin | T_end | T_label | T_procedure | T_var
    | T_boolean | T_false | T_mod | T_program | T_while
    | T_char | T_forward | T_new | T_real
    | T_dispose | T_function | T_nil | T_result
    | T_div | T_goto | T_not | T_return
    | T_eq | T_gt | T_lt | T_gte | T_lte | T_neq  | T_plus | T_minus | T_times | T_frac | T_exp | T_ptr
    | T_lparen | T_rparen | T_set | T_semicolon | T_dot | T_comma | T_lsquare | T_rsquare | T_ddot
    | T_comment
}

(* Building blocks for regular expressions *)
let digit = ['0'-'9']
let lowercase_letter = ['a' - 'z']
let uppercase_letter = ['A' - 'Z']
let letter = lowercase_letter | uppercase_letter
let white  = [' ' '\t' '\r' '\n']
let real_constant = digit+ ('.' digit+ (['E' 'e'] ['+' '-']? digit+)? )?
let name = letter (letter|digit|'_')*
let escape_character = '\\' ['n' 't' 'r' '0' '\\' ''' '"']
let character = ''' (escape_character|_) '''
(* TODO: maybe this is allowed in string? *)
let string = '"' [^ '"']* '"'
let comment = '(''*' ([^ '*']+ | '*'+ [^ '*' ')'])* '*'+ ')'

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

  (* Chars and strings *)
  | character { T_character }
  | string    { T_string }



  (* Names *)
  | name     { T_name }


  (* Operators and arithmetic *)
  | '='      { T_eq }
  | '('      { T_lparen }
  | ')'      { T_rparen }
  | '+'      { T_plus }
  | '-'      { T_minus }
  | '*'      { T_times }
  | '/'      { T_frac }
  | '>'      { T_gt }
  | '<'      { T_lt }
  | '>''='   { T_gte }
  | '<''='   { T_lte }
  | '['      { T_lsquare }
  | ']'      { T_rsquare }
  | '^'      { T_exp }
  | '@'      { T_ptr }
  | '<''>'   { T_neq }

  (* Separators *)
  | ':' '='  { T_set }
  | ';'      { T_semicolon }
  | '.'      { T_dot }
  | ':'      { T_ddot }
  | ','      { T_comma }

  (* Whitespace and comments *)
  | comment       { T_comment }
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
    | T_character -> "T_character"
    | T_string  -> "T_string"
    | T_comment -> "T_comment"
    | T_eq      -> "T_eq"
    | T_lparen  -> "T_lparen"
    | T_rparen  -> "T_rparen"
    | T_plus    -> "T_plus"
    | T_minus   -> "T_minus"
    | T_times   -> "T_times"
    | T_frac    -> "T_frac"
    | T_gt      -> "T_gt"
    | T_lt      -> "T_lte"
    | T_gte     -> "T_gte"
    | T_lte     -> "T_lte"
    | T_lsquare -> "T_lsquare"
    | T_rsquare -> "T_rsquare"
    | T_exp     -> "T_exp"
    | T_ptr     -> "T_ptr"
    | T_set     -> "T_set"
    | T_semicolon -> "T_semicolon"
    | T_dot    -> "T_dot"
    | T_ddot   -> "T_ddot"
    | T_comma  -> "T_comma"
    | T_neq    -> "T_neq"


  let main =
    let lexbuf = Lexing.from_channel stdin in
    let rec loop () =
      let token = lexer lexbuf in
      Printf.printf "token=%s, lexeme=\"%s\"\n"
        (string_of_token token) (Lexing.lexeme lexbuf);
      if token <> T_eof then loop () in
    loop ()
}

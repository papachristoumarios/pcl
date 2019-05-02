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
  open Parser

  let num_lines = ref 1 ;;

  let get_lines = !num_lines ;;

}

(* Building blocks for regular expressions *)
let digit = ['0'-'9']
let lowercase_letter = ['a' - 'z']
let uppercase_letter = ['A' - 'Z']
let letter = lowercase_letter | uppercase_letter
let white  = [' ' '\t' '\r' ]
let newline = '\n'
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
  | digit+ { T_integer_constant (int_of_string (Lexing.lexeme lexbuf)) }
  | real_constant { T_real_constant (float_of_string (Lexing.lexeme lexbuf)) }

  (* Chars and strings *)
  | character { T_character (Lexing.lexeme lexbuf).[0] }
  | string    { T_string (Lexing.lexeme lexbuf) }



  (* Names *)
  | name     { T_name (Lexing.lexeme lexbuf) }


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
  | comment       { lexer lexbuf }
  | white+        { lexer lexbuf }
  | newline       { incr num_lines; lexer lexbuf }

  | eof           { T_eof }

  |  _ as chr     { Printf.eprintf "LEXER ERROR: Invalid character: '%c' (ascii: %d) at line %d"
                      chr (Char.code chr) !num_lines;
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
  | T_integer_constant _ -> "T_integer_constant"
  | T_name _ -> "T_name"
  | T_real_constant _ -> "T_real_constant"
  | T_character _ -> "T_character"
  | T_string _ -> "T_string"
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

  (* let lexer_run =
    let lexbuf = Lexing.from_channel stdin in
    let rec loop () =
      let token = lexer lexbuf in
      Printf.printf "token=%s, lexeme=\"%s\"\n"
        (string_of_token token) (Lexing.lexeme lexbuf);
      if token <> T_eof then loop () in
    loop () *)

}

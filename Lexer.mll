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

/*
  (C) Copyright 2019- Marios Papachristou and Ioannis Daras

  This file is part of PCL

  PCL is free software: you can redistribute it and/or modify
  it under the terms of the MIT License.

  PCL is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  LICENSE for more details.

  This file hosts the Lexer of PCL
*/

/* Tokens */
%token T_eof
%token T_integer_constant
%token T_real_constant
%token T_name
%token T_character
%token T_string
%token T_and
%token T_do
%token T_if
%token T_of
%token T_then
%token T_array
%token T_else
%token T_integer
%token T_or
%token T_true
%token T_begin
%token T_end
%token T_label
%token T_procedure
%token T_var
%token T_boolean
%token T_false
%token T_mod
%token T_program
%token T_while
%token T_char
%token T_forward
%token T_new
%token T_real
%token T_dispose
%token T_function
%token T_nil
%token T_result
%token T_div
%token T_goto
%token T_not
%token T_return
%token T_eq
%token T_gt
%token T_lt
%token T_gte
%token T_lte
%token T_neq
%token T_plus
%token T_minus
%token T_times
%token T_frac
%token T_exp
%token T_ptr
%token T_lparen
%token T_rparen
%token T_set
%token T_semicolon
%token T_dot
%token T_comma
%token T_lsquare
%token T_rsquare
%token T_ddot

/* Start symbol */
%start program

/* ttypes */
%type <unit> program

/* Precendencies & Associativity */
%nonassoc T_eq T_gt T_lt T_gte T_lte T_neq
%left T_plus T_minus T_or
%left T_times T_frac T_div T_mod T_and
%left NOT POS NEG
%right T_exp
%left T_ptr

%nonassoc SINGLE_IF
%nonassoc T_else

%%

program : T_program T_name T_semicolon body T_dot T_eof { () }

body : local* block { () }

local : T_var complex_ids complex_ids_list { () }
        | T_forward header T_semicolon { () }
        | header T_semicolon body T_semicolon { () }
        | T_label T_name id_list T_semicolon { () }

complex_ids : T_name id_list T_ddot ttype T_semicolon { () }

complex_ids_list : { () } | complex_ids complex_ids_list { () }

sep_id: T_comma T_name { () }

id_list: T_name sep_id* { () }


header : T_procedure T_name T_lparen formal_opt? T_rparen { () }
         | T_function T_name T_lparen formal_opt? T_rparen T_ddot ttype { () }

formal : T_var? T_name id_list T_ddot ttype { () }

formal_opt : formal sep_formal* { () }

sep_formal : T_semicolon formal { () }


/* TypeNode */
ttype : T_integer { () }
      | T_real { () }
      | T_boolean { () }
      | T_char { () }
      | T_array array_length_opt? T_of ttype { () }
      | T_exp ttype { () }

array_length_opt: T_lsquare T_integer_constant T_rsquare { () } /* done */

block : T_begin stmt stmt_list T_end { () } /* done */

stmt_list : { () } | T_semicolon stmt stmt_list { () }

/*  Statements */
stmt : { () }
      | l_value T_set expr { () } /* done */
      | block { () } /* done */
      | call { () } /* done */
      | if_stmt { () } /* done */
      | T_while expr T_do stmt { () } /* done */
      | T_name T_ddot stmt { () } /* done */
      | T_goto T_name { () } /* done */
      | T_return { () } /* done */
      | T_new new_stmt { () } /* done */
      | T_dispose dispose_stmt { () } /* done */


new_stmt : l_value { () } | T_lsquare expr T_rsquare  l_value { () } /* done */

dispose_stmt : l_value { () } | T_lsquare T_rsquare l_value { () } /* done */

if_stmt : T_if expr T_then stmt %prec SINGLE_IF { () } /* done */
      | T_if expr T_then stmt T_else stmt { () } /* done */

/* L-values and R-values */
l_value : T_name { () } /* Id */
        | T_result { () } /* Result */
        | T_string { () } /* ConstNode */
        | expr T_exp { () } /* Dref Expr */
        | l_value T_lsquare expr T_rsquare { () } /* TODO */

/*  Expressions */
expr :  T_integer_constant { () } /* ConstNode */
        | T_character { () } /* ConstNode */
        | l_value { () }
        | T_real_constant { () } /* ConstNode */
        | T_lparen expr T_rparen { () } /* Expr */
        | call { () } /* FunctionCall */
        | T_plus expr %prec POS { () } /* ArithmeticUnary */
        | T_minus expr %prec NEG { () } /* ArithmeticUnary */
        | T_not expr %prec NOT { () } /* BooleanUnary */
        | expr T_plus expr { () } /* ArithmeticBinary */
        | expr T_minus expr { () } /* ArithmeticBinary */
        | expr T_times expr { () } /* ArithmeticBinary */
        | expr T_frac expr { () } /* ArithmeticBinary */
        | expr T_div expr { () } /* ArithmeticBinary */
        | expr T_mod expr { () } /* ArithmeticBinary */
        | T_true { () } /* ConstNode */
        | T_false { () } /* ConstNode */
        | expr T_or expr { () } /* BooleanBinary */
        | expr T_and expr { () } /* BooleanBinary */
        | expr T_neq expr { () } /* BooleanBinary */
        | expr T_eq expr { () } /* BooleanBinary */
        | expr T_lt expr { () } /* BooleanBinary */
        | expr T_gt expr { () } /* BooleanBinary */
        | expr T_lte expr { () } /* BooleanBinary */
        | expr T_gte expr { () } /* BooleanBinary */
        | T_nil { () } /* ConstNode */

/* Calls */
call : T_name T_lparen expr_opt? T_rparen { () } /* FunctionCall */

expr_opt : expr sep_expr* { () } /* Create list of expressions */

sep_expr : T_comma expr { () } /* Expr */

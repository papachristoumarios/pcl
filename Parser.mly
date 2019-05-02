%{
  open Ast
%}
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

/* Types */
%type <Ast.body> program
%type <Ast.body> body
%type <Ast.local> local
%type <Ast.complex_ids> complex_ids
%type <Ast.header> header
%type <formal> formal
%type <formal> sep_formal
%type <formal list> formal_opt
%type <ttype> ttype
%type <int> array_length_opt

%type <expr> sep_expr
%type <expr list> expr_opt
%type <function_call> call
%type <expr> expr
%type <lvalue> l_value
%type <statement> if_stmt
%type <dispose_statement> dispose_stmt
%type <new_statement> new_stmt
%type <statement> stmt
%type <statement> sep_stmt
%type <Ast.block> block

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

program : T_program T_name T_semicolon body T_dot T_eof { $4 }

body : local* block { {local_list = $1; body_block = $2} }

local : T_var complex_ids complex_ids* { ComplexIds ($2 :: $3) }
        | T_forward header T_semicolon { ForwardHeader $2 }
        | header T_semicolon body T_semicolon { HeaderBody ($1, $3) }
        | T_label T_name id_list T_semicolon { IdList $3 }

complex_ids : T_name id_list T_ddot ttype T_semicolon { {id_list = $2; complex_ids_type = $4} }

sep_id: T_comma T_name { $2 }

id_list: T_name sep_id* { $1 :: $2 }


header : T_procedure T_name T_lparen formal_opt? T_rparen { {procedure = true; formal_list = $4; header_type = Void} }
         | T_function T_name T_lparen formal_opt? T_rparen T_ddot ttype { {procedure = false; formal_list =  $4; header_type = $7} }

formal : T_var? T_name id_list T_ddot ttype { {name = $2; id_list = $3; header_type = $5} } /* Formal */

formal_opt : formal sep_formal* { $1 :: $2 } /* FormalList */

sep_formal : T_semicolon formal { $2 }


/* TypeNode */
ttype : T_integer { Integer }
      | T_real { Real }
      | T_boolean { Boolean }
      | T_char { Char }
      | T_array array_length_opt? T_of ttype { {length = $2; arr_type = $4} }
      | T_exp ttype { {pointer_type = $2} }

array_length_opt: T_lsquare T_integer_constant T_rsquare { $2 }

block : T_begin stmt sep_stmt* T_end { $2 :: $3 }

sep_stmt : T_semicolon stmt { $2 }


/*  Statements */
stmt : { EmptyStatement }
      | l_value T_set expr { {s_lvalue=$1 ; s_expr=$3}}
      | block { Block $1 }
      | call { FunctionCall $1 }
      | if_stmt { IfStatement $1 }
      | T_while expr T_do stmt { {condition=$1 ; action=$4} }
      | T_name T_ddot stmt { {ddot_stmt = $3} }
      | T_goto T_name { {label = $2} }
      | T_return { Return }
      | T_new new_stmt { NewStatement $2 }
      | T_dispose dispose_stmt { DisposeStatement $2 }


new_stmt : l_value {$1} | T_lsquare expr T_rsquare  l_value {{expr = $2 ; value = $4}}

dispose_stmt : l_value { {square = false ; value = $1} }
      | T_lsquare T_rsquare l_value { {square = true; value = $3} }

if_stmt : T_if expr T_then stmt %prec SINGLE_IF { {simple_expr = $2 ; then_stmt = $4} }
      | T_if expr T_then stmt T_else stmt {{full_expr = $2; full_then_stmt = $4 ; else_stmt = $6} }

/* L-values and R-values */
l_value : T_name { Id $1}
        | T_result { Result }
        | T_string { Const $1 }
        | expr T_exp { Deref $1 }
        | l_value T_lsquare expr T_rsquare { {sq_lvalue=$1 ; sq_expr = $3}}

/*  Expressions */

constant : numeric_constant { NumericConstant $1 }
        | logical_constant { LogicalConst $1 }
        | T_character { CharacterConstant $1 }
        | T_nil { NullConstant }

numeric_constant :
          T_integer_constant { Int $1 } /* ConstNode */
        | T_real_constant { Real $1 }

logical_constant: T_true { Bool true }
        | T_false { Bool false }


expr :    constant { Constant $1 } /* ConstNode */
        | l_value { Lvalue $1 }
        | T_lparen expr T_rparen { $2 } /* Expr */
        /*| call { () } /* FunctionCall */
        | T_plus expr %prec POS { () } /* ArithmeticUnary */
        | T_minus expr %prec NEG { () } /* ArithmeticUnary */
        | T_not expr %prec NOT { () } /* BooleanUnary */
        | expr T_plus expr { () } /* ArithmeticBinary */
        | expr T_minus expr { () } /* ArithmeticBinary */
        | expr T_times expr { () } /* ArithmeticBinary */
        | expr T_frac expr { () } /* ArithmeticBinary */
        | expr T_div expr { () } /* ArithmeticBinary */
        | expr T_mod expr { () } /* ArithmeticBinary */
        | expr T_or expr { () } /* BooleanBinary */
        | expr T_and expr { () } /* BooleanBinary */
        | expr T_neq expr { () } /* BooleanBinary */
        | expr T_eq expr { () } /* BooleanBinary */
        | expr T_lt expr { () } /* BooleanBinary */
        | expr T_gt expr { () } /* BooleanBinary */
        | expr T_lte expr { () } /* BooleanBinary */
        | expr T_gte expr { () } /* BooleanBinary */

/* Calls */
call : T_name T_lparen expr_opt? T_rparen { {name = $1; args = $3} }

expr_opt : expr sep_expr* { $1 :: $2 }

sep_expr : T_comma expr { $2 }

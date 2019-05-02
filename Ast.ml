(*
  (C) Copyright 2019- Marios Papachristou and Ioannis Daras

  This file is part of PCL

  PCL is free software: you can redistribute it and/or modify
  it under the terms of the MIT License.

  PCL is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  LICENSE for more details.

  This file hosts the AST Data Types for the PCL Compiler
*)

let parse_opt_list l = match l with
  | None -> []
  | Some x -> x


(* Constants *)
type numeric_constant = Int of int | Real of float
type logical_constant = Bool of bool
type constant =
  | NumericConstant of numeric_constant
  | LogicalConstant of logical_constant
  | CharacterConstant of char
  | NullConstant

(* Operators *)
type bool_binary_operator = OR | AND | NEQ | EQ | LT | GT | LTE | GTE
type bool_unary_operator = NOT
type ar_binary_operator = PLUS | MINUS | TIMES | FRAC | DIV | MOD
type ar_unary_operator = SIGN_PLUS | SIGN_MINUS

(* L-Value *)
type lvalue =
  | Const of constant
  | Result
  | Deref of expr
  | Id of string
  | SquaredLvalue of squared_lvalue
  | String of string

and squared_lvalue = {sq_lvalue: lvalue; sq_expr: expr}

(* R-Value *)

and expr =
  | ArithmeticUnary of arithmetic_unary
  | ArithmeticBinary of arithmetic_binary
  | LogicalBinary of logical_binary
  | LogicalUnary of logical_unary
  | Lvalue of lvalue
  | FunctionCall of function_call
  | Constant of constant


and function_call = {name : string; args : expr list}

(* Arithmetic Expressions *)
and arithmetic_binary = {left_num: expr; op_num: ar_binary_operator; right_num: expr}
and arithmetic_unary = {unop_num: ar_unary_operator; operand_num: expr}

(* Logical Expressions *)
and logical_binary = {left_log: expr; op_log: bool_binary_operator; right_log: expr}
and logical_unary = {unop_log: bool_unary_operator; operand_log: expr}

(* Goto *)
type goto = {label: string}

(* Set *)
type set_statement = {s_lvalue : lvalue ; s_expr : expr}

(* Dispose *)
type dispose_statement = {square: bool;  value: lvalue}

(* New *)
type new_expr_statement = {expr : expr; value: lvalue}
type new_statement =
  | NewExprStatement of new_expr_statement
  | LValueStatement of lvalue

(* Statement *)
type statement =
  | SetStatement of set_statement
  | Block of block
  | FunctionCall of function_call
  | IfStatement of if_statement
  | WhileStatement of while_statement
  | NewStatement of new_statement
  | DDotStatement of ddot_statement
  | DisposeStatement of dispose_statement
  | GotoStatement of goto
  | Return
  | EmptyStatement

(* While *)
and while_statement = {condition : expr;  action : statement}

(* If Statement *)
and simple_if = {simple_expr : expr ; then_stmt: statement}
and full_if = {full_expr: expr ; full_then_stmt: statement ; else_stmt: statement}
and if_statement =
  | SimpleIf of simple_if
  | FullIf of full_if

and ddot_statement = {ddot_stmt : statement}

(* Block *)
and block = statement list

(* AST *)
type ast =
  | Expr of expr
  | Statement of statement

type ttype =
  | Integer
  | Real
  | Boolean
  | Char
  | Void
  | Array of array_ttype
  | Pointer of pointer

and array_ttype = {length: int; arr_type: ttype}

and pointer = {pointer_type: ttype}

(* Formals *)
type formal = {id_list : string list ; formal_type : ttype}

(* Header *)
type header = {procedure: bool; formal_list: formal list; header_type: ttype; }

(* Complex Ids *)
type complex_ids = {id_list: string list; complex_ids_type: ttype}

(* Body *)
type body = {local_list: local list; body_block: block}

(* Local *)
and local =
  | ForwardHeader of header
  | IdList of string list
  | HeaderBody of header * body
  | ComplexIds of complex_ids list

let print_block blk = Printf.eprintf "<Block>\n"

let print_local l = Printf.eprintf "<Local>"

let print_body b =
  Printf.eprintf "<Body>\n";
  List.iter print_local b.local_list ;
  print_block b.body_block ;

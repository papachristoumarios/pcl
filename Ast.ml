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

(* Constants *)
type numeric_constant = Int of int | Real of float
type logical_constant = Bool of bool
type constant =
  | NumericConst of numeric_constant
  | LogicalConst of logical_constant
  | CharacterConstant of char
  | NullConstant

(* Arithmetic Expressions *)
type arithmetic_binary = {left: numeric_constant; op: char; right: numeric_constant}
type arithmetic_unary = {op: char; operand: numeric_constant}
type arithmetic_expr =
  | ArithmeticUnary of arithmetic_unary
  | ArithmeticBinary of arithmetic_binary

(* Logical Expressions *)
type logical_binary = {left: logical_constant; op: char; right: logical_constant}
type logical_unary = {op: char; operand: logical_constant}
type logical_expr =
  | LogicalBinary of logical_binary
  | LogicalUnary of logical_unary

(* R-Value *)
type rvalue =
  | ArithmeticExpr of arithmetic_expr
  | LogicalExpr of logical_expr


(* L-Value *)
type lvalue =
  | Const of constant
  | Result
  | Deref of deref
  | Id of string
  | SquaredLvalue of squared_lvalue
and squared_lvalue = {sq_lvalue: lvalue; sq_expr: expr}
and deref = {variable: expr}
and expr =
  | Rvalue of rvalue
  | Lvalue of lvalue
  | FunctionCall of function_call

and function_call = {name : string; args : expr list}



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
  | Goto of goto
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
type formal = {name : string ; id_list : string list ; formal_type : ttype}

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

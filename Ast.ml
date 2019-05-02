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

type ast = expr | function_call | statement

type statement = SetStatement of set_statement
                 | Block of block
                 | FunctionCall of function_call
                 | IfStatement of if_statement
                 | WhileStatement of while_statement
                 | NewStatement of new_statement
                 | DDotStatement of ddot_statement
                 | DisposeStatement of dispose_statement
                 | Goto of goto
                 | Return
                 | EmptyStament

type if_statement = SimpleIf of simple_if | FullIf of full_if

type simple if = {expr : expr ; stmt: statement}
type full_if = {expr: expr ; stmt: statement ; else_stmt: statement}

type ddot_statement = {ddot_stmt : statement}


type set_statement = {s_lvalue : lvalue ; s_expr : expr}

type dispose_statement = {square: bool, value: lvalue}

type new_statement =  {expr : expr; value: lvalue} | l_value

type while_statement = {condition : expr;  action : statement}

type block = statement list

type lvalue = const_node | result | deref | Id of string

type result = {result : Id}

type deref = {variable: Id}

type function_call = {name : string; args : expr list}

type goto = {label: Id}

(* Constants *)
type numeric_constant = Int of int | Real of float
type logical_constant = Bool of bool
type constant = NumericConst of numeric_constant | LogicalConst of logical_constant

(* Arithmetic Expressions *)
type arithmetic_binexpr = {left: numeric_constant; op: char; right: numeric_constant}
type arithmetic_unexpr = {op: char; operand: numeric_constant}
type arithmetic_expr =
  | ArithmeticBinExpr of arithmetic_binexpr
  | ArithmeticUnExpr of arithmetic_unexpr

(* Logical Expressions *)
type logical_binexpr = {left: logical_constant; op: char; right: logical_constant}
type logical_unexpr = {op: char; operand: logical_constant}
type logical_expr =
  | LogicalBinExpr of logical_binexpr
  | LogicalUnExpr of logical_unexpr

(* R-Value *)
type rvalue =
  | ArithmeticExpr of arithmetic_expr
  | LogicalExpr of logical_expr

let main () =
    Printf.eprintf "D\n" ;;

let _ = Printexc.print main ()

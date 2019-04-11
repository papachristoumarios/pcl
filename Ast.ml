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

type id = Name of string

type arithmetic_binop =
          O_plus
        | O_minus
        | O_times
        | O_frac
        | O_div
        | O_mod

type arithmetic_unop =
          O_neg
        | O_pos

type logical_binop =
          O_eq
        | O_neq
        | O_gt
        | O_lt
        | O_gte
        | O_lte
        | O_or
        | O_and

type logical_unop = O_not

type lvalue_unop = O_ptr | O_deref


let main () =
    Printf.eprintf "D\n" ;;

let _ = Printexc.print main ()

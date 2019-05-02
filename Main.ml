(*
  (C) Copyright 2019- Marios Papachristou and Ioannis Daras

  This file is part of PCL

  PCL is free software: you can redistribute it and/or modify
  it under the terms of the MIT License.

  PCL is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  LICENSE for more details.

  This file hosts the driver program for the PCL compiler.
*)

open Ast 

let print_ast ast = print_body ast

let usage () = Printf.eprintf "usage: pcl [-l|-p|-h|-v]* <stream.pcl
    -l      Run Lexer
    -p      Run Parser
    -h      Display usage
    -v      Display version and credits\n"

let version () =
    Printf.eprintf "PCL Compiler version 1.0
Created by:
    Marios Papachristou <papachristoumarios@gmail.com>
    Ioannis Daras <daras.giannhs@gmail.com>
Source Code: https://github.com/papachristoumarios/pcl\n"

let parse () =
  let lexbuf = Lexing.from_channel stdin in
  try
    let ast = Parser.program Lexer.lexer lexbuf in print_ast ast;
    exit 0
  with Parser.Error ->
    Printf.eprintf "PARSER ERROR: Syntax error at line: %d\n" !Lexer.num_lines;
    exit 1

let lex () =
    let lexbuf = Lexing.from_channel stdin in
    let rec loop () =
      let token = Lexer.lexer lexbuf in
        Printf.printf "token=%s, lexeme=\"%s\"\n"
        (Lexer.string_of_token token) (Lexing.lexeme lexbuf);
      if token <> Parser.T_eof then loop () in
    loop ()

let main =
    for i = 1 to Array.length Sys.argv - 1 do
      if Sys.argv.(i) = "-h" then usage ()
      else if Sys.argv.(i) = "-v" then version ()
      else if Sys.argv.(i) = "-p" then parse ()
      else if Sys.argv.(i) = "-l" then lex ()
    done;;

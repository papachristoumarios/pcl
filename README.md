# PCL

Compiler for the PCL Language written in [OCaml](http://www.ocaml.org/).

This is part of the semester assignment for [_Compilers_](https://courses.softlab.ntua.gr/compilers/2019a/) course taught in ECE NTUA (Spring 2018-2019).

## :busts_in_silhouette: Authors

This compiler would have never been born without the orderly contributions of its authors
  * Marios Papachristou ([papachristoumarios](https://github.com/papachristoumarios))
  * Ioannis Daras ([giannisdaras](https://github.com/giannisdaras))

---

## :tomato: What is PCL?

PCL is a imperative programming language based on a proper subset of ISO PASCAL, among with some changes. The basic characteristics of PCL include:

1. Syntax similar to PASCAL
2. Structured functions similar to PASCAL
3. Basic data types for integers and real numbers, booleans and characters
4. Arrays of fixed or variable size
5. Built-in function library

The complete PCL specification is available under `docs/specification.pdf`.

## :nut_and_bolt: Setup

The compiler comes with a `Makefile` for installation. Install it via

```bash
make depend
make
sudo make install
```

For a user specific installation you can use
```bash
make install INSTALL_PREFIX=/home/user/.local
```

## :hammer: Usage

After you have set up PCL you can use the `pcl` executable of the PCL compiler.
You can display the usage of `pcl` via
```bash
./pcl -h
```

The `pcl` executable allows the use of its constituent parts independently. Such parts include

1. The lexer
2. The parser (printing the AST)
3. The semantic analyzer
4. The codegen module

## :tv: Technological Stack

This implementation of PCL is developed using the OCaml language and the following meta-programs

1. ocamllex for lexical analysis
2. menhir for parsing
3. LLVM backend for OCaml

## Contributing to the project 

If you want to contribute to the project, please submit a pull request. 

## Documentation

The PCL documentation is located at `docs/` and the [wiki](https://github.com/papachristoumarios/pcl/wiki)

## References 

If you want to dive deeper into our compiler we advise you study the following references

1. Ullman, Jeffrey D., and Alfred V. Aho. "Principles of compiler design." Reading: Addison Wesley (1977).
2. Skordalakis, Manolis, and Papaspyrou,  Nikolaos. "Compilers". Symmetria Publications (2003 - in Greek) 
3. PCL Specification under `docs/specification.pdf` (in Greek) 

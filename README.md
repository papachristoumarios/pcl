# PCL

[![Build Status](https://travis-ci.com/papachristoumarios/pcl.svg?token=DxqFuX4UzFjiGRipqjph&branch=master)](https://travis-ci.com/papachristoumarios/pcl)

Compiler for the PCL Language written in [Python](http://www.python.org/).

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

The complete PCL specification is available under `docs/pcl2019.pdf` (in Greek).

## :nut_and_bolt: Setup

The compiler comes with a `Makefile` for installation. Install it via

```bash
make depend
make compiler
```

Please note that PCL compiler requires Python **>=3.6** to work since it has metaprogramming features (due to SLY) to specify lexers and parsers. Older versions **won't** work. 

## :hammer: Usage

After you have set up PCL you can use the `pcl` executable of the PCL compiler.
You can display the usage of `pcl` via
```bash
pclc.py --help
```

The `pcl` executable allows the use of its constituent parts independently. Such parts include

1. The lexer
2. The parser
3. The semantic analyzer
4. The codegen module

## :tv: Technological Stack

This implementation of PCL is developed using the Python language and the following meta-programs

1. [SLY](https://github.com/dabeaz/sly) for lexing and parsing
2. [llvmlite](https://llvmlite.readthedocs.io/en/latest/) for IR generation
3. LLVM for producing the object files

## Contributing to the project 

If you want to contribute to the project, please submit a pull request. 

## Documentation

The PCL documentation is located at `docs/` and the [wiki](https://github.com/papachristoumarios/pcl/wiki).
You can generate the API docs from the docstrings via 
```
pydoc pcl.submodule
```

where `submodule` is one of the submodules inside `pcl/`.

## Tests

The PCL Language comes with tests built-in for every "independent" part of the compiler. The tests are located in the `tests/` directory and the examples used in the `examples/` directory. You will need `pytest` to run them.  You can run the tests via
```bash
cd tests/ && pytest *
```

## References 

If you want to dive deeper into our compiler we advise you study the following references

1. Ullman, Jeffrey D., and Alfred V. Aho. "Principles of compiler design." Reading: Addison Wesley (1977).
2. Skordalakis, Manolis, and Papaspyrou,  Nikolaos. "Compilers". Symmetria Publications (2003 - in Greek). 
3. PCL Specification under `docs/pcl2019.pdf` (in Greek). 
4. `llvmlite` Reference Manual.
5. `SLY` Reference Manual.

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

After you have set up PCL you can use the `pclc.py` executable of the PCL compiler.
You can display the usage of `pclc.py` via

```bash
pclc.py --help
```

The `pcl` executable allows the use of its constituent parts independently. Such parts include

1. The lexer
2. The parser
3. The semantic analyzer
4. The codegen module



#### Compile PCL programs

For instance assume that you have the following PCL program under `example.pcl`

```pascal
program dummmy;
	var x: integer;
begin
	x := 0;
	while x < 10 do
	begin
		writeInteger(x);
		writeChar('\n');
		x := x + 1;
	end;
end.
```

which prints the numbers 0 to 9. Running

```bash
pclc.py example.pcl
```

will produce IR code at `example.imm` , the object file at `example.o` and the final (linked) executable at `example.out`.  If you specify the flag `-i` then the program should be read from `stdin` and the IR will be emitted to `stdout` . So the PCL compiler should be called as 

```bash
pclc.py -i <example.pcl >example.imm
```

If one wants to create an object file, he could use UNIX pipes

```bash
pclc.py -i <example.pcl | llc -filetype=obj >example.o
```

Compiling and linking the final can be separately done with the use of `gcc`. If one wants static linking with the `pcl/builtins.h` library then one should use

```bash
gcc -Wall -Werror -fpic -lm example.o /path/to/builtins.c/builtins.c -o example.out 
```

Note that builtins depend on `stdio.h` and `math.h` so the flag `-lm` is used to do dynamic linking with the math library. If one wants to perform dynamic linking with `pcl/libbuiltins.so` one should use

```bash
gcc -Wall -Werror -fpic -lm -L/path/to/libbuiltins.so -lbuiltins example.o -o example.out
```

Again, if one wants to use pipes, it is possible via the `-x` option as 

```bash
pclc.py -i <example.pcl | llc -filetype=obj | gcc -Wall -Werror -fpic -lm -L/path/to/libbuiltins.so -lbuiltins -o example.out -x -
```

The `pclc.py` executable produces verified LLVM code, throwing an exception otherwise. Successful compilation exits with code 0.  

Furthermore one can specify optimization flags using the `-O` argument. More specifically the acceptable values are 0, 1 and 2 according to the [LLVM Reference](https://llvm.org/doxygen/classllvm_1_1PassManagerBuilder.html) for `PassManagerBuilder`. For a complete and fathomable list on the LLVM optimizations performed by the optimizer, we redirect the interested reader to this [StackOverflow thread](https://stackoverflow.com/questions/15548023/clang-optimization-levels). 



#### Test individual parts of PCL

For testing individual parts of the compiler, one has to specify the `--pipeline` argument as a list containing a subset of the following (in correct order) arguments:

* `lex` to invoke the lexer
* `parse` to invoke the parser
* `sem` to invoke the semantic analyzer
* `codegen` to invoke the codegen module
* `pprint` to print the (annotated) AST to **stdout**. 

So in case one wants to do lexical analysis only

```bash
pclc.py example.pcl --pipeline lex pprint
```

to get the tokens to stdout. If one wants to do lexing, parsing and semantic analysis (type checking, label checking) and get the types of the compatible AST nodes.  

```bash
pclc.py example.pcl --pipeline lex parse sem pprint
```

More information on the design of the current compiler can be found at the wiki. 



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
make test
```

## References 

If you want to dive deeper into our compiler we advise you study the following references

1. Ullman, Jeffrey D., and Alfred V. Aho. "Principles of compiler design." Reading: Addison Wesley (1977).
2. Skordalakis, Manolis, and Papaspyrou,  Nikolaos. "Compilers". Symmetria Publications (2003 - in Greek). 
3. PCL Specification under `docs/pcl2019.pdf` (in Greek). 
4. `llvmlite` Reference Manual.
5. `SLY` Reference Manual.

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

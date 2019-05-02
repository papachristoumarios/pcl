  # (C) Copyright 2019- Marios Papachristou and Ioannis Daras
  #
  # This file is part of PCL
  #
  # PCL is free software: you can redistribute it and/or modify
  # it under the terms of the MIT License.
  #
  # PCL is distributed in the hope that it will be useful,
  # but WITHOUT ANY WARRANTY; without even the implied warranty of
  # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  # LICENSE for more details.
  #
  # This file hosts the Makefile of PCL


ifdef OS
   EXE=.exe
else
   EXE=
endif

CP=cp
INSTALL_PREFIX=/usr/local

OCAMLC_FLAGS=-g
OCAMLC=ocamlc
OCAMLDEP=ocamldep


%.cmo: %.ml %.mli
	$(OCAMLC) $(OCAMLC_FLAGS) -c $<

%.cmi: %.mli
	$(OCAMLC) $(OCAMLC_FLAGS) -c $<

%.cmo %.cmi: %.ml
	$(OCAMLC) $(OCAMLC_FLAGS) -c $<

pcl$(EXE): Lexer.cmo Parser.cmo Ast.cmo Main.cmo 
	$(OCAMLC) $(OCAMLC_FLAGS) -o $@ $^

Lexer.ml: Lexer.mll
	ocamllex -o $@ $<

Parser.ml Parser.mli: Parser.mly
	menhir -v Parser.mly

.PHONY: clean distclean

-include .depend

depend: Lexer.ml Lexer.mli Parser.ml Parser.mli Ast.ml Main.ml
	$(OCAMLDEP) $^ > .depend

clean:
	$(RM) Lexer.ml Parser.ml Parser.mli Parser.output *.cmo *.cmi *~


install:
	$(CP) pcl$(EXE) $(INSTALL_PREFIX)/bin/pcl$(EXE)
	chmod +x $(INSTALL_PREFIX)/bin/pcl$(EXE)

uninstall: $(INSTALL_PREFIX)/bin/pcl$(EXE)
	$(RM) $(INSTALL_PREFIX)/bin/pcl$(EXE)

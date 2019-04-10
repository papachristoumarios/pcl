# PCL Makefile
# Authors:
#		1. Marios Papachristou
#		2. Ioannis Daras

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

pcl$(EXE): Lexer.cmo Parser.cmo Main.cmo
	$(OCAMLC) $(OCAMLC_FLAGS) -o $@ $^

Lexer.ml: Lexer.mll
	ocamllex -o $@ $<

Parser.ml Parser.mli: Parser.mly
	ocamlyacc -v Parser.mly

.PHONY: clean distclean

-include .depend

depend: Lexer.ml Lexer.mli Parser.ml Parser.mli Main.ml
	$(OCAMLDEP) $^ > .depend

clean:
	$(RM) Lexer.ml Parser.ml Parser.mli Parser.output *.cmo *.cmi *~


install:
	$(CP) pcl$(EXE) $(INSTALL_PREFIX)/bin/pcl$(EXE)
	chmod +x $(INSTALL_PREFIX)/bin/pcl$(EXE)

uninstall: $(INSTALL_PREFIX)/bin/pcl$(EXE)
	$(RM) $(INSTALL_PREFIX)/bin/pcl$(EXE)

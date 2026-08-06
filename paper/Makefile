# Build the Recursive Observability Filter paper.
#
#   make            -> main.pdf
#   make figures    -> regenerate figures 5-10 from the simulator
#   make clean      -> remove LaTeX build artefacts
#   make distclean  -> also remove generated figures and main.pdf
#
# Uses the plain pdflatex/bibtex sequence rather than latexmk, because
# latexmk requires Perl, which a stock MiKTeX installation does not provide.

PYTHON ?= python
LATEX  ?= pdflatex --enable-installer -interaction=nonstopmode -halt-on-error
BIBTEX ?= bibtex

SECTIONS := $(wildcard sections/*.tex)
FIGURES  := $(wildcard figures/*.pdf)

.PHONY: all figures clean distclean

all: main.pdf

main.pdf: main.tex refs.bib $(SECTIONS) $(FIGURES)
	$(LATEX) main.tex
	$(BIBTEX) main
	$(LATEX) main.tex
	$(LATEX) main.tex

figures:
	$(PYTHON) make_figures.py

clean:
	rm -f *.aux *.bbl *.blg *.log *.out *.fls *.fdb_latexmk *.toc sections/*.aux

distclean: clean
	rm -f main.pdf js_dump.json figures/fig0*.pdf figures/fig1*.pdf

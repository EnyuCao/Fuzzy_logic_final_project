FNAME?=group_09_finalreport
BNAME?=mybibfile

pdf: $(FNAME).tex $(BNAME).bib
	make raw
	make clean

raw: $(FNAME).tex $(BNAME).bib
	pdflatex $(FNAME).tex
	bibtex $(FNAME).aux
	pdflatex $(FNAME).tex
	pdflatex $(FNAME).tex

clean:
	rm -f *~ *.aux *.bbl *.blg *.log *.out *.run.xml *-blx.bib

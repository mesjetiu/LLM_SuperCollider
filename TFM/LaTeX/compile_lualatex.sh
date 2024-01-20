#!/bin/bash

# Este script compilará el documento principal del proyecto en lualatex y generará el pdf final. Incluye la generación de la bibliografía y el índice.

bibtex main
lualatex main.tex
makeindex main
bibtex main.aux
makeglossaries main
lualatex main.tex
lualatex main.tex

# Makefile for EurocodePy

This file is used to show how to build the EurocodePy package and generate documentation.
It assumes that you have the necessary tools installed, such as `uv` for building and `mkdocs` for documentation.

## Build the package

uv build

## Create documentation for EurocodePy

### install packages

uv add mkdocs, mkdocs-material, mkdocstrings, mkdocstrings-python

### create documentation

cd mkdocs
mkdocs build
commit to github
mkdocs gh-deploy

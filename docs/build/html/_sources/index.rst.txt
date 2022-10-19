.. eurocodepy documentation master file, created by
   sphinx-quickstart on Sun Feb 13 19:18:00 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to eurocodepy's docs!
=============================

Eurocodepy are Python functions to work with structural eurocodes. Material data is stored in a JSON file. Current materials in the database are:

urrent materials in the database are:

* concrete (C20 to C90)
* timber (C, D, GL)
* reinforcement (B400, B500, A400, A500)
* structural steel (S235, S275, S355, S450)

Available european steel profiles are:
* IPE
* HEA
* HEB
* HEM
* L
* C
* T
* Pipe
* Box
* Double L
* Double C

There are also some functions to work with material properties:

* creep_coef
* shrink_strain

## Usage

Install Eurocodespy via pip:
>pip install eurocodespy

To use Eurocodespy in a Python file:<br>
>python import eurocodespy as ec

To access the database:<br>
>db = ec.db

The existing functions are listed in the page 'modules'. They are divided by eurocode

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   install
   modules
   support

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

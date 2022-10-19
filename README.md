# eurocodepy v0.1.1

Functions to work with struuctural eurocodes. Relevant data is stored in a JSON file 'eeurocodes.json'. 

Current materials in the database are:

* concrete (C20 to C90)
* timber (C, D, GL)
* reinforcement (S400, S500, A400, A500)
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

## Documentation

A more or less complete description of existing packages and modules can be found on [eurocodepy.readthedocs.io](https://eurocodepy.readthedocs.io)

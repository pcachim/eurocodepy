# Home

This site contains the project documentation for the
[eurocodepy](https://github.com/pcachim/eurocodepy) project that is a python package for using Eurocodes.

**IMPORTANT**: This documentation is a work in progress and is not complete yet (and don't know if it will ever be...).s

## Projet overview

Eurocodepy is a Python package that provides functions to work with structural Eurocodes. It includes material properties, load combinations, and other utilities for structural engineering calculations.

Material data is stored in a JSON file. Current materials in the database are:

* concrete (C20 to C90)
* timber (C, D, GL)
* reinforcement (B400, B500, A400, A500)
* structural steel (S235, S275, S355, S450)
* prestressing steel (Y1770, Y1860, ...)
* bolts (4.6 to 10.9)

Available european steel profiles are:

* IPE
* HEA, HEB, HEM
* CHS, RHS, SHS

There are also some functions to work with material properties:

* creep_coef
* shrink_strain

The existing functions are listed in the page '[Reference](reference/eurocodepy)'.

## Table Of Contents

This documentation is divided into several sections to help you navigate through the project:

* [Home](index.md)
* [Tutorials](tutorials.md)
* [Modules](modules/ec1)
* [Reference](reference/eurocodepy)
* [License](copyright.md)

## Support

If you need any help you can contact the developer via email.

Github: [http://github.com/pcachim/eurocodepy](http://github.com/pcachim/eurocodepy)

## Acknowledgements

I want to thank my plants for providing me with an amount of oxygen each day. Also, I want to thank the sun for providing more than half of their nourishment free of charge.

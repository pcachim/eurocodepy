# eurocodepy v2025.6.5

EurocodePy is a Python package for calculating structures according to Eurocodes. It provides a collection of functions that enable engineers to design and analyze structures based on the Eurocode standards. In addition, it includes a database of structural materials and steel profiles, making it easy to design and analyze structures according to Eurocode standards.

There are also some functions to work with material properties:

* creep_coef
* shrink_strain

The **utils** package has some functions that can be useful:

* stress: calculate the principal stresses and vectors, and the stress inavariants (I1, J2, J3, ...)

## Installation

You can install EurocodePy using pip or [uv](https://github.com/astral-sh/uv) by running the following command:

```shell
pip install eurocodepy
```

or

```shell
uv add eurocodepy
```

Too upgrade to the latest version use:

```shell
pip install eurocodepy --upgrade
```

## Usage

EurocodePy provides a range of functions for designing and analyzing structures according to Eurocodes. Here are some examples:

```python
import eurocodepy as ec
from eurocodepy import ec2
```

## Materials and Profiles Database

EurocodePy includes a database of structural materials and steel profiles. The database is stored in a JSON file and can be easily updated or extended. The materials database includes properties such as the density, modulus of elasticity, and Poisson's ratio, while the steel profiles database includes properties such as the cross-sectional area, moment of inertia, and section modulus.

The database is stored in a JSON file 'eurocodes.json'. This file is loaded when the package is imported, so you can modify it to include your own properties. If you have some suggestions or materials to add to the database and want them to be included for all the community, please contribute as described below in the [contributions](#contributing)
 section. Steel profiles are stored in a separate file 'prof_euro.json'

The database can be accessed through a dictionary. There are also some aliases to easily access the database. The following code gives examples on how to use it.

```Python
import eurocodepy as ec

# To access the entire database
db = ec.db

# To access concrete grade C30/37
conc = ec.db["Materials"]["Concrete"]["Grade"]["C30_37"]  # Alternative 1
conc = ec.Materials["Concrete"]["Grade"]["C30_37"]  # Alternative 2
conc = ec.Concrete["Grade"]["C30_37"]  # Alternative 3
conc = ec.ConcreteGrades["C30_37"]  # Alternative 4

# To access a steel profile
ipe200 = ec.db["SteelProfiles"]["Euro"]["I"]["IPE200"]  # Alternative 1
ipe200 = ec.SteelProfiles["I"]["IPE200"]  # Alternative 2
```

Current materials in the database are:

* concrete (C20/25 to C90/105)
* timber (C14 to C24, D18, GL24 to 36)
* reinforcement - general (B400, B450, B500, B550, B600, B700, classes A, B and C: B400A etc.)
* reinforcement - portuguese (A400NR, A400NRSD, A500NR, A500NRSD, A500ER, A500EL)
* structural steel (S235, S275, S355, S460)

Available european steel profiles are:

* I sections (IPE, HEA, HEB, HEM)
* L sections
* C sections
* T sections
* Pipe sections
* Box sections
* Double L sections
* Double C sections

## Documentation

A more or less complete description of existing packages and modules can be found on [https://pcachim.github.io/eurocodepy](https://pcachim.github.io/eurocodepy/)

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE.md) file for details.

## Contributing

We welcome contributions from everyone. Before getting started, please read our [Code of Conduct](CODE_OF_CONDUCT.md) and [Contributing Guidelines](CONTRIBUTING_GUIDELINES.md).

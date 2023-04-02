# eurocodepy v0.1.20

EurocodePy is a Python package for calculating structures according to Eurocodes. It provides a collection of functions that enable engineers to design and analyze structures based on the Eurocode standards. In addition, it includes a database of structural materials and steel profiles, making it easy to design and analyze structures according to Eurocode standards.

There are also some functions to work with material properties:

* creep_coef
* shrink_strain

The **utils** package has some functions that can be useful:

* stress: calculate the principal stresses and vectors, and the stress inavariants (I1, J2, J3, ...)

## Installation

You can install EurocodePy using pip by running the following command::

```shell
pip install eurocodepy
```

## Usage

EurocodePy is designed to be easy to use. Simply import the package and start using the functions. Here's an example of how to calculate the bending resistance of a steel beam:

```python
import eurocodepy as ec

beam = ec.SteelBeam('HEA200')
beam.check_bending_capacity(M=1000)
```

EurocodePy provides a range of functions for designing and analyzing structures according to Eurocodes. Here are some examples:

from eurocodepy import ec2

## Materials and Profiles Database

EurocodePy includes a database of structural materials and steel profiles. The database is stored in a JSON file and can be easily updated or extended. The materials database includes properties such as the density, modulus of elasticity, and Poisson's ratio, while the steel profiles database includes properties such as the cross-sectional area, moment of inertia, and section modulus.

The database is stored in a JSON file 'eurocodes.json'. This file is loaded when the package is impoorted, soo you can modified it to include you own properties. If you have some suggestions or materials to add to the database and want them to be included for all the coommunity, please contribute as described below in the [contributions](#contributing)
 section. Steel profiles arre stored in a separate file 'prof_euro.json'

The database can be accessed through a dictionary. There are also some aliases to easily access the database. The following code gives examples on how to use it.

```Python
import eurocodepy as ec

# To access the entire database
db = ec.db

# To access concrete class C20/25
conc = ec.db["Materials"]["Concrete"]["Classes"]["C30/37"] # Alternative 1
conc = ec.Materials["Concrete"]["Classes"]["C30/37"] # Alternative 2
conc = ec.Concrete["Classes"]["C30/37"] # Alternative 3
conc = ec.ConcreteClasses["C30/37"] # Alternative 4

# to access a steel profile
ipe200 = ec.SteelProfiles["I_SECTION"]["IPE200]
```

Current materials in the database are:

* concrete (C20/25 to C90/105)
* timber (C14 to C24, D18, GL24 to 36)
* reinforcement - general (B400, B450, B500, B550, B600, B700, cclasses A, B and C: B400A etc.)
* reinforcement - portuguese (A400NR, A400NRSD, A500NR, A500NRSD, A500ER, A500EL)
* structural steel (S235, S275, S355, S450)

Available european steel profiles are:

* I sections (IPE, HEA, HEB, HEM)
* L sections
* C sections
* T sections
* Pipe sections
* Box sections
* Double L sections
* Double C sections

### Calculate the resistance of a concrete section according to Eurocode 2

resistance = ec2.concrete_section_resistance(fck=30, b=0.2, h=0.4, d=0.35, fyk=500)

### Calculate the shear capacity of a reinforced concrete beam according to Eurocode 2

shear_capacity = ec2.shear_capacity_beam(b=0.3, d=0.4, as_=0.01, fck=30, fyk=500, vEd=50)

### Calculate the bending moment capacity of a reinforced concrete beam according to Eurocode 2

moment_capacity = ec2.bending_moment_capacity_beam(b=0.3, d=0.4, as_=0.01, fck=30, fyk=500)
In addition to the Eurocode 2 functions shown above, EurocodePy includes functions for Eurocodes 0, 1, 3, 4, 5, 6, 7, 8, 9, and EN 1992-1-1.

### Create a material object for concrete

concrete = Material(name="C30/37", fck=30, fck_cube=37, fctm=2.6, Ecm=31000, G=11500)

### Create a material object for steel

steel = Material(name="S500", fyk=500, fuk=630, E=200000, G=77000)

### Use the concrete object in a Eurocode 2 calculation

resistance = ec2.concrete_section_resistance(b=0.2, h=0.4, d=0.35, material=concrete, gamma_c=1.5)

### Use the steel object in a Eurocode 3 calculation

section_class = ec3.section_classification(h=0.3, b=0.2, t=0.01, material=steel)

## Documentation

A more or less complete description of existing packages and modules can be found on [eurocodepy.readthedocs.io](https://eurocodepy.readthedocs.io)

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE.md) file for details.

## Contributing

We welcome contributions from everyone. Before getting started, please read our [Code of Conduct](CODE_OF_CONDUCT.md) and [Contributing Guidelines](CONTRIBUTING.md).

### Bug Reports and Feature Requests

If you have found a bug or have a feature request, please submit an issue on our [GitHub issue tracker](https://github.com/pcachim/eurocodepy/issues).

### Pull Requests

We welcome pull requests from everyone. Please ensure that your PR adheres to the following guidelines:

* Before submitting a PR, please create an issue first and wait for approval from a project maintainer.
* Your code should follow our [style guide](STYLE_GUIDE.md).
* Write tests for any new functionality.
* Ensure that all tests pass before submitting your pull request.
* Include documentation for any new functionality you've added.
* Make sure your code has no linter errors or warnings.
* Be sure to explain what your changes do and why they are necessary.

### Getting Started

To get started with contributing, take a look at the issues on our [GitHub issue tracker](https://github.com/pcachim/eurocodepy/issues). If you have any questions or need any help, please don't hesitate to reach out to us on [Slack](https://yourproject.slack.com).

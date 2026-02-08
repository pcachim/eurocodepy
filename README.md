# eurocodepy

A Python library for structural design calculations according to the Eurocode standards, being mostly Python helpers for working with **Eurocodes** in a pragmatic, engineering-focused way: reusable calculations, common design utilities, and tidy abstractions you can drop into your own scripts and notebooks.

> Repo: <https://github.com/pcachim/eurocodepy>

## What this project is

`eurocodepy` aims to provide small, composable building blocks that make it easier to:

- perform Eurocode-aligned calculations in Python
- standardize recurring formulas / factors / combinations
- keep design code in projects readable and testable

Some of the included fatures are:

- Material Properties: Access characteristic and design values for common construction materials (concrete, steel, timber) as defined in EN 1992, EN 1993, and EN 1995.
- Load Combinations: Generate load combinations for Ultimate Limit State (ULS) and Serviceability Limit State (SLS) according to EN 1990.
- Section Properties: Calculate geometric properties for common steel and concrete cross-sections.
- Design Helpers: Functions for verifying buckling resistance, shear capacity, bending moment capacity, and other fundamental checks.

## Status

Early-stage / evolving. APIs may change as the library grows.

## Installation

You can install EurocodePy directly from PyPI using pip:

```shell
pip install eurocodepy
```

with uv

```shell
uv add eurocodepy
```

Or install the latest development version directly from the source repository:

```shell
pip install git+https://github.com/pcachim/eurocodepy.git
```

## Documentation

Detailed documentation, including a full API reference and worked examples, is available at <https://pcachim.github.io/eurocodepy/>.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

Fork the repository.
Create a feature branch (git checkout -b feature/AmazingFeature).
Commit your changes (git commit -m 'Add some AmazingFeature').
Push to the branch (git push origin feature/AmazingFeature).
Open a Pull Request.
Please ensure your code follows the existing style and includes appropriate tests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This software is intended for educational, research, and preliminary design purposes. It is not a certified engineering tool. The authors and contributors assume no liability for any design decisions made using this library. Always verify critical calculations with hand checks and consult the latest official Eurocode standards and national annexes for final design.

## Acknowledgements

Eurocodes and National Annexes are published by their respective standards bodies.
This project is not affiliated with CEN or national standards organizations.

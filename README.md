# normaldb

[![CodeFactor](https://www.codefactor.io/repository/github/anirudh-bijay/normaldb/badge)](https://www.codefactor.io/repository/github/anirudh-bijay/normaldb)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

*normaldb* is a pure-Python package supplying a quadratic-time
implementation of Bernstein's synthesis algorithm for relational
schemas in Codd's third normal form (3NF)[^1]. The core algorithm
is implemented as a builder class to enable inspection of the
outputs of individual steps of the algorithm. The package is
accompanied by an optional Flask app that takes
a set of functional dependencies from the user, pipes it through
the algorithm, and presents the generated schema.

The algorithm uses as a subroutine a linear-time algorithm proposed by
Beeri and Bernstein[^2] to check the
membership of a functional dependency in the closure of a set
of functional dependencies.

This project is undertaken in partial fulfilment of the requirements
of the course [CS315: Principles of Database Systems](https://www.cse.iitk.ac.in/pages/CS315.html)
offered at [IIT Kanpur](https://iitk.ac.in) in Winter 2026 instructed by
[Prof. Arnab Bhattacharya](https://www.cse.iitk.ac.in/users/arnabb).

## Setting up

You will need a recent version of [Python](https://www.python.org).
We have tested the package with Python 3.14.

In the repository root, create a
[virtual environment](https://docs.python.org/3/tutorial/venv.html) and run
```bash
pip install .
```
to install the package dependencies, or
```pwsh
pip install .[gui]
```
to install the package dependencies and the optional dependencies for the
GUI as well.

To launch the app on `localhost`, run
```bash
flask run
```
on the command line.

[^1]: Philip A. Bernstein. “Synthesizing third normal form relations from
      functional dependencies”. In: _ACM Trans. Database Syst._ 1.4 (Dec.
      1976), pp. 277-298. ISSN: 0362-5915.
      doi: [10.1145/320493.320489](https://doi.org/10.1145/320493.320489).

[^2]: Catriel Beeri and Philip A. Bernstein. “Computational problems
      related to the design of normal form relational schemas”. In: _ACM
      Trans. Database Syst._ 4.1 (Mar. 1979), pp. 30-59. ISSN: 0362-5915.
      doi: [10.1145/320064.320066](https://doi.org/10.1145/320064.320066).

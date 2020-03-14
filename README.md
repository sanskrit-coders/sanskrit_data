## Introduction
This module defines:

- **schema**
    - shared standard schema for communicating and storing data (with a particular focus on sanskrit texts) of various types.
    - various idiosyncratic notations used by various modules which deviate from the proposed standards.
- **python classes** (corresponding to the schema) and **shared libraries** for validating, (de-)serializing and storing sanskrit data of various types.
- a **common database interface** for accessing various databases (so that a downstream app can switch to a different database with a single line change).

While this package was originally motivated by Sanskrit text annotation needs, it is more generally useful. 

Similar libraries in various other programming languages are being built:

- Scala (likely compatible with Java): [db-interface](https://github.com/vedavaapi/db-interface) .

## Motivation
- Various sanskrit modules need to communicate data amongst each other (for example through a REST API or database stores or even function calls). **Examples of the data being communicated** could be:
    - Gramatical details of a given word
    - Sentences in a given book chapter
    - Annotations on a given phrase
- When it comes to serialization formats - two distinct approaches present themselves to us:
    - One possible route is to have each project defining and using its own idiosyncratic notation. But this entails an additional burdens:
        - Each communicating module having to convert the data from one idiosyncratic notation to another.
        - Good schema design or notation is non trivial. Even if no external module is using the data, it is a waste to have to reinvent the wheel.
    - A superior route is to have a common, standard format for encoding various data-types for storage/ communication.
- To the extant possible, we should take latter approach to data storage and communication.
- Where idiosyncratic notations are adapted for various reasons, it is still desirable to collect such definitions in a single module - to facilitate conversion to the standard format.

# For users
## Installation
- Install this library (Replace pip2 with pip3 as needed)
    - Latest release: `sudo pip3 install sanskrit_data -U`
    - Development copy: `sudo pip3 install git+https://github.com/vedavaapi/sanskrit_data@master -U`
    - Local modifications: `pip install -e .`
    - [Web](https://pypi.python.org/pypi/sanskrit_data).
- Install libraries for the particular database you want to access through the sanskrit_data.db interface (as needed): pymongo, cloudant (for couchdb).

## Usage
- Please see the generated python sphinx docs in one of the following places:
    - http://sanskrit-data.readthedocs.io
    - [project page](https://sanskrit-coders.github.io/sanskrit_data/build/html/).
    - under docs/build/html/index.html
- Design considerations for data containers corresponding to the various submodules (such as books and annotations) are given below - or in the corresponding source files.

# For contributors
## Contact
Have a problem or question? Please head to [github](https://github.com/vedavaapi/sanskrit_data).

## Packaging
* ~/.pypirc should have your pypi login credentials.
```
python3 setup.py bdist_wheel
twine upload dist/* --skip-existing
```

## Document generation
- sphinx html docs can be generated with `cd docs; make html`
- http://sanskrit-data.readthedocs.io/en/latest/sanskrit_data.html should automatically have good updated documentation - unless there are build errors.
- To update UML diagrams, copy the outputs of the below to docs:
  - `pyreverse -ASmy -k -o png sanskrit_data.schema -p sanskrit_data_schema`
  - `pyreverse -ASmy -k -o png sanskrit_data.db -p sanskrit_data_db`

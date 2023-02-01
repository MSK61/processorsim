
# processorsim

A simulator for program execution on pipelined processors


## Badges

[![Build Status](https://app.travis-ci.com/MSK61/processorsim.svg?branch=master)](https://app.travis-ci.com/MSK61/processorsim)
[![Coverage Status](https://coveralls.io/repos/github/MSK61/processorsim/badge.svg?branch=master)](https://coveralls.io/github/MSK61/processorsim?branch=master)
[![license](https://img.shields.io/github/license/MSK61/processorsim)](https://www.gnu.org/licenses/lgpl-3.0)
![Written in Python](https://img.shields.io/static/v1?label=&message=Python&color=3C78A9&logo=python&logoColor=FFFFFF)
[![Open in Visual Studio Code](https://open.vscode.dev/badges/open-in-vscode.svg)](https://open.vscode.dev/MSK61/processorsim)


## Usage/Examples

Check the [examples](examples) directory for how to use the API. [tests/test_whole.py](tests/test_whole.py) on the other hand illustrates how to use [processorSim.py](src/processorSim.py) as a CLI driver to simulate program executions.


## Requirements

Please refer to [Pipfile](Pipfile) for the list of dependency packages.
## Installation

Install processorsim with pipenv.

```bash
  cd processorsim # local repo directory
  pipenv sync
```

## Running Tests

To run tests, run the following command(inside the local repo directory)

```bash
  pipenv run ./test.sh
```

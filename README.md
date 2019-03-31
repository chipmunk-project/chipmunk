# Chipmunk

[![Build status](https://ci.appveyor.com/api/projects/status/060fwhaq3vfvt22n/branch/master?svg=true)](https://ci.appveyor.com/project/anirudhSK/chipmunk-hhg5f/branch/master)

## Installation
- Install [antlr](https://www.antlr.org/)
- Install [sketch](https://people.csail.mit.edu/asolar/sketch-1.7.5.tar.gz)
- `pip3 install -r requirements.txt && pip3 install .`(from this directory)
(Add sudo if you want to install system wide.)

## How to

### Develop

When you run `python3 chipc/chipmunk.py ...`, Python will complain like following.
```shell
Traceback (most recent call last):
  File "chipc/chipmunk.py", line 6, in <module>
    from chipc.compiler import Compiler
ModuleNotFoundError: No module named 'chipc'
```
It's because how we import all the modules in this package: we're using absolute imports.

You can simply iterate like following
1. make changes to any module
2. pip install .
3. run `chipmunk` or other binaries to see your change is working or not
4. Make more changes
5. pip uninstall chipc
6. pip install .

and many more steps like this

Since this process will be prone to confusion, simply do following, when developing.
1. `pip install -e .`
2. Make changes to any module
3. `python3 chipc/chipmunk.py ...`


### Codegen

```shell
chipmunk example_specs/simple.sk example_alus/raw.stateful_alu 2 2 codegen sample1 serial
```

or
```shell
chipmunk example_specs/simple.sk example_alus/raw.stateful_alu 2 2 codegen sample1 parallel
```

### Parallel codegen

```shell
chipmunk_parallel example_specs/simple.sk example_alus/raw.stateful_alu 2 2 codegen
```

### Optimization Verification

```shell
chipmunk example_specs/simple.sk example_alus/raw.stateful_alu 1 1 optverify sample1 serial
chipmunk example_specs/simple.sk example_alus/raw.stateful_alu 1 1 optverify sample2 serial
optverify sample1 sample2 example_transforms/very_simple.transform
```

### Test

Run:

```shell
antlr4 chipc/stateful_alu.g4 -Dlanguage=Python3 -visitor -package chipc
python3 -m unittest
```

If you want to add a test, add a new file in [tests](tests/) directory or add
test cases in existing `test_*.py` file.

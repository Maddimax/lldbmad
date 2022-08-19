# lldbmad

An lldb script that adds various summary providers and Child synthesizers for Qt and Qt Creator

# Installation

Add the following line to your .lldbinit:

`command script import <path-to-checkout>/lldbmad.py`

# Tests

To run tests execute:

`cmake --build . --target check`

To run the tests in docker:

```
docker build . -t lldbmad
docker run --privileged -it --rm -v $PWD:/src lldbmad
```
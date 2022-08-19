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
docker build . -f Dockerfile-ubuntu-qt6 -t lldbmad-ubuntu-qt6
docker run --privileged -it --rm -v $PWD:/src lldbmad-ubuntu-qt6
```

> You NEED to run "--privileged", otherwise lldb will fail to attach to the process with `error: 'A' packet returned an error: 8`

> The Alpine Docker currently fails the checks, since the debug symbols for private classes are missing. If you have any idea how to get them, please open an Issue
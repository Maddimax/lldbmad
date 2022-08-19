# lldbmad

An lldb script that adds various summary providers and Child synthesizers for Qt and Qt Creator

# Installation

Add the following line to your .lldbinit:

`command script import <path-to-checkout>/lldbmad.py`



# Tests

To run tests execute:

`lldb build/test-app/lldbtest --one-line "command script import test.py" -o quit`
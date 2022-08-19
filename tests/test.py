import sys
from lldb import debugger
import os

target = debugger.GetSelectedTarget()

def check(value, expr, expected):
    print('\t"%s" => (should be "%s")' % (expr, expected))

    if isinstance(expected, dict):
        numChildren = value.GetNumChildren()
        if numChildren != len(expected):
            raise Exception('\t\tFAILED: Expected %i children, got %i' % (len(expected), numChildren))
    
        for i in range(0, numChildren):
            child = value.GetChildAtIndex(i)
            k = list(expected.keys())[i]
            if child.name != k:
                raise Exception('\t\tFAILED: Expected child %i to be named "%s", got "%s"' % (i, k, child.name))

            if child.TypeIsPointerType():
                child = child.Dereference()
            
            check(child, "%s.%s" % (expr, child.name), expected[k])

    elif isinstance(expected, str) and value.summary != expected:
        raise Exception('\t\tFAILED: Expected "%s" = "%s", got "%s" = "%s"' % (expr, expected, expr, value.summary))
    elif isinstance(expected, int) and value.GetValueAsSigned() != expected:
        raise Exception('\t\tFAILED: Expected "%s" = %s, got "%s" = %s' % (expr, expected, expr, value.GetValueAsSigned()))


def CHECK_SUMMARY(expression, expected_summary):
    currentFrame = debugger.GetSelectedTarget().GetProcess().GetSelectedThread().GetSelectedFrame()
    print('Current frame: %s' % currentFrame)
    print('\tChecking summary ...')
    value = target.EvaluateExpression(expression)

    try:
        check(value, expression, expected_summary)
        print('\t\tPASSED')
    except Exception as e:
        print(e, flush=True)
        os._exit(1)

def CHECK_CHILDREN(expression, expected_children):
    currentFrame = debugger.GetSelectedTarget().GetProcess().GetSelectedThread().GetSelectedFrame()
    print('Current frame: %s' % currentFrame)
    print('\tChecking children ...')
    value = target.EvaluateExpression(expression)

    try:
        check(value, expression, expected_children)
        print('\t\tPASSED')
    except Exception as e:
        print(e, flush=True)
        os._exit(1)

def CHECK(expression, expected_summary, expected_children):
    CHECK_SUMMARY(expression, expected_summary)
    CHECK_CHILDREN(expression, expected_children)

def read_source():
    '''Read the source file and create Breakpoints for CHECK_SUMMARY and CHECK_CHILDREN'''
    print("Reading source ...")
    with open('test-app/main.cpp', 'r') as f:
        lineNumber = 1
        for line in f:
            if "// CHECK" in line:
                line = line.strip('/ \n')
                print("Found check in line %i: %s" % (lineNumber, line))

                # Create a breakpoint at the line
                breakpoint = target.BreakpointCreateByLocation('main.cpp', lineNumber)
                breakpoint.SetScriptCallbackBody("import test;return test.%s" % (line))
                breakpoint.SetAutoContinue(True)
            lineNumber = lineNumber+1

read_source()

debugger.HandleCommand('r')

#debugger.HandleCommand('exit')


import sys
from lldb import debugger
import os

print('IMPORTING ...')

def check(value, expr, expected):
    target = debugger.GetSelectedTarget()
    print('\t"%s" => (should be "%s")' % (expr, expected))

    if isinstance(expected, dict):
        numChildren = value.GetNumChildren()
        if numChildren != len(expected):
            raise Exception('\t\tFAILED: Expected %i children, got %i' % (len(expected), numChildren))
    
        for i in range(0, numChildren):
            child = value.GetChildAtIndex(i)
            k = list(expected.keys())[i]
            if not isinstance(k, int) and child.name != k:
                raise Exception('\t\tFAILED: Expected child %i to be named "%s", got "%s"' % (i, k, child.name))

            if child.TypeIsPointerType():
                child = child.Dereference()
            
            check(child, "%s.%s" % (expr, child.name), expected[k])

    elif isinstance(expected, str) and value.summary != expected:
        raise Exception('\t\tFAILED: Expected "%s" = "%s", got "%s" = "%s"' % (expr, expected, expr, value.summary))
    elif isinstance(expected, int) and value.GetValueAsSigned() != expected:
        raise Exception('\t\tFAILED: Expected "%s" = %s, got "%s" = %s' % (expr, expected, expr, value.GetValueAsSigned()))


def CHECK_SUMMARY(expression, expected_summary):
    target = debugger.GetSelectedTarget()
    currentFrame = target.GetProcess().GetSelectedThread().GetSelectedFrame()
    print('Current frame: %s' % currentFrame)
    print('\tChecking summary ... ("%s")' % expression, flush=True)

    try:
        value = currentFrame.FindVariable(expression)
        if not value.IsValid():
            print('!! Could not find variable by name "%s"' % expression)
            return False

        check(value, expression, expected_summary)
        print('\t\tPASSED')
        return True
    except Exception as e:
        print(e, flush=True)
        return False


def CHECK_CHILDREN(expression, expected_children):
    target = debugger.GetSelectedTarget()
    currentFrame = debugger.GetSelectedTarget().GetProcess().GetSelectedThread().GetSelectedFrame()
    print('Current frame: %s' % currentFrame)
    print('\tChecking children ... ("%s")' % expression, flush=True)

    try:
        value = currentFrame.FindVariable(expression)
        if not value.IsValid():
            print('!! Could not find variable by name "%s"' % expression)
            return False

        check(value, expression, expected_children)
        print('\t\tPASSED')
        return True
    except Exception as e:
        print(e, flush=True)
        return False

def CHECK(expression, expected_summary, expected_children):
    return CHECK_SUMMARY(expression, expected_summary) and CHECK_CHILDREN(expression, expected_children)

activeBp = 0
numBp = 0

bp = []
cmds = []
def read_source():
    global bp

    target = debugger.GetSelectedTarget()

    print("Reading source ...")
    with open('test-app/main.cpp', 'r') as f:
        lineNumber = 1
        for line in f:
            if "// CHECK" in line:
                line = line[line.index("// CHECK") + len("// "):].strip('\r\n')
                print("Found check in line %i: %s" % (lineNumber, line))

                # Create a breakpoint at the line
                breakpoint = target.BreakpointCreateByLocation('main.cpp', lineNumber)
                breakpoint.SetAutoContinue(False)
                breakpoint.SetEnabled(activeBp == bp)
                bp.append(breakpoint)
                cmds.append((line, lineNumber))
            lineNumber = lineNumber+1

    print("Done reading source.")
    print()

read_source()

debugger.SetAsync(False)

for i in range(0, len(bp)):
    print('RUN (%i/%i)' %(i, len(bp)), flush=True)
    bp[i].SetEnabled(True)
    debugger.HandleCommand('r')
    if debugger.GetSelectedTarget().GetProcess().GetState() == 5:
        # We have stopped at the breakpoint ...
        expectedLine = cmds[i][1]
        actualLine = debugger.GetSelectedTarget().GetProcess().GetSelectedThread().GetSelectedFrame().GetLineEntry().GetLine()
        print('\tExpected line %i, actual line %i' % (expectedLine, actualLine))
        if expectedLine == actualLine:
            if not eval(cmds[i][0]):
                break
        else:
            print('Stopped in wrong location, continuing ...')

    bp[i].SetEnabled(False)
    print('DONE', flush=True)

#debugger.HandleCommand('exit')


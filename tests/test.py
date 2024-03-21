import lldb
import sys
import os


# Create a new debugger instance
debugger = lldb.SBDebugger.Create()
if "SkipAppInitFiles" in dir(debugger):
    debugger.SkipAppInitFiles(True)
if "SkipLLDBInitFiles" in dir(debugger):
    debugger.SkipLLDBInitFiles(True)

debugger.HandleCommand('command script import lldbmad.py')

# When we step or continue, don't return from the function until the process
# stops. We do this by setting the async mode to false.
debugger.SetAsync (False)


def check(debugger, value, expr, expected):
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
            
            check(debugger, child, "%s.%s" % (expr, child.name), expected[k])

    elif isinstance(expected, str) and value.summary != expected:
        raise Exception('\t\tFAILED: Expected "%s" = "%s", got "%s" = "%s"' % (expr, expected, expr, value.summary))
    elif isinstance(expected, int) and value.GetValueAsSigned() != expected:
        raise Exception('\t\tFAILED: Expected "%s" = %s, got "%s" = %s' % (expr, expected, expr, value.GetValueAsSigned()))


def CHECK_SUMMARY(expression, expected_summary):
    global debugger
    target = debugger.GetSelectedTarget()
    currentFrame = target.GetProcess().GetSelectedThread().GetSelectedFrame()
    print('\tChecking summary ... ("%s")' % expression, flush=True)

    try:
        value = currentFrame.FindVariable(expression)
        if not value.IsValid():
            print('!! Could not find variable by name "%s"' % expression)
            return False

        check(debugger, value, expression, expected_summary)
        print('\t\tPASSED')
        return True
    except Exception as e:
        print(e, flush=True)
        return False


def CHECK_CHILDREN(expression, expected_children):
    global debugger

    target = debugger.GetSelectedTarget()
    currentFrame = debugger.GetSelectedTarget().GetProcess().GetSelectedThread().GetSelectedFrame()
    print('\tChecking children ... ("%s")' % expression, flush=True)

    try:
        value = currentFrame.FindVariable(expression)
        if not value.IsValid():
            print('!! Could not find variable by name "%s"' % expression)
            return False

        check(debugger, value, expression, expected_children)
        print('\t\tPASSED')
        return True
    except Exception as e:
        print(e, flush=True)
        return False

def CHECK(expression, expected_summary, expected_children):
    return CHECK_SUMMARY(expression, expected_summary) and CHECK_CHILDREN(expression, expected_children)

def read_source():
    breakPoints = []
    cmds = []

    target = debugger.GetSelectedTarget()

    print("Reading source ...")
    with open('test-app/main.cpp', 'r') as f:
        lineNumber = 0
        for line in f:
            lineNumber = lineNumber+1
            if "// CHECK" in line:
                line = line[line.index("// CHECK") + len("// "):].strip('\r\n')
                # Create a breakpoint at the line
                breakpoint = target.BreakpointCreateByLocation('main.cpp', lineNumber)
                breakpoint.SetAutoContinue(False)
                breakpoint.SetEnabled(False)

                if breakpoint.GetNumLocations() == 0:
                    print("Could not create breakpoint at line %i" % lineNumber)
                    continue
                if breakpoint.GetNumLocations() > 1:
                    print("Warning: Multiple locations for breakpoint at line %i, Ignoring..." % lineNumber)
                    continue
                location = breakpoint.GetLocationAtIndex(0)
                if location.GetAddress().GetLineEntry().GetLine() != lineNumber:
                    print("Warning: Breakpoint at line %i is at line %i, Ignoring..." % (lineNumber, location.GetAddress().GetLineEntry().GetLine()))
                    continue
                print("Found check in line %i: %s" % (lineNumber, line))

                breakpoint.SetEnabled(True)
                breakPoints.append(breakpoint)
                cmds.append((line, lineNumber))

    print("Done reading source.")
    return (breakPoints, cmds)


def do_check(process, cmds):
    state = process.GetState()

    if state == lldb.eStateExited:
        print('Process exited??')
        return False

    if state != lldb.eStateStopped:
        print('Process is not stopped, but in state %i' % state)
        return False

    currentFrame = process.GetSelectedThread().GetSelectedFrame()
    print('Current frame: %s' % currentFrame)

    cmd = next(cmd for cmd in cmds if cmd[1] == currentFrame.GetLineEntry().GetLine())

    if not cmd:
        print('Could not find command for line %i' % actualLine)
        return False

    if not eval(cmd[0]):
        return False
    
    return True

def main(args):
    # Create a target from a file and arch
    print('Creating a target for "%s"' % args[0])

    target = debugger.CreateTargetWithFileAndArch (args[0], lldb.LLDB_ARCH_DEFAULT)

    if not target:
        print('Error creating target')
        return 1

    bps, cmds = read_source()

    if len(bps) == 0:
        print('No checks found in source')
        return 1

    print("Starting process ...")
    process = target.LaunchSimple (None, None, os.getcwd())

    for i in range(0, len(bps)):
        print('RUN (%i/%i)' %(i, len(bps)), flush=True)
        if not do_check(process, cmds):
            return 2

        process.Continue()

    return 0

if __name__ == '__main__':
    exit(main(sys.argv[1:]))
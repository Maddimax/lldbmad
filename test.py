from lldb import debugger

target = debugger.GetSelectedTarget()

def CHECK_SUMMARY(expression, expected_summary):
    currentFrame = debugger.GetSelectedTarget().GetProcess().GetSelectedThread().GetSelectedFrame()
    print('Current frame: %s' % currentFrame)
    print('\tChecking summary for expression "%s" (should be "%s")' % (expression, expected_summary))
    summary = target.EvaluateExpression(expression).summary
    print('\t\tActual summary: %s' % summary)

    if summary == expected_summary:
        print('\t\tPASSED')
    else:
        print('\t\tFAILED')
        debugger.Terminate()

def CHECK_CHILDREN(expression, expected_children):
    currentFrame = debugger.GetSelectedTarget().GetProcess().GetSelectedThread().GetSelectedFrame()
    print('Current frame: %s' % currentFrame)
    print('\tChecking children for expression "%s" (should be "%s")' % (expression, expected_children))
    value = target.EvaluateExpression(expression)

    numChildren = value.GetNumChildren()
    if numChildren != len(expected_children):
        print('\t\tFAILED: Expected %i children, got %i' % (len(expected_children), numChildren))
        debugger.Terminate()
        return
    
    for i in range(0, numChildren):
        child = value.GetChildAtIndex(i)
        k = list(expected_children.keys())[i]
        if child.name != k:
            print('\t\tFAILED: Expected child %i to be named "%s", got "%s"' % (i, k, child.name))
            debugger.Terminate()
            break
        if isinstance(expected_children[k], str) and child.summary != expected_children[k]:
            print('\t\tFAILED: Expected child %i to be "%s": "%s", got "%s": "%s"' % (i, k, expected_children[k], child.name, child.summary))
            debugger.Terminate()
            break
        if isinstance(expected_children[k], int) and child.GetValueAsSigned() != expected_children[k]:
            print('\t\tFAILED: Expected child %i to be "%s": "%s", got "%s": "%s"' % (i, k, expected_children[k], child.name, child.GetValueAsSigned()))
            debugger.Terminate()
            break
        
    print('\t\tPASSED')

def read_source():
    print("Reading source ...")
    with open('test-app/main.cpp', 'r') as f:
        lineNumber = 1
        for line in f:
            if "// CHECK_" in line:
                line = line.strip('/ \n')
                print("Found check in line %i: %s" % (lineNumber, line))

                # Create a breakpoint at the line
                breakpoint = target.BreakpointCreateByLocation('main.cpp', lineNumber)
                breakpoint.SetScriptCallbackBody("import test;test.%s" % (line))
                breakpoint.SetAutoContinue(True)
            lineNumber = lineNumber+1

read_source()


debugger.HandleCommand('r')

#debugger.HandleCommand('exit')
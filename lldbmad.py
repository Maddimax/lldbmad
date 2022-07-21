import traceback
import lldb
import pdb

g_qtVersion = None

def stringFromSummary(summary):
    result = summary.strip('u')
    return result.strip('"')

def splitVersion(version):
    return tuple(map(int, version.split('.')))    

def output_exceptions(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(traceback.format_exc())
        return None

    return inner

def detectQtVersion(debugger):
    global g_qtVersion

    if g_qtVersion is None:
        target = debugger.GetSelectedTarget()
        v = target.EvaluateExpression('qVersion()')
        if v.IsValid():
            g_qtVersion = splitVersion(v.summary.strip('"'))
            print("Detected Qt Version:", g_qtVersion)

    return g_qtVersion

def check_qt_version(func):
    def inner(*args, **kwargs):
        detectQtVersion(lldb.debugger)
        return func(*args, **kwargs)
    return inner

class qt_version:
    """Decorator to automatically select the correct version of a function based on the Qt version."""

    # _func_versions is a (global) dictionary of dictionaries.
    # The outer dictionary is keyed by function name.
    # The inner dictionary is keyed by the qt version.
    _func_versions = {}

    # This is the constructor. It is called once for every instance of @qt_version being created.
    def __init__(self, version):
        self._version = version

    # This is the decorator function. It is called once for every instance of @qt_version being used.
    def __call__(self, func):
        # If we haven't seen this function yet, add it to the dictionary.
        if not func.__name__ in self._func_versions:
            self._func_versions[func.__name__] = {}

        # Add the function to the dictionary.
        self._func_versions[func.__name__][self._version] = func

        # This is the wrapper function that is actually called.
        def wrapped(*args, **kwargs):
            v = detectQtVersion(lldb.debugger)
            # func.__name__ is captured once when __call__ is called.

            if not v[0] in self._func_versions[func.__name__]:
                raise Exception('"%s" is not implemented for Qt version %s' % (func.__name__, v[0]))

            return self._func_versions[func.__name__][v[0]](*args, **kwargs)
        return wrapped

class QListChildProvider:
    def __init__(self, valobj, internal_dict):
        self.valobj = valobj

    def num_children(self):
        return self.dLen.unsigned

    def get_child_index(self, name):
        if name == '$$dereference$$':
            return 0
        try:
            return int(name.lstrip('[').rstrip(']'))
        except:
            return -1

    def get_child_at_index(self, index):
        dt = self.ptr.GetType().GetPointeeType()
        return self.ptr.CreateChildAtOffset('[' + str(index) + ']', index * dt.GetByteSize(), dt)

    def update(self):
        try:
            self.dLen = self.valobj.GetChildMemberWithName('d').GetChildMemberWithName('size')
            self.ptr = self.valobj.GetChildMemberWithName('d').GetChildMemberWithName('ptr')

        except:
            pass

    def has_children(self):
        return True

class QVariantChildProvider:
    def __init__(self, valobj, idict):
        self.valobj = valobj

    def hasChildren(self):
        return True

    def get_qvariant_type(self):
        try:
            target = lldb.debugger.GetSelectedTarget()
            typeAddr = self.packedType.unsigned << 2
            metaType = target.FindFirstType('QtPrivate::QMetaTypeInterface')
            mtAddr = lldb.SBAddress(typeAddr, target)
            mtd = target.CreateValueFromAddress('mt', mtAddr, metaType)
            mtdName = mtd.GetChildMemberWithName('name')
            if mtdName.summary == None:
                return None, None
            tName = mtdName.summary.strip('"')
            tName = tName.replace(',', ', ').replace('>>', '> >')
            vType = target.FindFirstType(tName)
            return tName, vType
        except Exception as e:
            print("Error retrieving QVariant type:", e)
            
        return None, None

    def get_child_index(self, name):
        if name == '$$dereference$$' or name.starts_with('QVariant'):
            return 0
        return -1

    def num_children(self):
        if self.isNull.unsigned == 1:
            return 0

        tName, vType = self.get_qvariant_type()
        if not vType:
            return 0

        return 1

    def get_child_at_index(self, index):
        if self.isShared.unsigned == 1:
            return None
        try:
            tName, vType = self.get_qvariant_type()
            if not vType:
                return None
            
            return self.data.CreateValueFromAddress('[%s]'%tName, self.data.GetLoadAddress(), vType)
        except Exception as e:
            print("Error parsing QVariant:", e)
        return None

    def update(self):
        try:
            self.d = self.valobj.GetChildMemberWithName('d')
            self.isNull = self.d.GetChildMemberWithName('is_null')
            self.isShared = self.d.GetChildMemberWithName('is_shared')
            self.packedType = self.d.GetChildMemberWithName('packedType')
            self.data = self.d.GetChildMemberWithName('data').GetChildMemberWithName('data')
        except:
            pass

@output_exceptions
@check_qt_version
def qcoreapplication_summary(valobj, idict, options):
    d = valobj.GetChildMemberWithName('d_ptr').GetChildMemberWithName('d').Dereference()
    argc = d.GetChildMemberWithName('argc').Dereference().unsigned

    args = [d.GetValueForExpressionPath('.argv[%i]' % (i)).summary for i in range(0,argc)]
    return "{%s}"%' '.join(args)

@output_exceptions
@check_qt_version
def qobject_summary(valobj, idict, options):
    extraData = valobj.GetNonSyntheticValue().GetValueForExpressionPath('.d_ptr.d' ).Dereference().GetChildMemberWithName('extraData')# '((QObjectPrivate*).d_ptr.d).extraData.objectName.val')
    
    if extraData.unsigned != 0:
        objName = extraData.Dereference().GetChildMemberWithName('objectName')
        val = objName.GetValueForExpressionPath('.val.d.ptr')
        if val.unsigned != 0:
            return "{%s}" % val.summary.strip('u')

    return ""

class QObjectChildProvider:
    def __init__(self, valobj, idict):
        self.valobj = valobj

    def hasChildren(self):
        return True

    def num_children(self):
        return len(self.children) + self.numProperties

    def get_child_at_index(self, index):
        if index < len(self.children):
            return self.children[index]

        pIndex = index - len(self.children)

        pName = self.propNames.GetChildAtIndex(pIndex).GetValueForExpressionPath('.d.ptr').summary
        pVal = self.propValues.GetChildAtIndex(pIndex).Dereference()
        return pVal.CreateValueFromData("[%s]" % pName, pVal.GetData(), pVal.GetType())

    def update(self):
        try:
            self.children = [
                self.valobj.GetValueForExpressionPath('.d_ptr.d.parent' ),
                self.valobj.GetValueForExpressionPath('.d_ptr.d.children' ),
            ]
            extraData = self.valobj.GetValueForExpressionPath('.d_ptr.d' ).Dereference().GetValueForExpressionPath('.extraData')
            self.propNames = extraData.GetChildMemberWithName('propertyNames')
            self.propValues = extraData.GetChildMemberWithName('propertyValues')

            self.numProperties = self.propNames.GetNumChildren()
        except:
            pass

@output_exceptions
@check_qt_version
def qfile_summary(valobj: lldb.SBValue, idict, options):
    target = lldb.debugger.GetSelectedTarget()
    tFilePrivate = target.FindFirstType("QFilePrivate")

    d = valobj.GetValueForExpressionPath('->d_ptr.d' )
    dFilePrivate = d.CreateChildAtOffset("fileprivate", 0, tFilePrivate)
    fileName = dFilePrivate.GetValueForExpressionPath('.fileName.d.ptr')
    fileNameSummary = fileName.summary if fileName.summary else ""
    openMode = dFilePrivate.GetValueForExpressionPath('.openMode.i')
    error = dFilePrivate.GetValueForExpressionPath('.error').value
    openMode = openMode.signed
    oModeFields = ['read', 'write', 'append', 'truncate', 'text', 'unbuffered', 'newonly', 'existing']
    lOpenMode = ['closed']

    
    if openMode != 0:
        lOpenMode = []
        for i in range(1, 8):
            if (1 << i) & openMode:
                lOpenMode.append(oModeFields[i])

    return "{filename=%s, openmode=%s, error=%s}" % (stringFromSummary(fileNameSummary), '|'.join(lOpenMode), error)

@output_exceptions
@qt_version(6)
def qstring_summary(valobj: lldb.SBValue, idict, options):
    d = valobj.GetNonSyntheticValue().GetChildMemberWithName('d')
    size = d.GetChildMemberWithName('size').unsigned
    ptr = d.GetChildMemberWithName('ptr')

    if size == 0:
        return '""'

    return '"%s"' % (stringFromSummary(ptr.summary))


@output_exceptions
@qt_version(5)
def qstring_summary(valobj: lldb.SBValue, idict, options):
    type = valobj.GetType().GetBasicType(lldb.eBasicTypeChar16)
    d = valobj.GetNonSyntheticValue().GetChildMemberWithName('d')
    addr = d.AddressOf().Dereference().unsigned
    offset = d.GetChildMemberWithName('offset').unsigned
    ptr = valobj.CreateValueFromAddress('test', addr+offset, type)
    return '"%s"' % stringFromSummary(ptr.AddressOf().summary)


class QStringProvider:
    def __init__(self, valobj, idict):
        self.valobj = valobj

    def hasChildren(self):
        return True

    def num_children(self):
        return 3

    @qt_version(6)
    def get_child_at_index(self, index):
        if index == 0:
            return self.valobj.GetChildMemberWithName('d').GetChildMemberWithName('size')
        if index == 1:
            return self.valobj.GetChildMemberWithName('d').GetChildMemberWithName('ptr')
        if index == 2:
            return self.valobj.GetChildMemberWithName('d').GetChildMemberWithName('d')
        return None
    
    @qt_version(5)
    def get_child_at_index(self, index):
        if index == 0:
            return self.valobj.GetChildMemberWithName('d').GetChildMemberWithName('size')

        if index == 1:
            type = self.valobj.GetType().GetBasicType(lldb.eBasicTypeChar16)

            d = self.valobj.GetChildMemberWithName('d')
            addr = d.AddressOf().Dereference().unsigned
            offset = d.GetChildMemberWithName('offset').unsigned
            ptr = self.valobj.CreateValueFromAddress('ptr', addr+offset, type).AddressOf()
            return ptr

        return self.valobj.GetChildMemberWithName('d')

    def update(self):
        pass


@output_exceptions
@check_qt_version
def envpair_summary(valobj: lldb.SBValue, idict, options):
    key = valobj.GetChildMemberWithName('first').GetChildMemberWithName('name').summary
    value = valobj.GetChildMemberWithName('second').GetChildMemberWithName('first').summary
    return "{%s => %s}" % (key, value)

@output_exceptions
@check_qt_version
def qtextcursor_summary(valobj: lldb.SBValue, idict, options):
    target = lldb.debugger.GetSelectedTarget()
    tPrivate = target.FindFirstType("QTextCursorPrivate")


    d = valobj.GetChildMemberWithName('d').GetChildMemberWithName('d')

    priv = d.CreateValueFromAddress('private', d.unsigned, tPrivate)

    pos = priv.GetChildMemberWithName('position').unsigned
    anchor = priv.GetChildMemberWithName('anchor').unsigned
    return "{pos=%i, anchor=%i}" % (pos, anchor)

# QMap is just a wrapper for std::map<>, so we just return the internal map here as the sole child
class QMapChildProvider:
    def __init__(self, valobj, idict):
        self.valobj = valobj

    def hasChildren(self):
        return True
    
    def num_children(self):
        return self.m.GetNumChildren()
    
    @output_exceptions
    def get_child_at_index(self, index):
        syntheticChild = self.m.GetChildAtIndex(index, lldb.eDynamicCanRunTarget, True)
        key = syntheticChild.GetChildMemberWithName('first').GetSummary()
        child = self.m.CreateValueFromData('[%s]' % key, syntheticChild.GetData(), syntheticChild.GetType())
        return child

    def update(self):
        try:
            self.m = self.valobj.GetChildMemberWithName('d').GetChildMemberWithName('d').GetChildMemberWithName('m')
            self.m.SetPreferSyntheticValue(True)
        except:
            pass



def __lldb_init_module(debugger, dict):
    print("Loading MAD extensions...")
    debugger.HandleCommand('type category  define MAD')

    debugger.HandleCommand('type summary   add -w MAD QObject --expand -F lldbmad.qobject_summary')
    debugger.HandleCommand('type synthetic add -w MAD QObject --python-class lldbmad.QObjectChildProvider')

    debugger.HandleCommand('type summary   add -w MAD QFile -F lldbmad.qfile_summary')
    
    debugger.HandleCommand('type summary   add QFileInfo --summary-string "${var.d_ptr.d.fileEntry.m_filePath}"')
    
    debugger.HandleCommand('type summary   add -w MAD QString -F lldbmad.qstring_summary')
    debugger.HandleCommand('type synthetic add -w MAD QString  --python-class lldbmad.QStringProvider')
    
    debugger.HandleCommand('type summary   add -w MAD --summary-string "size=${var.d.size}" QByteArray')

    debugger.HandleCommand('type summary   add -w MAD QTextCursor -F lldbmad.qtextcursor_summary')

    debugger.HandleCommand('type summary   add -w MAD -x "^QList<.+>$" --expand --summary-string "size=${svar%#}"')
    debugger.HandleCommand('type synthetic add -w MAD -x "^QList<.+>$" --python-class lldbmad.QListChildProvider')
    
    debugger.HandleCommand('type synthetic add -w MAD -l lldbmad.QVariantChildProvider QVariant')
    debugger.HandleCommand('type summary   add -w MAD --inline-children QVariant')

    debugger.HandleCommand('type summary   add -w MAD -x "^Q.*Application$" -F lldbmad.qcoreapplication_summary')

    debugger.HandleCommand('type summary   add -w MAD --summary-string "${var.d.d.m}" -x "^QMap<.+>$"')
    debugger.HandleCommand('type synthetic add -w MAD -l lldbmad.QMapChildProvider -x "^QMap<.+>$"')

    debugger.HandleCommand('type category  enable MAD')

    debugger.HandleCommand('type category  define QTC')

    debugger.HandleCommand('type summary   add -w QTC -x "^std::__[[:alnum:]]+::pair<const Utils::DictKey, std::__[[:alnum:]]+::pair<QString, bool> >" -F lldbmad.envpair_summary')

    debugger.HandleCommand('type summary   add -w QTC "Utils::FilePath" --summary-string "${var.m_data}"')

    debugger.HandleCommand('type category  enable QTC')

    debugger.HandleCommand('settings set target.process.thread.step-avoid-regexp "^(std::|boost::shared_ptr|QStringBuilder)"')


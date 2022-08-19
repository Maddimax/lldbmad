import math
import traceback
import lldb
import pdb
from functools import wraps

g_qtVersion = None

def stringFromSummary(summary):
    #print("Summary: ((%s))" % summary)
    if not summary or summary == "unable to read data":
        return None
    
    result = summary.strip('u')
    return result.strip('"')

def splitVersion(version):
    return tuple(map(int, version.split('.')))    

def output_exceptions(func):
    @wraps(func)
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(traceback.format_exc())
        return None

    return inner

def detectQtVersion(debugger):
    global g_qtVersion
    try:
        if g_qtVersion is None:
            target = debugger.GetSelectedTarget()
            v = target.EvaluateExpression('qVersion()')
            if v.IsValid() and v.summary:
                g_qtVersion = splitVersion(v.summary.strip('"'))
                print("Detected Qt Version:", g_qtVersion)
            else:
                v = target.EvaluateExpression('qtHookData[2]')
                if v.IsValid():
                    h = hex(v.unsigned)
                    g_qtVersion = (int(h[2:][:-4]), int(h[2:][-4:-2]), int(h[2:][-2:]))
                    print("Detected Qt Version:", g_qtVersion)
    except Exception as e:
        print("Auto-determining Qt Version failed:", e)
        g_qtVersion = (6, 3, 0)
        print("Falling back to hard-coded version:", g_qtVersion)

    return g_qtVersion

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
        @wraps(func)
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

    @output_exceptions
    def update(self):
        self.dLen = self.valobj.GetChildMemberWithName('d').GetChildMemberWithName('size')
        self.ptr = self.valobj.GetChildMemberWithName('d').GetChildMemberWithName('ptr')

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
def qcoreapplication_summary(valobj, idict, options):
    d = valobj.GetChildMemberWithName('d_ptr').GetChildMemberWithName('d').Dereference()
    argc = d.GetChildMemberWithName('argc').Dereference().unsigned

    args = [d.GetValueForExpressionPath('.argv[%i]' % (i)).summary for i in range(0,argc)]
    return "{%s}"%' '.join(args)

@output_exceptions
def qobject_summary(valobj, idict, options):
    extraData = valobj.GetNonSyntheticValue().GetValueForExpressionPath('.d_ptr.d' ).Dereference().GetChildMemberWithName('extraData')# '((QObjectPrivate*).d_ptr.d).extraData.objectName.val')
    if extraData.unsigned != 0:
        objName = extraData.Dereference().GetChildMemberWithName('objectName')
        if objName.summary != None:
            return "{%s}" % objName.summary

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
def qfile_summary(valobj: lldb.SBValue, idict, options):
    target = lldb.debugger.GetSelectedTarget()
    tFilePrivate = target.FindFirstType("QFilePrivate")

    d = valobj.GetValueForExpressionPath('->d_ptr.d' )
    dFilePrivate = d.CreateChildAtOffset("fileprivate", 0, tFilePrivate)
    fileName = dFilePrivate.GetValueForExpressionPath('.fileName')
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

    s = stringFromSummary(ptr.summary)
    if s:
        return '"%s"' % (s)
    return None


@output_exceptions
@qt_version(5)
def qstring_summary(valobj: lldb.SBValue, idict, options):
    type = valobj.GetType().GetBasicType(lldb.eBasicTypeChar16)
    d = valobj.GetNonSyntheticValue().GetChildMemberWithName('d')
    addr = d.AddressOf().Dereference().unsigned
    offset = d.GetChildMemberWithName('offset').unsigned
    ptr = valobj.CreateValueFromAddress('test', addr+offset, type)

    return '"%s"' % stringFromSummary(ptr.AddressOf().summary)

@output_exceptions
def qurl_summary(valobj: lldb.SBValue, idict, options):
    target = lldb.debugger.GetSelectedTarget()
    tUrlPrivate = target.FindFirstType("QUrlPrivate")

    d = valobj.GetNonSyntheticValue().GetChildMemberWithName('d')
    dUrlPrivate = d.CreateChildAtOffset("urlprivate", 0, tUrlPrivate)

    scheme = (dUrlPrivate.GetChildMemberWithName('scheme').summary or "").strip('"')
    host = (dUrlPrivate.GetChildMemberWithName('host').summary or "").strip('"')
    path = (dUrlPrivate.GetChildMemberWithName('path').summary or "").strip('"')
    port = dUrlPrivate.GetChildMemberWithName('port').signed
    user = (dUrlPrivate.GetChildMemberWithName('userName').summary or "").strip('"')
    password = (dUrlPrivate.GetChildMemberWithName('password').summary or "").strip('"')
    query = (dUrlPrivate.GetChildMemberWithName('query').summary or "").strip('"')
    fragment = (dUrlPrivate.GetChildMemberWithName('fragment').summary or "").strip('"')

    if any([scheme, host, path, port, user, password]):
        summary = scheme + '://' if scheme else ''
        summary += user + ':' + password + '@' if user else ''
        summary += host if host else ''
        summary += ':%i' % port if port > 0 else ''
        summary += path if path else ''
        summary += "?%s" % query if query else ''
        summary += "#%s" % fragment if fragment else ''
    else:
        return None

    return '"%s"' % summary

class QUrlProvider:
    def __init__(self, valobj, _):
        self.valobj = valobj
        self.urlPrivateType = None
        self.dUrlPrivate = None
        self.d = None
        self.children = []
    
    def hasChildren(self):
        return True
    
    def num_children(self):
        return len(self.children)

    @output_exceptions
    def get_child_at_index(self, index):
        return self.children[index]
    
    @output_exceptions
    def update(self):
        target = lldb.debugger.GetSelectedTarget()
        self.urlPrivateType = target.FindFirstType("QUrlPrivate")

        self.d = self.valobj.GetNonSyntheticValue().GetChildMemberWithName('d')
        self.dUrlPrivate = self.d.CreateChildAtOffset("urlprivate", 0, self.urlPrivateType)

        self.children = list(filter(lambda child: child.GetError().Success(), [
            self.dUrlPrivate.GetChildMemberWithName('scheme'),
            self.dUrlPrivate.GetChildMemberWithName('userName'),
            self.dUrlPrivate.GetChildMemberWithName('password'),
            self.dUrlPrivate.GetChildMemberWithName('host'),
            self.dUrlPrivate.GetChildMemberWithName('port'),
            self.dUrlPrivate.GetChildMemberWithName('path'),
            self.dUrlPrivate.GetChildMemberWithName('query'),
            self.dUrlPrivate.GetChildMemberWithName('fragment'),
        ]))


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
def envpair_summary(valobj: lldb.SBValue, idict, options):
    key = valobj.GetChildMemberWithName('first').GetChildMemberWithName('name').summary
    value = valobj.GetChildMemberWithName('second').GetChildMemberWithName('first').summary
    return "{%s => %s}" % (key, value)

@output_exceptions
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

@output_exceptions
def qstringview_summary(valobj: lldb.SBValue, idict, options):
    type = valobj.GetType().GetBasicType(lldb.eBasicTypeChar16)
    data = valobj.GetNonSyntheticValue().GetChildMemberWithName('m_data')
    size = valobj.GetNonSyntheticValue().GetChildMemberWithName('m_size').signed

    size = max(size, 0)

    addr = data.AddressOf().Dereference().unsigned
    ptr = valobj.CreateValueFromAddress('test', addr, type)

    return '"%s"' % stringFromSummary(ptr.AddressOf().summary)[:size]

@output_exceptions
def qjsonarray_summary(valobj: lldb.SBValue, idict, options):
    target = lldb.debugger.GetSelectedTarget()
    tPrivate = target.FindFirstType("QCborContainerPrivate")
    d = valobj.GetNonSyntheticValue().GetChildMemberWithName('a').GetChildMemberWithName('d')
    dc = d.CreateChildAtOffset('[private]', 0, tPrivate);
    elements = dc.GetChildMemberWithName('elements')
    elements.SetPreferSyntheticValue(True)

    numElements = elements.GetNumChildren()
    return "size=%i" % numElements

class JsonArrayChildProvider:
    def __init__(self, valobj, idict):
        self.valobj = valobj
    
    def hasChildren(self):
        return True
    
    def num_children(self):
        return self.numElements + 1

    def get_child_at_index(self, index):
        if index < self.numElements:
            return self.elements.GetChildAtIndex(index)
        return self.dc

    def update(self):
        try:
            target = lldb.debugger.GetSelectedTarget()
            tPrivate = target.FindFirstType("QCborContainerPrivate")
            d = self.valobj.GetNonSyntheticValue().GetChildMemberWithName('a').GetChildMemberWithName('d')
            self.dc = d.CreateChildAtOffset('[private]', 0, tPrivate);
            self.elements = self.dc.GetChildMemberWithName('elements')
            self.elements.SetPreferSyntheticValue(True)
            self.numElements = self.elements.GetNumChildren() #  GetValueForExpressionPath('.d.size').unsigned
        except:
            pass

@output_exceptions
def qjsonobject_summary(valobj: lldb.SBValue, idict, options):
    target = lldb.debugger.GetSelectedTarget()
    tPrivate = target.FindFirstType("QCborContainerPrivate")
    d = valobj.GetNonSyntheticValue().GetChildMemberWithName('o').GetChildMemberWithName('d')
    dc = d.CreateChildAtOffset('[private]', 0, tPrivate);
    elements = dc.GetChildMemberWithName('elements')
    elements.SetPreferSyntheticValue(True)

    numElements = elements.GetNumChildren()
    return "size=%i" % numElements

class JsonObjectChildProvider:
    def __init__(self, valobj, idict):
        self.valobj = valobj
    
    def hasChildren(self):
        return True
    
    def num_children(self):
        return self.numElements + 1

    def get_child_at_index(self, index):
        if index < self.numElements:
            return self.elements.GetChildAtIndex(index)
        return self.dc

    def update(self):
        try:
            target = lldb.debugger.GetSelectedTarget()
            tPrivate = target.FindFirstType("QCborContainerPrivate")
            d = self.valobj.GetNonSyntheticValue().GetChildMemberWithName('o').GetChildMemberWithName('d')
            self.dc = d.CreateChildAtOffset('[private]', 0, tPrivate);
            self.elements = self.dc.GetChildMemberWithName('elements')
            self.elements.SetPreferSyntheticValue(True)
            self.numElements = self.elements.GetNumChildren() #  GetValueForExpressionPath('.d.size').unsigned
        except:
            pass

@output_exceptions
def registerTypeSummary(category, typeName, functionOrString, typeNameIsRegularExpression=False, options=None):
    '''Register a summary provider for a type.'''
    typeSpecifier = lldb.SBTypeNameSpecifier(typeName, typeNameIsRegularExpression)
    if isinstance(functionOrString, str):
        summary = lldb.SBTypeSummary().CreateWithSummaryString(functionOrString)
    else:
        summary = lldb.SBTypeSummary().CreateWithFunctionName("%s.%s" %(__name__, functionOrString.__name__))
    if options:
        summary.SetOptions(options)
    
    category.AddTypeSummary(typeSpecifier, summary)
    #print("%s => %s" % (typeSpecifier, summary))
    return summary

@output_exceptions
def registerTypeSynthetic(category, typeName, cls, typeNameIsRegularExpression=False):
    '''Register a synthetic provider for a type.'''
    typeSpecifier = lldb.SBTypeNameSpecifier(typeName, typeNameIsRegularExpression)
    typeSynthetic = lldb.SBTypeSynthetic().CreateWithClassName("%s.%s" %(__name__, cls.__name__))
    category.AddTypeSynthetic(typeSpecifier, typeSynthetic)
    #print("%s => %s" % (typeSpecifier, typeSynthetic))
    return typeSynthetic


@output_exceptions
def __lldb_init_module(debugger, dict):
    print("Loading MAD extensions...")

    ################################################################################
    # Qt Extensions

    madCategory = debugger.CreateCategory('MAD')
    madCategory.SetEnabled(True)

    registerTypeSummary(madCategory, "QString", qstring_summary)
    registerTypeSynthetic(madCategory, "QString", QStringProvider)

    registerTypeSummary(madCategory, "QObject", qobject_summary)
    registerTypeSynthetic(madCategory, "QObject", QObjectChildProvider)

    registerTypeSummary(madCategory, "QFile", qfile_summary)

    registerTypeSummary(madCategory, "QFileInfo", "${var.d_ptr.d.fileEntry.m_filePath}")

    registerTypeSummary(madCategory, "QUrl", qurl_summary)
    registerTypeSynthetic(madCategory, "QUrl", QUrlProvider)

    registerTypeSummary(madCategory, "QStringView", qstringview_summary)

    registerTypeSummary(madCategory, "QByteArray", "size=${var.d.size}")

    registerTypeSummary(madCategory, "QTextCursor", qtextcursor_summary)

    registerTypeSummary(madCategory, "^QList<.+>$", "size=${svar%#}", True)
    registerTypeSynthetic(madCategory, "^QList<.+>$", QListChildProvider, True)

    registerTypeSummary(madCategory, "QVariant", "<placeholder>", False, lldb.eTypeOptionShowOneLiner)
    registerTypeSynthetic(madCategory, "QVariant", QVariantChildProvider)

    registerTypeSummary(madCategory, "^Q.*Application$", qcoreapplication_summary, True)

    registerTypeSummary(madCategory, "^QMap<.+>$",  "${var.d.d.m}", True)
    registerTypeSynthetic(madCategory, "^QMap<.+>$", QMapChildProvider, True)

    registerTypeSummary(madCategory, "QJsonArray", qjsonarray_summary)
    registerTypeSynthetic(madCategory, "QJsonArray", JsonArrayChildProvider)

    registerTypeSummary(madCategory, "QJsonObject", qjsonobject_summary)
    registerTypeSynthetic(madCategory, "QJsonObject", JsonObjectChildProvider)


    ################################################################################
    # Qt Creator extensions

    qtcCategory = debugger.CreateCategory('QTC')
    qtcCategory.SetEnabled(True)

    registerTypeSummary(qtcCategory, "^std::__[[:alnum:]]+::pair<const Utils::DictKey, std::__[[:alnum:]]+::pair<QString, bool> >", envpair_summary, True)

    registerTypeSummary(qtcCategory, "Utils::FilePath", "${var.m_scheme},${var.m_host},${var.m_root},${var.m_path}")
    registerTypeSummary(qtcCategory, "Utils::FilePaths", "size=${svar%#}")
    registerTypeSynthetic(qtcCategory, "Utils::FilePaths", QListChildProvider)


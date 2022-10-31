#include <QCoreApplication>

#include <QList>
#include <QDebug>
#include <QVariant>
#include <QRect>
#include <QMap>

#include <memory>
#include <QHash>
#include <QFile>
#include <QFileInfo>
#include <QPair>
#include <QUrl>
#include <QTextCursor>
#include <QTextDocument>

#include <QStringView>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonValue>

#include <vector>

void chk() {}

void qString()
{
    QStringList test({"Hallo", "Welt"});
#if QT_VERSION >= QT_VERSION_CHECK(6, 0, 0)
    chk(); // CHECK("test", None, {'[0]': '"Hallo"', '[1]': '"Welt"'})
#else
    chk(); // CHECK("test", None, { 0: {'[0]': '"Hallo"', '[1]': '"Welt"'}})
#endif

    std::vector<QString> testVector{"Hallo", "Welt"};
    chk(); // CHECK("testVector", "size=2", {'[0]': '"Hallo"', '[1]': '"Welt"'} )

    std::unique_ptr<QStringList> testPtr = std::make_unique<QStringList>();
    *testPtr << "UNique";
    *testPtr << "Ptr";

    QString floatString = "Just a float?";
    chk(); // CHECK_SUMMARY("floatString", '"Just a float?"')

    QStringView sv(floatString);
    chk(); // CHECK_SUMMARY("sv", '"Just a float?"')

    QStringView svMid = sv.mid(4);
    chk(); // CHECK_SUMMARY("svMid", '" a float?"')

    QStringView svLeft = sv.left(4);
    chk(); // CHECK_SUMMARY("svLeft", '"Just"')
}

void qObject()
{
    QObject *qObj = new QObject();
    qObj->setObjectName("Object_Name_Here");
    chk(); // CHECK_SUMMARY("qObj", '{"Object_Name_Here"}')

    QObject *qObjNoName = new QObject(qObj);
    qObjNoName->setProperty("Test", "Hallo");
    qObjNoName->setProperty("2te Property", 1234);
}

void qMap()
{
    QMap<QString, QMap<QString, int>> testMap;
    QMap<QString, int> testiMap;
    testiMap["1"] = 1;
    testMap["key"] = testiMap;
    QVariant mapVar = QVariant::fromValue(testMap);
    QMap<QString, float> floatMap;
    floatMap["key1"] = 1.01234f;
    floatMap["key2"] = 2.01234f;
    floatMap["key3"] = 3.01234f;
    floatMap["key4"] = 4.01234f;
}

void qVariant()
{
    QVariant emptyVar;
    QVariant intVar(1234);
    QVariant floatVar(0.1234);
    QVariant stringVar(QString("Hallo Welt! Ihr bubbas seid ja mal blah blah blah blah blah blah blah"));
    QVariant byteVar(QByteArray("awfoiaf\1oaw\2hifafohwaof"));

    intVar = "Hallo Welt du int";

    QRect r(0, 0, 100, 100);
    QVariant rectVar(r);

    QVariant sharedVar(stringVar);
}

void qHash()
{
    QHash<int, QPair<int, int>> testHash;
    testHash[10] = QPair<int, int>(10, 12);

    for (auto it = testHash.begin(); it != testHash.end(); ++it)
    {
        qDebug() << it.key();
    }
}

void json()
{
    QJsonArray arr({123, 234, 533});

    QJsonObject obj({{"key1", "value1"}, {"key2", "value2"}});

    qDebug() << arr;
    qDebug() << obj;
}

void file()
{
    QFile f("/tmp/test.txt");
    f.open(QIODevice::WriteOnly | QIODevice::Append);
    chk(); // CHECK_SUMMARY("f", "{filename=/tmp/test.txt, openmode=write|append, error=NoError}")

    QFileInfo fInfo("/tmp/test.txt");
}

void textCursor()
{
    QTextDocument doc;
    doc.setHtml("<p>Hallo Welt</p>");

    QTextCursor cursor(&doc);
    cursor.setPosition(2);
    cursor.movePosition(QTextCursor::MoveOperation::Right, QTextCursor::KeepAnchor, 10);
    chk(); // CHECK_SUMMARY("cursor", "{pos=10, anchor=2}")
}

void url()
{
    QUrl url("http://www.google.de");
    chk(); // CHECK_SUMMARY("url", '"http://www.google.de"')

    QUrl fileUrl = QUrl::fromLocalFile("/tmp/test.txt");
    QUrl portUrl("http://127.0.0.1:8888/admin");

    QUrl userPortUrl("http://user:pass@127.0.0.1:8888/admin");
    chk(); // CHECK_SUMMARY("userPortUrl", '"http://user:pass@127.0.0.1:8888/admin"')

    QUrl userPortFragmentUrl("http://user:pass@127.0.0.1:8888/admin?x=y&z=1#anchor");
    chk(); // CHECK_SUMMARY("userPortFragmentUrl", '"http://user:pass@127.0.0.1:8888/admin?x=y&z=1#anchor"')

    QUrl empty;
    chk(); // CHECK_SUMMARY("empty", 'None')

    QUrl relative("test.txt");
    chk(); // CHECK_CHILDREN("relative", { 'scheme': '""', 'userName': '""', 'password': '""', 'host': '""', 'port': -1, 'path': '"test.txt"', 'query': '""', 'fragment': '""' })

    QUrl *ptr = new QUrl("I am a pointer");
    chk(); // CHECK_SUMMARY("ptr", '"I am a pointer"')

    QUrl *invalidPtr = (QUrl*)0x1234;
    chk(); // CHECK_CHILDREN("invalidPtr", {})

    QUrl *nullPtr = nullptr;
    nullPtr = new QUrl("I was null but now i'm valid");

    auto uniquePtr = std::make_unique<QUrl>("I am a unique pointer");
    chk(); // CHECK_CHILDREN("uniquePtr", {0: { 'scheme': '""', 'userName': '""', 'password': '""', 'host': '""', 'port': -1, 'path': '"I am a unique pointer"', 'query': '""', 'fragment': '""' }})
}

void qList() 
{
    using ComplexType = std::pair<int, QString>;

    QList<int> empty;
    chk(); // CHECK_SUMMARY("empty", 'size=0')

    QList<int> someInts{1,2,3,4};
    qDebug() << "XXXXXX:" << someInts;
    chk(); // CHECK("someInts", 'size=4', {'[0]': 1, '[1]': 2, '[2]': 3, '[3]': 4})

    QList<QString> stringList{"one", "two", "three"};
    chk(); // CHECK("stringList", 'size=3', {'[0]': '"one"', '[1]': '"two"', '[2]': '"three"'})

    ComplexType ct{1, "Hallo"};
    chk(); // CHECK_CHILDREN("ct", {'first': 1, 'second': '"Hallo"'})

    QList<ComplexType> someComplexTypes{ComplexType(1, "one"), ComplexType(2, "two"), ComplexType(3, "three")};
    chk(); // CHECK("someComplexTypes", 'size=3', {'[0]': {"first": 1, "second": '"one"'}, '[1]': {"first": 2, "second": '"two"'}, '[2]': {"first": 3, "second": '"three"'}})

    someComplexTypes.erase(someComplexTypes.begin());
    chk(); // CHECK("someComplexTypes", 'size=2', {'[0]': {"first": 2, "second": '"two"'}, '[1]': {"first": 3, "second": '"three"'}})
}

int main(int argc, char *argv[])
{
    QCoreApplication a(argc, argv);

    qDebug() << "Qt Version: " << qVersion();

    json();
    url();
    textCursor();
    file();
    qVariant();
    qHash();
    qMap();
    qObject();
    qString();
    qList();

    float floatValue = 1.0f;

    return 0;
}

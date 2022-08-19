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

void qString()
{
    QStringList test({"Hallo", "Welt"});

    std::vector<QString> testVector{"Hallo", "Welt"};

    std::unique_ptr<QStringList> testPtr = std::make_unique<QStringList>();
    *testPtr << "UNique";
    *testPtr << "Ptr";

    QString floatString = "Just a float?";

    QStringView sv(floatString);
    QStringView svMid = sv.mid(4);

    QStringView svLeft = sv.left(4);
}

void qObject()
{
    QObject *qObj = new QObject();
    qObj->setObjectName("Object_Name_Here");

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
    f.open(QIODevice::WriteOnly | QIODevice::ExistingOnly | QIODevice::Append);

    QFileInfo fInfo("/tmp/test.txt");
}

void textCursor()
{
    QTextDocument doc;
    doc.setHtml("<p>Hallo Welt</p>");

    QTextCursor cursor(&doc);
    cursor.setPosition(2);
    cursor.movePosition(QTextCursor::MoveOperation::Right, QTextCursor::KeepAnchor, 10);
}

void url()
{
    QUrl url("http://www.google.de");
    // CHECK_SUMMARY("url", '"http://www.google.de"');

    QUrl fileUrl = QUrl::fromLocalFile("/tmp/test.txt");
    QUrl portUrl("http://127.0.0.1:8888/admin");

    QUrl userPortUrl("http://user:pass@127.0.0.1:8888/admin");
    // CHECK_SUMMARY("userPortUrl", '"http://user:pass@127.0.0.1:8888/admin"');

    QUrl empty;
    // CHECK_SUMMARY("empty", 'None');

    QUrl relative("test.txt");
    // CHECK_CHILDREN("relative", {'scheme': '""', 'host': '""', 'path': '"test.txt"', 'port': -1, 'userName': '""', 'password': '""'})

    QUrl *ptr = new QUrl("I am a pointer");

    QUrl *invalidPtr = (QUrl*)0x1234;
    // CHECK_CHILDREN("invalidPtr", {})

    QUrl *nullPtr = nullptr;
    nullPtr = new QUrl("I was null but now i'm valid");

    auto uniquePtr = std::make_unique<QUrl>("I am a unique pointer");
    // CHECK_CHILDREN("uniquePtr", {'__value_': { 'scheme': '""', 'host': '""', 'path': '"I am a unique pointer"', 'port': -1, 'userName': '""', 'password': '""' }})
}

void qList() 
{
    QList<int> empty;
    // CHECK_SUMMARY("empty", 'size=0');

    QList<int> someInts{1,2,3,4};
    // CHECK("someInts", 'size=4', {'[0]': 1, '[1]': 2, '[2]': 3, '[3]': 4})
}

int main(int argc, char *argv[])
{
    QCoreApplication a(argc, argv);

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

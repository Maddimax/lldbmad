#include <QCoreApplication>

#include <QList>
#include <QDebug>
#include <QVariant>
#include <QRect>
#include <QMap>

#include <memory>
#include <QHash>
#include <QFile>
#include <QPair>
#include <QUrl>

#include <QStringView>

#include <vector>

int main(int argc, char *argv[])
{
    QCoreApplication a(argc, argv);

    float floatValue = 1.0f;

    QStringList test({"Hallo", "Welt"});

    std::vector<QString> testVector{"Hallo", "Welt"};

    std::unique_ptr<QStringList> testPtr = std::make_unique<QStringList>();
    *testPtr << "UNique";
    *testPtr << "Ptr";

    QObject* qObj = new QObject();
    qObj->setObjectName("Object_Name_Here");

    QObject* qObjNoName = new QObject(qObj);
    qObjNoName->setProperty("Test", "Hallo");
    qObjNoName->setProperty("2te Property", 1234);
    //QObject::staticMetaObject()

    QMap<QString, QMap<QString, int>> testMap;
    QMap<QString,int> testiMap;
    testiMap["1"] = 1;
    testMap["key"] = testiMap;
    QVariant mapVar = QVariant::fromValue(testMap);

    QMap<QString, float> floatMap;
    floatMap["key1"] = 1.01234f;
    floatMap["key2"] = 2.01234f;
    floatMap["key3"] = 3.01234f;
    floatMap["key4"] = 4.01234f;

    QString floatString = "Just a float?";

    QVariant emptyVar;
    QVariant intVar(1234);
    QVariant floatVar(0.1234);
    QVariant stringVar(QString("Hallo Welt! Ihr bubbas seid ja mal blah blah blah blah blah blah blah"));
    QVariant byteVar(QByteArray("awfoiaf\1oaw\2hifafohwaof"));

    intVar = "Hallo Welt du int";

    QRect r(0, 0, 100, 100);
    QVariant rectVar(r);

    QVariant sharedVar(stringVar);

    QHash<int, QPair<int, int>> testHash;
    testHash[10] = QPair<int, int>(10, 12);

    for(auto it = testHash.begin(); it != testHash.end(); ++it) {
        qDebug() << it.key();
    }

    char* x = new char[128];

    strcpy(x, "Hallo Welt");

    QFile f("/tmp/test.txt");
    f.open(QIODevice::WriteOnly|QIODevice::ExistingOnly|QIODevice::Append);

    QUrl url("http://www.google.de");
    QUrl fileUrl = QUrl::fromLocalFile("/tmp/test.txt");
    QUrl portUrl("http://127.0.0.1:8888/admin");
    QUrl userPortUrl("http://user:pass@127.0.0.1:8888/admin");

    qDebug() << test;

    
    QStringView sv(floatString);
    QStringView svMid = sv.mid(4); 

    QStringView svLeft = sv.left(4);

    //QObjectPrivate

    qVersion();

    return a.exec();    
}

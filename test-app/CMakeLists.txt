set(CMAKE_AUTOUIC ON)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)


find_package(QT NAMES Qt6 Qt5 REQUIRED COMPONENTS Core Gui Test)
find_package(Qt${QT_VERSION_MAJOR} REQUIRED COMPONENTS Core Gui Test)

if (${QT_VERSION_MAJOR} EQUAL 5)
  set(CMAKE_OSX_ARCHITECTURES "x86_64")
endif()

add_executable(lldbtest
  main.cpp
)
target_link_libraries(lldbtest Qt${QT_VERSION_MAJOR}::Core Qt${QT_VERSION_MAJOR}::Test Qt${QT_VERSION_MAJOR}::Gui)



find_program(LLDB_PATH lldb)

if (NOT LLDB_PATH)
    message(FATAL_ERROR "Could not find lldb")
endif()

message(STATUS "Lldb path: ${LLDB_PATH}")

add_test(
    NAME lldb-dumpers 
    COMMAND ${LLDB_PATH} 
        $<TARGET_FILE:lldbtest>
        --no-lldbinit
        --one-line "command script import ${CMAKE_CURRENT_SOURCE_DIR}/lldbmad.py"
        --one-line "command script import ${CMAKE_CURRENT_SOURCE_DIR}/tests/test.py"
        -o quit
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/..)


add_custom_target(check 
    COMMAND 
        ${LLDB_PATH} 
        $<TARGET_FILE:lldbtest>
        --no-lldbinit
        --one-line "command script import ${CMAKE_CURRENT_SOURCE_DIR}/../lldbmad.py"
        --one-line "command script import ${CMAKE_CURRENT_SOURCE_DIR}/test.py"
        -o quit
    DEPENDS lldbtest
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/..)
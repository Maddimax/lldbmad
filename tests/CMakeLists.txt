find_program(LLDB_PATH lldb)

if (NOT LLDB_PATH)
    message(FATAL_ERROR "Could not find lldb")
endif()

message(STATUS "Lldb path: ${LLDB_PATH}")

execute_process(COMMAND ${LLDB_PATH} -P OUTPUT_VARIABLE LLDB_PYTHON_PATH OUTPUT_STRIP_TRAILING_WHITESPACE)

add_test(
    NAME lldb-dumpers 
    COMMAND xcrun python3 tests/test.py $<TARGET_FILE:lldbtest>
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/..)

set_tests_properties(lldb-dumpers PROPERTIES ENVIRONMENT "PYTHONPATH=${LLDB_PYTHON_PATH}")

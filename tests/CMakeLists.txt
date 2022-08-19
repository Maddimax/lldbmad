find_program(LLDB_PATH lldb)

if (NOT LLDB_PATH)
    message(FATAL_ERROR "Could not find lldb")
endif()

message(STATUS "Lldb path: ${LLDB_PATH}")

add_test(
    NAME lldb-dumpers 
    COMMAND ${LLDB_PATH} 
        $<TARGET_FILE:lldbtest>
        --one-line "command script import tests/test.py"
        -o quit
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/..)


add_custom_target(check 
    COMMAND 
        ${CMAKE_COMMAND} -E env CTEST_OUTPUT_ON_FAILURE=1
        ${CMAKE_CTEST_COMMAND}
    DEPENDS lldbtest)
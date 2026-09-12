# zan_hello main component: zanc object + ESP-IDF adapter + the runtime
# sources the bare-metal target needs (rt_timer.c supplies the coroutine
# timer reactor and the fail-soft fault reports; ZAN_BARE_METAL selects the
# single-thread, no-signal branch).
set(ZAN_SRC ${CMAKE_CURRENT_SOURCE_DIR}/hello.zan)
set(ZAN_OBJ ${CMAKE_CURRENT_BINARY_DIR}/zan_hello.o)

find_program(ZANC zanc)
if(NOT ZANC)
    message(FATAL_ERROR
        "zanc not found on PATH. Install the zan toolchain (or point CMake "
        "at it: idf.py -DZANC=/path/to/zanc build), then rebuild. The "
        "compiler is needed to turn hello.zan into an rv32 object.")
endif()

# Regenerate the rv32 object whenever the program or the compiler changes.
add_custom_command(OUTPUT ${ZAN_OBJ}
    COMMAND ${ZANC} ${ZAN_SRC} --auto-stdlib --publish --target riscv32
            -o ${ZAN_OBJ}
    DEPENDS ${ZAN_SRC}
    VERBATIM)

# zanc_root: directory holding zanc; the runtime sources sit at
# <repo>/src/runtime next to the compiler. Override when zanc is installed
# standalone (no source checkout): copy rt_timer.c/rt_timer.h into main/.
cmake_path(GET ZANC PARENT_PATH ZANC_DIR)
if(EXISTS "${ZANC_DIR}/../src/runtime/rt_timer.c")
    set(ZAN_RT_DIR "${ZANC_DIR}/../src/runtime")
else()
    set(ZAN_RT_DIR ${CMAKE_CURRENT_SOURCE_DIR}/rt)
endif()

idf_component_register(
    SRCS "zan_adapter.c" "${ZAN_RT_DIR}/rt_timer.c"
    INCLUDE_DIRS "${ZAN_RT_DIR}/.."
    PRIV_REQUIRES pthread vfs)   # pthread_mutex_* / poll resolution

set_source_files_properties("${ZAN_RT_DIR}/rt_timer.c" PROPERTIES
    COMPILE_DEFINITIONS "ZAN_BARE_METAL")

# The zan object is machine code already; wrap it in a tiny archive so the
# component can link it like any library.
add_library(zan_hello_obj STATIC ${ZAN_OBJ})
set_target_properties(zan_hello_obj PROPERTIES LINKER_LANGUAGE C)
target_link_libraries(${COMPONENT_LIB} PRIVATE zan_hello_obj)

cmake_minimum_required(VERSION 2.8.12)
project (lmdb C)

include(conanbuildinfo.cmake)
conan_basic_setup()

set (CMAKE_DEBUG_POSTFIX "d")

set (SOURCES_PATH "source_subfolder/libraries/liblmdb")

add_library(lmdb ${SOURCES_PATH}/mdb.c 
                 ${SOURCES_PATH}/midl.c)

install(TARGETS lmdb)
install(FILES ${SOURCES_PATH}/lmdb.h DESTINATION include)
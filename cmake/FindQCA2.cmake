# - Try to find QCA2 (Qt Cryptography Architecture 2)
# Once done this will define
#
#  QCA2_FOUND - system has QCA2
#  QCA2_INCLUDE_DIR - the QCA2 include directory
#  QCA2_LIBRARY - the libraries needed to use QCA2
#  QCA2_DEFINITIONS - Compiler switches required for using QCA2
#
# use pkg-config to get the directories and then use these values
# in the FIND_PATH() and FIND_LIBRARY() calls

# Copyright (c) 2006, Michael Larouche, <michael.larouche@kdemail.net>
# Copyright (c) 2014, Larry Shaffer, <larrys (at) dakotacarto (dot) com>
#
# Redistribution and use is allowed according to the terms of the BSD license.
# For details see the accompanying COPYING-CMAKE-SCRIPTS file.

#include(FindLibraryWithDebug)

if(QCA2_INCLUDE_DIR AND QCA2_LIBRARY)

  # in cache already
  set(QCA2_FOUND TRUE)

else(QCA2_INCLUDE_DIR AND QCA2_LIBRARY)

  if(APPLE)

    include(CMakeFindFrameworks)
    cmake_find_frameworks(qca)
    if (qca_FRAMEWORKS)
      set(QCA2_LIBRARY "-framework qca -L${qca_FRAMEWORKS}" CACHE FILEPATH "QCA framework" FORCE)
      set(QCA2_INCLUDE_DIR "${qca_FRAMEWORKS}/Headers" CACHE FILEPATH "QCA framework headers" FORCE)
      set(QCA2_FOUND TRUE)
    endif (qca_FRAMEWORKS)

  endif(APPLE)

  if(NOT QCA2_FOUND)

    if(NOT WIN32)

      find_package(PkgConfig)
      pkg_check_modules(PC_QCA2 QUIET qca2)
      set(QCA2_DEFINITIONS ${PC_QCA2_CFLAGS_OTHER})

    endif(NOT WIN32)

    find_library(QCA2_LIBRARY
      WIN32_DEBUG_POSTFIX d
      NAMES qca qca2
      PATHS
        ${LIB_DIR}
        $ENV{LIB}
        "$ENV{LIB_DIR}"
        /usr/local/lib
      HINTS ${PC_QCA2_LIBDIR} ${PC_QCA2_LIBRARY_DIRS}
    )

    find_path(QCA2_INCLUDE_DIR
      NAMES QtCrypto
      PATHS
        ${LIB_DIR}/include
        "$ENV{LIB_DIR}/include"
        $ENV{INCLUDE}
        /usr/local/include
      HINTS ${PC_QCA2_INCLUDEDIR} ${PC_QCA2_INCLUDE_DIRS}
      PATH_SUFFIXES QtCrypto qt4/QtCrypto
    )

    include(FindPackageHandleStandardArgs)
    find_package_handle_standard_args(QCA2  DEFAULT_MSG  QCA2_LIBRARY QCA2_INCLUDE_DIR)

  endif(NOT QCA2_FOUND)

  mark_as_advanced(QCA2_INCLUDE_DIR QCA2_LIBRARY)

endif(QCA2_INCLUDE_DIR AND QCA2_LIBRARY)
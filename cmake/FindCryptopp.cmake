# Find Crypto++
# ~~~~~~~~
# Copyright (c) 2014, Larry Shaffer <larrys at dakotacarto dot com>
#
# Redistribution and use is allowed according to the terms of the BSD license.
# For details see the accompanying COPYING-CMAKE-SCRIPTS file.
#
# Once run this will define:
#
# CRYPTOPP_FOUND       = system has QwtPolar lib
# CRYPTOPP_LIBRARY     = full path to the QwtPolar library
# CRYPTOPP_INCLUDE_DIR = where to find headers
#
# Initially culled from the cryptoface project:
# https://github.com/harningt/cryptoface
#
# = cryptoface LICENSE TEXT =
#
# == MIT ==
# Copyright (c) 2008-2011 Thomas Harning Jr.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.



if(CRYPTOPP_INCLUDE_DIR AND CRYPTOPP_LIBRARY)
   set(CRYPTOPP_FOUND TRUE)

else(CRYPTOPP_INCLUDE_DIR AND CRYPTOPP_LIBRARY)

  find_path(CRYPTOPP_INCLUDE_DIR cryptlib.h PATHS
      /usr/include
      /usr/local/include
      /opt/local/include
      $ENV{SystemDrive}/Crypto++/include
      PATH_SUFFIXES cryptopp crypto++
      )

  find_library(CRYPTOPP_LIBRARY NAMES cryptopp crypto++ PATHS
      /usr/lib
      /usr/local/lib
      /opt/local/lib
      $ENV{SystemDrive}/Crypto++/lib
      )

  if(CRYPTOPP_INCLUDE_DIR AND CRYPTOPP_LIBRARY)
    set(CRYPTOPP_FOUND TRUE)
    if(NOT QWTPOLAR_FIND_QUIETLY)
      message(STATUS "Found Crypto++: ${CRYPTOPP_INCLUDE_DIR}, ${CRYPTOPP_LIBRARY}")
    endif(NOT QWTPOLAR_FIND_QUIETLY)
  else(CRYPTOPP_INCLUDE_DIR AND CRYPTOPP_LIBRARY)
    set(CRYPTOPP_FOUND FALSE)
    if(CRYPTOPP_FIND_REQUIRED)
      message(FATAL_ERROR "Crypto++ not found")
    endif(CRYPTOPP_FIND_REQUIRED)
  endif(CRYPTOPP_INCLUDE_DIR AND CRYPTOPP_LIBRARY)

  mark_as_advanced(CRYPTOPP_INCLUDE_DIR CRYPTOPP_LIBRARY)

endif(CRYPTOPP_INCLUDE_DIR AND CRYPTOPP_LIBRARY)

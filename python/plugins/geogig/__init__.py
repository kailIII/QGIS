# -*- coding: utf-8 -*-

import sys
import os
import site

site.addsitedir(os.path.abspath(os.path.dirname(__file__) + '/ext-libs'))

def classFactory(iface):
    from geogig.plugin import GeoGigPlugin
    return GeoGigPlugin(iface)

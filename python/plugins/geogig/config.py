from PyQt4.QtCore import *

iface = None
explorer = None

GENERAL = "General"
                        
CLONE_PARENT_PATH = "CloneParentPath"
CLONE_DIRECTLY = "CloneDirectly"
USE_THREADS = "UseThreads"
AUTO_UPDATE = "AutoUpdate"
GATEWAY_PORT = "GatewayPort"
ENABLE_SMART_UPDATE = "EnableSmartUpdate"
AUTO_ADD_ID = "AutoAddId"
UJO_ENDPOINT = "UjoEndpoint"

generalParams = [                         
                 (CLONE_PARENT_PATH, "Preferred parent path for Ujo copied repositories", ""),
                 (CLONE_DIRECTLY, "Copy directly into preferred path without asking", False),
                 (AUTO_UPDATE, "Automatically import tracked layers after they are edited", False),
                 (AUTO_ADD_ID, "Automatically add 'geogigid' field without asking", False),
                 (GATEWAY_PORT, "Port for GeoGig gateway", 25333),
                 (UJO_ENDPOINT, "Ujo endpoint", "http://ujo.dev.boundlessgeo.com/cli-api"),
                 (ENABLE_SMART_UPDATE, "Enable smart update when layers are edited", True)]
                          
def getConfigValue(group, name):
    default = None
    for param in generalParams:
        if param[0] == name:
            default = param[2]
    
    if isinstance(default, bool):
        return QSettings().value("/GeoGig/Settings/%s/%s" % (group, name), default, bool)
    else:
        return QSettings().value("/GeoGig/Settings/%s/%s" % (group, name), default, str) 

def setConfigValue(group, name, value):
    return QSettings().setValue("/GeoGig/Settings/%s/%s" % (group, name), value)

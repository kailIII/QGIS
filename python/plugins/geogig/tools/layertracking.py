import os
from qgis.core import *
from geogig.tools.utils import userFolder, tempFolder
import json
from json.decoder import JSONDecoder
from json.encoder import JSONEncoder
from geogig.tools.repodecorator import LocalRepository
from geogig.tools.layers import getVectorLayers
from geogig.gui.dialogs.updatelayersdialog import UpdateLayersDialog

tracked = []

class Encoder(JSONEncoder):
    def default(self, o):
        return o.__dict__

def decoder(jsonobj):
    if 'source' in jsonobj:
        return TrackedLayer(jsonobj['source'], jsonobj['url'], 
                            jsonobj['dest'], jsonobj['insync'])
    else:
        return jsonobj

class TrackedObject(object):
    pass

class TrackedLayer(TrackedObject):
    def __init__(self, source, url, dest, inSync):
        self.url = url
        self.dest = dest
        self.source = source
        self.insync = inSync
    
def setInSync(layer, insync):    
    source = _formatSource(layer)
    for obj in tracked:
        if obj.source == source:
            obj.insync = True
    saveTracked()    
       
def addTrackedLayer(url, source, dest = None):
    global tracked
    source = _formatSource(source)
    layer = TrackedLayer(source, url, dest, True)
    if layer not in tracked:
        for lay in tracked:
            if lay.source == source:
                tracked.remove(lay)
        tracked.append(layer)
        saveTracked()    
        

def removeTrackedLayer(layer):
    global tracked
    source = _formatSource(layer)
    for i, obj in enumerate(tracked):
        if obj.source == source:
            del tracked[i]
            saveTracked()
            return

def cleanTemporaryLayers():
    global tracked
    tmp = os.path.normcase(tempFolder())
    tracked = [t for t in tracked if not t.source.startswith(tmp)]
    saveTracked()

def saveTracked():
    filename = os.path.join(userFolder(), "layers")
    with open(filename, "w") as f:
        f.write(json.dumps(tracked, cls = Encoder))

def readTrackedLayers():
    try:
        global tracked
        filename = os.path.join(userFolder(), "layers")
        if os.path.exists(filename):
            with open(filename) as f:
                lines = f.readlines()
            jsonstring = "\n".join(lines)
            if jsonstring:
                tracked = JSONDecoder(object_hook = decoder).decode(jsonstring)
    except KeyError:
        pass

def isTracked(layer):
    return getTrackingInfo(layer) is not None

def getTrackingInfo(layer):
    source = _formatSource(layer)
    for obj in tracked:
        if obj.source == source:
            return obj.url, obj.dest, obj.insync

    return None

def getTrackedOpenLayersForRepo(repo):
    repoLayers = LocalRepository(repo.url).layers()
    toUpdate = {layer.source:layer for layer in tracked
            if repo.url == layer.url and layer.dest in repoLayers}
    vlayers = getVectorLayers()
    openToUpdate = []
    for layer in vlayers:
        source =_formatSource(layer)
        if source in toUpdate:
            openToUpdate.append((layer, toUpdate[source]))
    return openToUpdate 
        
    
def updateOpenTrackedLayers(repo):
    layers = getTrackedOpenLayersForRepo(repo)
    if layers:
        dlg = UpdateLayersDialog(layers)
        dlg.exec_()    
        for layer in layers:
            setInSync(layer, layer in dlg.updated)   
        
def _formatSource(obj):
    if isinstance(obj, QgsVectorLayer):            
        if obj.dataProvider().name() == "postgres":
            uri = QgsDataSourceURI(obj.dataProvider().dataSourceUri())
            return " ".join([uri.database(), uri.schema(), uri.table()])
        else:
            return os.path.normcase(obj.source())
    else:
        return os.path.normcase(unicode(obj))




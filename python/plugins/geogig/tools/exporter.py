'''
This module provides methods to export layers so they can be used as valid data
for importing to GeoGig.

It also includes method to export from GeoGig to QGIS
'''

import re
import utils
import logging
from qgis.core import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from geogigpy.geogigexception import GeoGigException
from geogig.tools.utils import tempFilenameInTempFolder
from geogig.tools.layertracking import addTrackedLayer

_logger = logging.getLogger("geogigpy")

def exportVectorLayer(layer):
    '''accepts a QgsVectorLayer'''
    settings = QSettings()
    systemEncoding = settings.value( "/UI/encoding", "System" )
    filename = unicode(layer.source())
    destFilename = unicode(layer.name())
    if not filename.lower().endswith("shp"):
        output = utils.tempFilenameInTempFolder(destFilename + ".shp")
        provider = layer.dataProvider()
        fields = layer.pendingFields()
        writer = QgsVectorFileWriter(output, systemEncoding, fields, provider.geometryType(), layer.crs())
        for feat in layer.getFeatures():
            writer.addFeature(feat)
        del writer
        return output
    else:
        return filename


def exportFromGeoGigToTempFile(repo, ref, path):
    #try to import as spatialite (might not work in if sl drivers are not available)
    failed = False
    try:
        filepath = tempFilenameInTempFolder("export.sqlite")
        repo.exportsl(ref, path, filepath, table = path)
        uri = QgsDataSourceURI()
        uri.setDatabase(filepath)
        uri.setDataSource('', path, 'the_geom')
        layer = QgsVectorLayer(uri.uri(), path, 'spatialite')
        failed = not layer.isValid()
    except GeoGigException:
        _logger.debug("Could not export layer %s to spatialite database %s" % (path, filepath))
        failed = True;

    if failed:
        filepath = tempFilenameInTempFolder("export.shp")
        repo.exportshp(ref, path, filepath)
        layer = QgsVectorLayer(filepath, path, "ogr")


    QgsMapLayerRegistry.instance().addMapLayers([layer])
    hasField = layer.dataProvider().fieldNameIndex("geogigid") != -1
    if hasField:
        addTrackedLayer(repo.url, layer.source(), path)
    return hasField

def exportVectorLayerAddingId(layer, fid):
    '''accepts a QgsVectorLayer'''
    settings = QSettings()
    systemEncoding = settings.value( "/UI/encoding", "System" )    
    destFilename = unicode(layer.name())
    output = utils.tempFilenameInTempFolder(destFilename + ".shp")
    provider = layer.dataProvider()
    fields = layer.pendingFields()
    fieldsInFid = re.findall("\[.*?\]", fid)
    fidattrs = {}
    for field in fieldsInFid:
        name = field[1:-1]
        idx = provider.fieldNameIndex(name)
        if idx == -1:
            raise Exception("Field %s not found in layer" % name) 
        fidattrs[field] = idx
    fields.append(QgsField("geogigid", QVariant.String))
    writer = QgsVectorFileWriter(output, systemEncoding, fields, provider.geometryType(), layer.crs())
    outFeat = QgsFeature()    
    for feat in layer.getFeatures():                
        inGeom = feat.geometry()
        outFeat.setGeometry(inGeom)
        attrs = feat.attributes()
        if fid:
            geogitid = fid
            for k,v in fidattrs.iteritems():
                geogitid = geogitid.replace(k, unicode(attrs[v]))
        else:
            geogitid = str(hash(tuple(attrs)))
        attrs.append(geogitid)
        outFeat.setAttributes(attrs)
        writer.addFeature(outFeat)        
        writer.addFeature(feat)
    del writer
    return output


    



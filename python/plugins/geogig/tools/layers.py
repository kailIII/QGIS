from qgis.core import *
from geogig import config
from PyQt4 import QtCore
from geogig.tools.postgis_utils import GeoDB, TableConstraint
from geogig.gui.dialogs.userpasswd import UserPasswordDialog
import uuid

ALL_TYPES = -1

class WrongLayerNameException(BaseException) :
    pass

class WrongLayerSourceException(BaseException) :
    pass

def resolveLayer(name):
    layers = getAllLayers()
    for layer in layers:
        if layer.name() == name:
            return layer
    raise WrongLayerNameException()


def getRasterLayers():
    layers = config.iface.legendInterface().layers()
    raster = list()
    for layer in layers:
        if layer.type() == layer.RasterLayer:
            if layer.providerType() == 'gdal':#only gdal file-based layers
                raster.append(layer)
    return raster


def getVectorLayers(shapetype=-1):
    layers = config.iface.legendInterface().layers()
    vector = list()
    for layer in layers:
        if layer.type() == layer.VectorLayer:
            if shapetype == ALL_TYPES or layer.geometryType() == shapetype:
                uri = unicode(layer.source())
                if not uri.lower().endswith("csv") and not uri.lower().endswith("dbf"):
                    vector.append(layer)
    return vector

def getAllLayers():
    layers = []
    layers += getRasterLayers();
    layers += getVectorLayers();
    return layers


def getGroups():
    groups = {}
    rels = config.iface.legendInterface().groupLayerRelationship()
    for rel in rels:
        groupName = rel[0]
        if groupName != '':
            groupLayers = rel[1]
            groups[groupName] = [QgsMapLayerRegistry.instance().mapLayer(layerid) for layerid in groupLayers]
    return groups

def setIdEditWidget(layer):
    provider = layer.dataProvider()                    
    idx = provider.fieldNameIndex("geogigid")
    if idx != -1:
        field = provider.fields().at(idx)
        layer.setFieldEditable(idx, field.type() != QtCore.QVariant.String)
        if provider.name() != "postgres":   
            layer.setEditType(idx, QgsVectorLayer.UuidGenerator)


def addIdField(layer):    
    layer.blockSignals(True)
    try:
        provider = layer.dataProvider()
        caps = provider.capabilities()
        if provider.name() == "postgres":        
            uri = QgsDataSourceURI(provider.dataSourceUri())
            username,password = getDatabaseCredentials(uri)            
            db =  GeoDB(uri.host(), int(uri.port()), uri.database(), username, password)
            constraints = [c for c in db.get_table_constraints(uri.table(), uri.schema()) 
                           if c.con_type == TableConstraint.TypePrimaryKey]
            if constraints:
                db.table_delete_constraint(uri.table(), constraints[0].name, uri.schema())
            db.table_add_serial_column(uri.schema(), uri.table(), "geogigid")
            db.table_add_primary_key(uri.table(), "geogigid", uri.schema())
            layer.updateFields()
            layer.reload()
            setIdEditWidget(layer)                    
        elif caps & QgsVectorDataProvider.AddAttributes:
            provider.addAttributes([QgsField("geogigid", QtCore.QVariant.String)])
            layer.updateFields()
            idx = provider.fieldNameIndex("geogigid")
            layer.startEditing()
            features = layer.getFeatures()
            for feature in features:
                fid = int(feature.id())
                print layer.changeAttributeValue(fid, idx, str(uuid.uuid4()))
            layer.commitChanges()
            setIdEditWidget(layer)
        else:
            pass
            #TODO handle this
    finally:
        layer.blockSignals(False)        
        
_credentials = {}

def getDatabaseCredentials(uri):
    if uri.password() and uri.username():
        return uri.username(), uri.password()
    global _credentials
    if uri.database() in _credentials:
        return _credentials[uri.database()]            
    dlg = UserPasswordDialog(title = "Credentials for PostGIS layer")
    dlg.exec_()
    if dlg.user is None:
        return None, None
    u = dlg.user
    p = dlg.password
    _credentials[uri.database()] = (u, p)
    return u, p
    
def removeCredentials(database):
    global _credentials
    del _credentials[database]

    
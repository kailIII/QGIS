import os
from qgis.core import *
from qgis.gui import *
from PyQt4 import QtCore, QtGui
from geogig.gui.dialogs.commitdialog import CommitDialog
from geogig import config
from geogig.gui.pyqtconnectordecorator import createRepository
import logging
from geogigpy import geogig
from layertracking import getTrackingInfo, isTracked
import traceback
from geogig.gui.dialogs.userconfigdialog import UserConfigDialog
from geogigpy.geogigexception import UnconfiguredUserException, GeoGigException
from geogig.tools.exporter import exportVectorLayer
from geogig.tools.layertracking import setInSync
from geogig.tools.layers import getDatabaseCredentials
from geogigpy.py4jconnector import Py4JConnectionException
from geogig.gui.dialogs.gatewaynotavailabledialog import GatewayNotAvailableWhileEditingDialog

_logger = logging.getLogger("geogigpy")

class LayerTracker(object):

    def __init__(self, layer):
        self.layer = layer
        self.featuresToUpdate = set()
        self.featuresToRemove = []
        self.canUseSmartUpdate = True
        self.hasChanges = False

    def featureChanged(self, fid):
        if isTracked(self.layer):
            self.hasChanges = True
            self.featuresToUpdate.add(fid)
            
    def featureTypeChanged(self):
        if isTracked(self.layer):            
            self.hasChanges = True
            self.canUseSmartUpdate = False
            
    def editingStarted(self):
        self.featuresToUpdate = set()
        self.featuresToRemove = []
        self.canUseSmartUpdate = True
        self.hasChanges = False
        provider = self.layer.dataProvider()                    
        idx = provider.fieldNameIndex("geogigid")
        self.layer.setFieldEditable(idx, False)
        if provider.name() != "postgres":   
            self.layer.setEditType(idx, QgsVectorLayer.UuidGenerator)

    def featuresAdded(self, features):
        if not isTracked(self.layer):
            return
        for feature in features:
            self.hasChanges = True
            self.featuresToUpdate.add(feature.id())

    def featureDeleted(self, fid):
        if not isTracked(self.layer):
            return
        if not self.canUseSmartUpdate:
            return
        if fid >= 0:
            self.hasChanges = True
            fIterator = self.layer.dataProvider().getFeatures(QgsFeatureRequest(fid));
            try:
                geogigfid = self._getFid(fIterator.next())
                self.featuresToRemove.append(geogigfid)
            except Exception, e:
                _logger.error(str(e))
                _logger.debug("No geogigid field found in feature in layer %s. Disabling smart update" %( self.layer.source()))
                self.canUseSmartUpdate = False
                return

            
    def editingStopped(self):
        if not isTracked(self.layer):
            return
        if not self.hasChanges:
            return
        self.hasChanges = False
        url, dest, inSync = getTrackingInfo(self.layer)
        try:
            repo = createRepository(url, False)
        except Py4JConnectionException:
            QtGui.QApplication.restoreOverrideCursor()
            dlg = GatewayNotAvailableWhileEditingDialog(config.iface.mainWindow())
            dlg.exec_()
            return
        QtGui.QApplication.restoreOverrideCursor()
        autoUpdate = config.getConfigValue(config.GENERAL, config.AUTO_UPDATE)

        if not autoUpdate:
            ret = QtGui.QMessageBox.information(config.iface.mainWindow(), "Ujo",
                                "You have modified a layer that was imported into the"
                                +"following Ujo repository:\n%s\n" % url
                                + "Do you want to update the repository with these changes?",
                                QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                QtGui.QMessageBox.Yes)
            if ret == QtGui.QMessageBox.No:
                setInSync(self.layer, False)  
                _logger.debug("Update canceled, setting layer as not synchronized")              
                return
        smartUpdate = config.getConfigValue(config.GENERAL, config.ENABLE_SMART_UPDATE)
        if inSync and smartUpdate and self.canUseSmartUpdate:
            try:
                _logger.debug("Trying smart update on layer %s and repo %s" %(self.layer.source(), url))
                self.doSmartUpdate(dest, repo)
            except Exception, e:
                _logger.error(traceback.format_exc())
                _logger.debug("Smart update failed. Using import update instead")                
                self.doUpdateLayer(dest, repo)
        else:
            self.doUpdateLayer(dest, repo)
        unstaged = repo.difftreestats(geogig.HEAD, geogig.WORK_HEAD)
        total = 0
        for counts in unstaged.values():
            total += sum(counts)
        if total == 0:
            return
            #TODO: maybe show message dialog?
        dlg = CommitDialog(repo, config.iface.mainWindow(), False, False)
        dlg.exec_()
        explorer = config.explorer
        repo.add(dlg.getPaths())
        try:
            repo.commit(dlg.getMessage())
        except UnconfiguredUserException, e:
            configdlg = UserConfigDialog(config.iface.mainWindow())
            configdlg.exec_()
            if configdlg.user is not None:
                repo.config(geogig.USER_NAME, configdlg.user)
                repo.config(geogig.USER_EMAIL, configdlg.email)
                repo.commit(dlg.getMessage())
            else:
                return
        if (explorer is not None and explorer.currentRepo is not None
                and explorer.currentRepo.url == url):
            explorer.updateRepoStatusLabelAndToolbar()
            explorer.updateCommitsList()
        config.iface.messageBar().pushMessage("Repository correctly updated",
                                                  level=QgsMessageBar.INFO, duration = 4)

        

    def _getFid(self, feature):
        try:
            return  feature['geogigid']
        except:
            raise Exception("No ID field found in layer")


    def doSmartUpdate(self, dest, repo):
        features = {}
        geomType = None
        geomField = "geom"
        #we try to have the same geom type as the default featuretype of the destination tree
        try:
            ftype = repo.featuretype(geogig.HEAD, dest)
            for fieldName, fieldType in ftype.iteritems():
                if fieldType in geogig.GEOMTYPES:
                    geomType = fieldType
                    geomField = fieldName
                    break
        except GeoGigException, e:
            pass
        for fid in self.featuresToUpdate:
            fIterator = self.layer.getFeatures(QgsFeatureRequest(fid));
            try:
                feature = fIterator.next()
            except StopIteration, e: # might happen if a newly added feature is then edited
                continue #we just ignore the feature, since it will be added anyway
            geom = feature.geometry()
            wkt = geom.exportToWkt()
            #===================================================================
            # shapelyGeom = loads(wkt)
            # if isinstance(shapelyGeom, Polygon) and geomType == geogig.TYPE_MULTIPOLYGON:
            #     shapelyGeom = MultiPolygon([shapelyGeom])
            # elif isinstance(shapelyGeom, LineString) and geomType == geogig.TYPE_MULTILINESTRING:
            #     shapelyGeom = MultiLineString([shapelyGeom])
            # elif isinstance(shapelyGeom, Polygon) and geomType == geogig.TYPE_MULTIPOINT:
            #     shapelyGeom = MultiPoint([shapelyGeom])
            #===================================================================
            geogigfid = unicode(self._getFid(feature))
            geogigfid = dest + "/" + geogigfid
            attrValues = [f if not isinstance(f, QtCore.QPyNullVariant) else None for f in feature.attributes() ]
            attributes = dict(zip([f.name() for f in feature.fields()], attrValues))
            attributes[geomField] = str(wkt)
            features[geogigfid] = attributes
        if features:
            repo.insertfeatures(features)

        toRemove = [dest + "/" + unicode(fid) for fid in self.featuresToRemove]
        if toRemove:
            repo.removefeatures(toRemove)


    def doUpdateLayer(self, dest, repo):
        url, dest, inSync = getTrackingInfo(self.layer)
        repo = createRepository(url, False)
        if self.layer.dataProvider().fieldNameIndex("geogigid") == -1:
            config.iface.messageBar().pushMessage("Cannot update Ujo repository. Layer has no 'geogigid' field",
                                                      level=QgsMessageBar.WARNING, duration = 4)

        else:
            if self.layer.dataProvider().name() == "postgres":
                provider = self.layer.dataProvider()
                uri = QgsDataSourceURI(provider.dataSourceUri())
                username,password = getDatabaseCredentials(uri)            
                if password is None and username is None:                
                    setInSync(self.layer, False)   
                    _logger.debug("Update canceled, setting layer as not synchronized")                     
                    return            
                repo.importpg(uri.database(), username, password, uri.table(),
                              uri.schema(), uri.host(), uri.port(), False, dest, True)
                setInSync(self.layer, True)
            else:
                exported = exportVectorLayer(self.layer)
                repo.importshp(exported, False, dest, "geogigid", True)
                setInSync(self.layer, True)


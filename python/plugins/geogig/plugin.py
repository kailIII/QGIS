import os
import sys
import inspect
from geogig import config
import traceback
import shutil
import logging
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from geogig.tools.utils import userFolder
from gui.dialogs.configdialog import ConfigDialog
from geogig.gui.dialogs.geogigerrordialog import GeoGigErrorDialog
from geogigpy.py4jconnector import Py4JConnectionException
from geogig.gui.viewer import GeoGigViewer
from geogigpy.geogigexception import GeoGigException
from geogig.tools.infotool import MapToolGeoGigInfo
from geogig.tools.layertracking import readTrackedLayers, cleanTemporaryLayers
from geogig.tools.layertracker import LayerTracker
from geogig.gui.dialogs import reposelector
from py4j.protocol import Py4JNetworkError
from geogig.gui.dialogs.addlayerdialog import AddGeoGigLayerDialog
from geogig.gui.dialogs.gatewaynotavailabledialog import GatewayNotAvailableDialog
from geogig.gui.pyqtconnectordecorator import killGateway
from geogig.tools.layers import getVectorLayers, setIdEditWidget
from geogig.tools.utils import tempFolder

cmd_folder = os.path.split(inspect.getfile( inspect.currentframe()))[0]
if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)

logger = logging.getLogger("geogigpy")

trackers = []

def trackLayer(layer): 
    global trackers       
    if layer.type() == layer.VectorLayer:                                    
        tracker = LayerTracker(layer)
        trackers.append(tracker)
        def featuresAdded(layername, features):                
            tracker.featuresAdded(features)  
        def geomChanged(fid, geom):                
            tracker.featureChanged(fid)            
        def attributeValueChanged(fid, idx, value):                
            tracker.featureChanged(fid)
        layer.featureDeleted.connect(tracker.featureDeleted)
        layer.committedFeaturesAdded.connect(featuresAdded)                
        QObject.connect(layer, SIGNAL("geometryChanged(QgsFeatureId, QgsGeometry&)"), geomChanged)
        layer.attributeValueChanged.connect(attributeValueChanged)                            
        layer.attributeAdded.connect(tracker.featureTypeChanged)
        layer.attributeDeleted.connect(tracker.featureTypeChanged)            
        layer.editingStopped.connect(tracker.editingStopped)           
        layer.editingStarted.connect(tracker.editingStarted)
        
        setIdEditWidget(layer)
                

class GeoGigPlugin:

    geogigPath = os.path.join(os.path.dirname(QgsApplication.qgisUserDbFilePath()),
                                "python", "plugins", "geogig", "apps" ,"geogig", "bin")

    def __init__(self, iface):
        self.iface = iface
        config.iface = iface

        self.explorer = None

        logFile = os.path.join(userFolder(), "geogigpy.log")
        handler = logging.FileHandler(logFile)
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)

        readTrackedLayers()
        
        QgsMapLayerRegistry.instance().layerWasAdded.connect(trackLayer)
        iface.actionSaveProject().triggered.connect(self.savingProject)
        iface.actionSaveProjectAs().triggered.connect(self.savingProject)
        
        
    def savingProject(self):
        layers = getVectorLayers()
        tempLayers = [lay.name() for lay in layers if lay.source().startswith(tempFolder())]
        if tempLayers:
            QMessageBox.warning(self.iface.mainWindow(), 'Ujo',
                    "The folowing layers are temporary Ujo layers that will be removed when you close QGIS:\n\n  - "
                    + "\n  - ".join(tempLayers)
                    + "\n\nSave them to a different location and then save the project again, to avoid issues\n" 
                    + "when reopening it.",
                    QMessageBox.Ok)
        
    def unload(self):
        self.menu.deleteLater()
        sys.excepthook = self.qgisHook

        killGateway()

        #delete temporary output files
        folder = tempFolder()
        if QDir(folder).exists():
            shutil.rmtree(folder, True)

        cleanTemporaryLayers()

    def initGui(self):

        icon = QIcon(os.path.dirname(__file__) + "/ui/resources/geogig.png")
        self.addLayerAction = QAction(icon, "Add Ujo layer...", self.iface.mainWindow())
        self.addLayerAction.triggered.connect(self.addLayer)
        menu = self.iface.layerMenu()
        actions = menu.actions()
        menu.insertAction(actions[6], self.addLayerAction)
        for subaction in actions:
            if subaction.isSeparator():
                menu.insertAction(subaction, self.addLayerAction)
                break

        self.menu = QMenu(self.iface.mainWindow())
        self.menu.setTitle("Ujo")
        icon = QIcon(os.path.dirname(__file__) + "/ui/resources/geogig.png")
        self.explorerAction = QAction(icon, "Ujo client", self.iface.mainWindow())
        self.explorerAction.triggered.connect(self.openExplorer)
        self.menu.addAction(self.explorerAction)
        icon = QIcon(os.path.dirname(__file__) + "/ui/resources/config.png")
        self.configAction = QAction(icon, "Ujo client settings", self.iface.mainWindow())
        self.configAction.triggered.connect(self.openSettings)
        self.menu.addAction(self.configAction)
        icon = QIcon(os.path.dirname(__file__) + "/ui/resources/identify.png")
        self.toolAction = QAction(icon, "Ujo feature info tool", self.iface.mainWindow())
        self.toolAction.setCheckable(True)
        self.toolAction.triggered.connect(self.setTool)
        self.menu.addAction(self.toolAction)

        menuBar = self.iface.mainWindow().menuBar()
        menuBar.insertMenu(self.iface.firstRightStandardMenu().menuAction(), self.menu)

        self.qgisHook = sys.excepthook;

        def pluginHook(t, value, tb):
            if isinstance(value, GeoGigException):
                logger.error(unicode(tb))
                self.setWarning(unicode(value))
            elif isinstance(value, (Py4JConnectionException, Py4JNetworkError)):
                dlg = GatewayNotAvailableDialog(self.iface.mainWindow())
                dlg.exec_()
            else:
                trace = "".join(traceback.format_exception(t, value, tb))
                if "geogig" in trace.lower():
                    dlg = GeoGigErrorDialog(trace, self.iface.mainWindow())
                    dlg.exec_()
                else:
                    self.qgisHook(t, value, tb)
        sys.excepthook = pluginHook

        self.mapTool = MapToolGeoGigInfo(self.iface.mapCanvas())
        #This crashes QGIS, so we comment it out until finding a solution
        #self.mapTool.setAction(self.toolAction)



    def setWarning(self, msg):
        QMessageBox.warning(None, 'Could not complete Ujo command',
                            msg,
                            QMessageBox.Ok)


    def setTool(self):
        self.toolAction.setChecked(True)
        self.iface.mapCanvas().setMapTool(self.mapTool)

    def addLayer(self):
        dlg = AddGeoGigLayerDialog(self.iface.mainWindow())
        dlg.exec_()

    def openExplorer(self):
        config.iface = self.iface
        repo = reposelector.getRepo()
        if repo is not None:
            repo.repo.connector.checkIsAlive()
            if self.explorer is None:
                self.explorer = GeoGigViewer(repo)
                config.explorer = self.explorer
                self.iface.addDockWidget(Qt.RightDockWidgetArea, self.explorer)
                self.explorer.show()
            else:
                self.explorer.setRepo(repo)
                self.explorer.show()

            
    def openSettings(self):
        dlg = ConfigDialog()
        dlg.exec_()


            
            
            
        



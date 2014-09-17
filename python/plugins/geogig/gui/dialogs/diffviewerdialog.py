import os
import logging
from PyQt4 import QtGui, QtCore
from qgis.core import *
from qgis.gui import *
from geogig.ui.diffviewerdialog import Ui_DiffViewerDialog
from geogig.gui.dialogs.geogigref import RefPanel
from geogigpy.diff import *
from geogigpy import geogig
from geogigpy.geogigexception import GeoGigException
from geogigpy.commit import Commit
from geogigpy.geometry import Geometry
from geogig import config

_logger = logging.getLogger("geogigpy")

resourcesPath = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, "resources")
ptStyleAfter = os.path.join(resourcesPath, "pt_after.qml")
lineStyleAfter = os.path.join(resourcesPath, "line_after.qml")
polygonStyleAfter = os.path.join(resourcesPath, "polygon_after.qml")
ptStyleBefore = os.path.join(resourcesPath, "pt_before.qml")
lineStyleBefore = os.path.join(resourcesPath, "line_before.qml")
polygonStyleBefore = os.path.join(resourcesPath, "polygon_before.qml")

class DiffViewerDialog(QtGui.QDialog):

    CHANGES_THRESHOLD = 300

    def __init__(self, repo, refa, refb):
        QtGui.QDialog.__init__(self, config.iface.mainWindow(),
                               QtCore.Qt.WindowSystemMenuHint | QtCore.Qt.WindowTitleHint)
        self.repo = repo
        self.oldLayerId = None
        self.newLayerId = None
        self._baseLayer = None
        self.currentPath = None

        if (isinstance(refa, Commit) and isinstance(refb, Commit)
                and refa.committerdate > refb.committerdate):
            refa, refb = refb, refa

        self.ui = Ui_DiffViewerDialog()
        self.ui.setupUi(self)

        self.setWindowFlags(self.windowFlags() |
                              QtCore.Qt.WindowSystemMenuHint |
                              QtCore.Qt.WindowMinMaxButtonsHint)

        self.commit1 = refa
        self.commit1Panel = RefPanel(self.repo, refa, onlyCommits = False)
        layout = QtGui.QHBoxLayout()
        layout.setSpacing(0)
        layout.setMargin(0)
        layout.addWidget(self.commit1Panel)
        self.ui.commit1Widget.setLayout(layout)
        self.commit2 = refb
        self.commit2Panel = RefPanel(self.repo, refb, onlyCommits = False)
        layout = QtGui.QHBoxLayout()
        layout.setSpacing(0)
        layout.setMargin(0)
        layout.addWidget(self.commit2Panel)
        self.ui.commit2Widget.setLayout(layout)
        self.commit1Panel.refChanged.connect(self.refsHaveChanged)
        self.commit2Panel.refChanged.connect(self.refsHaveChanged)

        horizontalLayout = QtGui.QHBoxLayout()
        horizontalLayout.setSpacing(0)
        horizontalLayout.setMargin(0)
        self.mapCanvas = QgsMapCanvas()
        self.mapCanvas.setCanvasColor(QtCore.Qt.white)
        settings = QtCore.QSettings()
        self.mapCanvas.enableAntiAliasing(settings.value( "/qgis/enable_anti_aliasing", False, type=bool))
        self.mapCanvas.useImageToRender(settings.value( "/qgis/use_qimage_to_render", False, type=bool))
        self.mapCanvas.mapRenderer().setProjectionsEnabled(True)
        action = settings.value("/qgis/wheel_action", 0, type=float)
        zoomFactor = settings.value("/qgis/zoom_factor", 2, type=float)
        self.mapCanvas.setWheelAction(QgsMapCanvas.WheelAction(action), zoomFactor)
        horizontalLayout.addWidget(self.mapCanvas)
        self.ui.mapContainer.setLayout(horizontalLayout)

        self.panAndSelectTool = MapToolPanAndSelect(self.mapCanvas, self)
        self.mapCanvas.setMapTool(self.panAndSelectTool)
        
        self.ui.attributesTable.itemSelectionChanged.connect(self.selectionChanged)

        def _setExtentToLayer(canvas):
            self.mapCanvas.setExtent(self.mapCanvas.layer(0).extent())
            self.mapCanvas.refresh()
        self.ui.zoomToExtentButton.clicked.connect(_setExtentToLayer)
    
        self.computeDiffs()
            
        self.showMaximized()


    def refsHaveChanged(self):
        self.computeDiffs()

    def getBaseLayer(self):
        if self._baseLayer is None:
            baseLayerFile = os.path.join(os.path.dirname(__file__),
                                         os.pardir, os.pardir, "resources", "osm.xml")
            baseLayer = QgsRasterLayer(baseLayerFile, "base", "gdal")
            if baseLayer.isValid():
                self._baseLayer = baseLayer
                QgsMapLayerRegistry.instance().addMapLayer(self._baseLayer, False)
        else:
            _logger.debug("Could not load base OSM layer")
        return self._baseLayer

    def getFullExtent(self, layers):
        extent = layers[0].extent()
        for layer in layers[1:]:
            extent.combineExtentWith(layer.extent())
        return extent

    def selectionChanged(self):
        row = self.ui.attributesTable.currentRow()  
        def _filter(feature):
            print feature["row"]
            print row
            return feature["row"] == row       
        if self.oldLayer is not None:            
            features = filter(_filter, self.oldLayer.getFeatures())  
            print features        
            self.oldLayer.setSelectedFeatures([feature.id() for feature in features])        
        if self.newLayer is not None:            
            features = filter(_filter, self.newLayer.getFeatures())
            print features                  
            self.newLayer.setSelectedFeatures([feature.id() for feature in features])  
        self.mapCanvas.refresh()           

    def computeDiffs(self):
        self.commit1 = self.commit1Panel.getRef()
        self.commit2 = self.commit2Panel.getRef()
        commit1 = self.commit1.ref
        commit2 = self.commit2.ref
        
        self.newLayer = None
        self.oldLayer = None

        treediffs = self.repo.difftreestats(commit1, commit2)
        path = treediffs.keys()[0] #TODO: handle changes in multiple layers
        attribs, features = self.repo.treediff(path, commit1, commit2)
        geogigidIdx = None
        if "geogigid" in attribs:
            geogigidIdx = attribs.keys().index("geogigid")
            del attribs["geogigid"]
        attribs = attribs.keys()
        self.ui.attributesTable.setColumnCount(len(attribs))        
        for i, attrib in enumerate(attribs):
            self.ui.attributesTable.setHorizontalHeaderItem(
                                            i,QtGui.QTableWidgetItem(attrib))
        self.ui.attributesTable.setRowCount(len(features))
        for row, feature in enumerate(features):
            if geogigidIdx is not None:
                del feature[geogigidIdx]
            changeTypes = set()
            for col, attrib in enumerate(feature):
                if isinstance(attrib[1], Geometry):                    
                    qgsgeom = QgsGeometry.fromWkt(attrib[1].geom)
                    crsTransform = QgsCoordinateTransform(QgsCoordinateReferenceSystem(attrib[1].crs), self.EPSG4326)
                    qgsgeom .transform(crsTransform)
                    geom = [attrib[0], qgsgeom]
                    if len(attrib) > 2:
                        qgsgeom2 = QgsGeometry.fromWkt(attrib[2].geom)
                        crsTransform = QgsCoordinateTransform(QgsCoordinateReferenceSystem(attrib[2].crs), self.EPSG4326)
                        qgsgeom2 .transform(crsTransform)
                        geom.append(qgsgeom2)                    
                    attrib = geom
                changeTypes.add(attrib[0])
                widget = TableWidget(attrib, self.mapCanvas)
                self.ui.attributesTable.setCellWidget(row, col, widget)            
            geom[0] = ATTRIBUTE_DIFF_MODIFIED if len(changeTypes) > 1 else changeTypes.pop() 
            self.addDiffGeomToLayer(geom, row)
        
        self.ui.attributesTable.horizontalHeader().setResizeMode(QtGui.QHeaderView.Interactive)
        self.ui.attributesTable.horizontalHeader().setDefaultSectionSize(200)
        self.ui.attributesTable.horizontalHeader().setMinimumSectionSize(150)        
        self.ui.attributesTable.horizontalHeader().setStretchLastSection(True)        
        for i in xrange(len(features)):
            self.ui.attributesTable.setVerticalHeaderItem(
                                            i,QtGui.QTableWidgetItem(str(i+1)))
        self.ui.attributesTable.setVisible(False)
        vporig = self.ui.attributesTable.viewport().geometry()
        vpnew = vporig;
        vpnew.setWidth(10000);
        self.ui.attributesTable.viewport().setGeometry(vpnew);        
        self.ui.attributesTable.resizeRowsToContents()
        self.ui.attributesTable.viewport().setGeometry(vporig);
        self.ui.attributesTable.setVisible(True)
        self.showLayers()
        
    def showLayers(self):
        settings = QtCore.QSettings()
        prjSetting = settings.value('/Projections/defaultBehaviour')
        settings.setValue('/Projections/defaultBehaviour', '')
        styles = [(ptStyleBefore, ptStyleAfter), (lineStyleBefore, lineStyleAfter),
                  (polygonStyleBefore, polygonStyleAfter)]
        
        if self.oldLayer is not None:
            vectortype = self.oldLayer.geometryType()
        else:
            vectortype = self.newLayer.geometryType()            
        styleBefore, styleAfter = styles[vectortype]
            
        layers = []
        if self.oldLayer is not None:
            self.oldLayer.updateExtents()
            #this is to correct a problem with memory layers in qgis 2.2
            self.oldLayer.selectAll()
            self.oldLayer.setExtent(self.oldLayer.boundingBoxOfSelected())
            self.oldLayer.invertSelection()
            self.oldLayer.loadNamedStyle(styleBefore)
            layers.append(self.oldLayer)
        if self.newLayer is not None:
            self.newLayer.updateExtents()
            self.newLayer.selectAll()
            self.newLayer.setExtent(self.newLayer.boundingBoxOfSelected())
            self.newLayer.invertSelection()
            self.newLayer.loadNamedStyle(styleAfter)
            layers.append(self.newLayer)
        extent = self.getFullExtent(layers)
        layers.append(self.getBaseLayer())
        self.mapCanvas.setRenderFlag(False)
        mapLayers = [QgsMapCanvasLayer(lay) for lay in layers]
        self.mapCanvas.setLayerSet(mapLayers)
        for layer in layers:
            QgsMapLayerRegistry.instance().addMapLayer(layer, False)        
        
        self.mapCanvas.setExtent(extent)
        self.mapCanvas.refresh()
        self.mapCanvas.setRenderFlag(True)
                
        settings.setValue('/Projections/defaultBehaviour', prjSetting)
   
    EPSG4326 = QgsCoordinateReferenceSystem("EPSG:4326")
    
    def addDiffGeomToLayer(self, geom, row):
        if geom[0] == ATTRIBUTE_DIFF_REMOVED:
            self._addGeomToOldLayer(geom[1], [geom[0], row])
        elif geom[0] == ATTRIBUTE_DIFF_ADDED:
            self._addGeomToNewLayer(geom[1], [geom[0], row])
        else:
            if len(geom) > 2:
                self._addGeomToOldLayer(geom[1], [geom[0], row])
                self._addGeomToNewLayer(geom[2], [geom[0], row])
            else:
                self._addGeomToOldLayer(geom[1], [geom[0], row])
                self._addGeomToNewLayer(geom[1], [geom[0], row])
                
    def _addGeomToOldLayer(self, qgsgeom, attribs):
        if self.oldLayer is None:
            geomtype = ["Point", "LineString", "Polygon"][qgsgeom.type()]
            self.oldLayer = QgsVectorLayer(geomtype +"?crs=EPSG:4326&field=changetype:string(1)&field=row:integer", "Old", "memory")                                
        pr = self.oldLayer.dataProvider()
        feat = QgsFeature()
        feat.setGeometry(qgsgeom)
        feat.setAttributes(attribs)
        pr.addFeatures([feat])
    
    def _addGeomToNewLayer(self, qgsgeom, attribs):
        if self.newLayer is None:
            geomtype = ["Point", "LineString", "Polygon"][qgsgeom.type()]
            self.newLayer = QgsVectorLayer(geomtype +"?crs=EPSG:4326&field=changetype:string(1)&field=row:integer", "New", "memory")                        
        pr = self.newLayer.dataProvider()
        feat = QgsFeature()
        feat.setGeometry(qgsgeom)
        feat.setAttributes(attribs)
        pr.addFeatures([feat])
        
    def reject(self):
        QtGui.QDialog.reject(self)
        if self.oldLayer:
            QgsMapLayerRegistry.instance().removeMapLayer(self.oldLayer.id())
        if self.newLayer:
            QgsMapLayerRegistry.instance().removeMapLayer(self.newLayer.id())
        if self.getBaseLayer():
            QgsMapLayerRegistry.instance().removeMapLayer(self.getBaseLayer().id())

class TableWidget(QtGui.QLabel):
    
    def __init__(self, attrDiff, canvas):
        QtGui.QLabel.__init__(self)
        self.setTextFormat(QtCore.Qt.RichText);
        self.setWordWrap(True)
        self.canvas = canvas
        self.extent = {}
        if attrDiff[0] == ATTRIBUTE_DIFF_REMOVED:                        
            self.setStyleSheet('color: rgb(170,0,0); padding-left: 3')            
        elif attrDiff[0] == ATTRIBUTE_DIFF_ADDED:
            self.setStyleSheet('color: rgb(0,200,0); padding-left: 3')
        elif attrDiff[0] == ATTRIBUTE_DIFF_MODIFIED:
            self.setStyleSheet('color: rgb(255, 170, 0); padding-left: 3')            
        else:
            self.setStyleSheet('padding-left: 3')            

        if isinstance(attrDiff[1], QgsGeometry):
            if attrDiff[0] == ATTRIBUTE_DIFF_MODIFIED:                 
                self.setText('<html><s>%s</s> <a href = "False"> [Zoom to]</a><br>%s<a href = "True"> [Zoom to]</a></html>'                              
                             % (self.asText(attrDiff[1]), self.asText(attrDiff[2], True)))
            elif attrDiff[0] == ATTRIBUTE_DIFF_REMOVED:                        
                self.setText('<html><s>%s</s><a href = "False"> [Zoom to]</a></html>' 
                             % self.asText(attrDiff[1]))
            else:                        
                self.setText('<html>%s<a href = "False"> [Zoom to]</a></html>' 
                             % self.asText(attrDiff[1]))
        else:
            if attrDiff[0] == ATTRIBUTE_DIFF_MODIFIED:
                self.setText('<html><s>%s</s><br>%s</html>' 
                             % (unicode(attrDiff[1]), unicode(attrDiff[2])))
            elif attrDiff[0] == ATTRIBUTE_DIFF_REMOVED:                        
                self.setText('<html><s>%s</s></html>' % unicode(attrDiff[1]))
            else:
                self.setText(self.asText(attrDiff[1]))
            
        self.connect(self, QtCore.SIGNAL("linkActivated(QString)"), self.zoomTo)
        
    def zoomTo(self, url):
        after = url == str(True)
        self.canvas.setExtent(self.extent[after])
        self.canvas.refresh()            

    def asText(self, value, after = False):
        if isinstance(value, QgsGeometry):
            self.extent[after] = value.boundingBox() 
            return value.exportToWkt().split("(")[0]        
        else:
            return unicode(value)
        

class MapToolPanAndSelect(QgsMapTool):

    def __init__(self, canvas, viewer):
        self.canvas = canvas
        self.viewer = viewer
        self.featureSelected = False
        self.dragging = False
        QgsMapTool.__init__(self, self.canvas)
        self.setCursor(QtCore.Qt.CrossCursor)

    def canvasReleaseEvent(self, e):
        if e.button() == QtCore.Qt.LeftButton:
            if (self.dragging ):
                self.canvas.panActionEnd(e.pos())
                self.dragging = False
        
    def canvasMoveEvent(self, e):
        if e.buttons() & QtCore.Qt.LeftButton:
            self.dragging = True
            self.canvas.panAction(e)
            
    def canvasPressEvent(self, e):
        layers = [lay for lay in self.canvas.layers() 
                           if lay.type() == lay.VectorLayer]
        if len(layers) == 0:
            return
        
        layers = layers[::-1]

        point = self.toMapCoordinates(e.pos())
        searchRadius = self.canvas.extent().width() * .01;
        r = QgsRectangle()
        r.setXMinimum(point.x() - searchRadius);
        r.setXMaximum(point.x() + searchRadius);
        r.setYMinimum(point.y() - searchRadius);
        r.setYMaximum(point.y() + searchRadius);

        self.viewer.ui.attributesTable.selectionModel().clear()         
        for layer in layers:
            layer.setSelectedFeatures([])
        for layer in layers:
            r = self.toLayerCoordinates(layer, r);
            features = layer.getFeatures(QgsFeatureRequest().setFilterRect(r).setFlags(QgsFeatureRequest.ExactIntersect));
            try:
                feature = features.next()
                self.viewer.ui.attributesTable.selectRow(int(feature["row"]))                                   
                #layer.setSelectedFeatures([feature.id()])                
                #self.canvas.refresh()                                        
                return
            except StopIteration, e:
                pass



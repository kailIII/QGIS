from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *
from geogig.ui.updatelayersdialog import Ui_UpdateLayersDialog
from geogig import config
from geogig.gui.pyqtconnectordecorator import createRepository
from geogigpy import geogig


class UpdateLayersDialog(QDialog, Ui_UpdateLayersDialog):

    def __init__(self, layers):
        QDialog.__init__(self)
        self.setupUi(self)

        self.layers = layers

        # Additional buttons
        self.btnSelectAll = QPushButton(self.tr('Select all'))
        self.buttonBox.addButton(self.btnSelectAll,
                                 QDialogButtonBox.ActionRole)
        self.btnClearSelection = QPushButton(self.tr('Clear selection'))
        self.buttonBox.addButton(self.btnClearSelection,
                                 QDialogButtonBox.ActionRole)
        self.btnToggleSelection = QPushButton(self.tr('Toggle selection'))
        self.buttonBox.addButton(self.btnToggleSelection,
                                 QDialogButtonBox.ActionRole)

        self.btnSelectAll.clicked.connect(lambda: self.selectAll(True))
        self.btnClearSelection.clicked.connect(lambda: self.selectAll(False))
        self.btnToggleSelection.clicked.connect(self.toggleSelection)

        self.populateList()

    def populateList(self):
        model = QStandardItemModel()
        for layer in self.layers:
            item = QStandardItem(layer[0].name())
            item.setCheckState(Qt.Unchecked)
            item.setCheckable(True)
            model.appendRow(item)

        self.lstLayers.setModel(model)

    def updateLayer(self, layer, trackInfo):        
        try:
            repo = createRepository(trackInfo.url, False)
            repo.connector.setShowProgress(False)        
            if layer.dataProvider().name() == "postgres":
                uri = QgsDataSourceURI(layer.dataProvider().dataSourceUri())
                repo.exportpg(geogig.HEAD, trackInfo.dest, uri.table(), uri.database(), 
                              uri.username(), uri.password(), uri.schema(), uri.host(), uri.port(), True)
            else:
                repo.exportshp(geogig.HEAD, trackInfo.dest, layer.source())                
            layer.reload() 
            config.iface.mapCanvas().refresh()       
        finally:
            repo.connector.setShowProgress(True)
        
    def accept(self):  
        self.updated = []       
        self.progressBar.setMaximum(0)       
        model = self.lstLayers.model()
        for i in xrange(model.rowCount()):
            item = model.item(i)
            if item.checkState() == Qt.Checked:
                self.updateLayer(*self.layers[i])
                self.updated.append(self.layers[i][0])
                item.setBackground(Qt.green)
            else:
                item.setBackground(Qt.yellow)
        config.iface.messageBar().pushMessage("Layers correctly updated",
                                              level=QgsMessageBar.INFO, duration = 4)
        QDialog.accept(self)

    def reject(self):
        self.updated = []
        QDialog.reject(self)

    def selectAll(self, value):
        model = self.lstLayers.model()
        for i in xrange(model.rowCount()):
            item = model.item(i)
            item.setCheckState(Qt.Checked if value else Qt.Unchecked)

    def toggleSelection(self):
        model = self.lstLayers.model()
        for i in xrange(model.rowCount()):
            item = model.item(i)
            checked = item.checkState() == Qt.Checked
            item.setCheckState(Qt.Unchecked if checked else Qt.Checked)

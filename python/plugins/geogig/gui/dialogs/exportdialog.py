import os
from PyQt4 import QtGui, QtCore
from qgis.core import *
from geogigpy import geogig
from geogigpy.commit import Commit
from geogigpy.tree import Tree
from geogigpy import geogig
from geogig import config
from geogig.gui.dialogs.geogigref import RefPanel
from geogigpy.geogigexception import GeoGigException, UnconfiguredUserException
from geogig.ui.exportdialog import Ui_ExportDialog
from geogig.tools.layertracking import addTrackedLayer
from geogig.tools import layers

class ExportDialog(QtGui.QDialog):

    FILE = 0
    SPATIALITE = 1
    POSTGIS = 2

    def __init__(self, parent, repo, ref = None):
        QtGui.QDialog.__init__(self, parent, QtCore.Qt.WindowSystemMenuHint | QtCore.Qt.WindowTitleHint)
        self.ui = Ui_ExportDialog()
        self.ui.setupUi(self)
        self.repo = repo
        exportButton = QtGui.QPushButton("Export")
        exportButton.clicked.connect(self.exportClicked)
        self.ui.exportButtonBox.addButton(exportButton, QtGui.QDialogButtonBox.ApplyRole)
        self.ui.exportButtonBox.rejected.connect(self.reject)

        verticalLayout = QtGui.QVBoxLayout()
        verticalLayout.setSpacing(0)
        verticalLayout.setMargin(0)        
        self.refPanel = RefPanel(self.repo, onlyCommits = False)
        verticalLayout.addWidget(self.refPanel)
        self.ui.exportSnapshotWidget.setLayout(verticalLayout)
        self.ui.selectExportFileButton.clicked.connect(self.selectExportFile)

        #hide bars until progress indication is fixed
        self.ui.progressBarExport.setVisible(False)


        self.refPanel.refChanged.connect(self.snapshotHasChanged)

        ref = repo.head if ref is None else ref
        self.refPanel.setRef(ref)

    def snapshotHasChanged(self):
        self.ui.layersList.clear()
        tree = Tree(self.repo, self.refPanel.getRef().ref)
        for subtree in tree.trees:
            item = TreeListItem(subtree.path)
            self.ui.layersList.addItem(item)


    def selectExportFile(self):
        settings = QtCore.QSettings()
        path = settings.value("/GeoGig/LastExportFilePath", "")
        filename = QtGui.QFileDialog.getSaveFileName(self, "Select shp file", path, "Shapefile files (*.shp)")
        if filename != "":
            self.ui.exportFileBox.setText(filename)
            settings.setValue("/GeoGig/LastExportFilePath", os.path.dirname(filename))


    def exportClicked(self):
        destinationType = self.ui.exportTypeWidget.currentIndex()
        selected = self.ui.layersList.selectedItems()
        if not selected:
            QtGui.QMessageBox.warning(self, 'Export',
                    "No tree has been selected for export.",
                    QtGui.QMessageBox.Ok)
            return
        path =  selected[0].path
        if destinationType == self.FILE:
            filepath = self.ui.exportFileBox.text().strip()
            self.repo.exportshp(self.refPanel.getRef().ref, path, filepath)
        elif destinationType == self.SPATIALITE:
            filepath = self.ui.spatialiteFileBox.text()
            user = self.ui.spatialiteUserBox.text()
            self.repo.exportsl(self.refPanel.getRef().ref, path, filepath, user)
        elif destinationType == self.POSTGIS:
            host = self.ui.pgExportHostBox.text().strip()
            host = "localhost" if host == "" else host
            database = self.ui.pgExportDatabaseBox.text().strip()
            database = "database" if database == "" else database
            user = self.ui.pgExportUserBox.text().strip()
            user = "postgres" if user == "" else user
            password = self.ui.pgExportPasswordBox.text().strip()
            password = "postgres" if password == "" else password
            port = self.ui.pgExportPortBox.text().strip()
            port = "5432" if port == "" else port
            schema = self.ui.pgExportSchemaBox.text().strip()
            schema = "public" if schema == "" else schema
            table = self.ui.pgExportTableBox.text().strip()
            if table == "":
                QtGui.QMessageBox.warning(self, 'Export',
                    "A destination table must be specified",
                    QtGui.QMessageBox.Ok)
                return
            try:
                self.repo.exportpg(self.refPanel.getRef().ref, path, table, database,
                                   user, password, schema, host, port)
            except GeoGigException, e:
                if "overwrite" in unicode(e):
                    ret = QtGui.QMessageBox.information(self, "Confirm overwrite",
                                                  "The selected table already exists.\n"
                                                  "Do you want to overwrite it?",
                                                  QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, 
                                                  QtGui.QMessageBox.No )
                    if ret == QtGui.QMessageBox.Yes:
                        self.repo.exportpg(self.refPanel.getRef().ref, path, table, database,
                                   user, password, schema, host, port, True)
                    else:
                        return
                else:
                    raise
            for vlayer in layers.getVectorLayers():
                if vlayer.dataProvider().name() == "postgres":
                    uri = QgsDataSourceURI(vlayer.dataProvider().dataSourceUri())
                    if uri.table() == table:
                        vlayer.reload()
        QtGui.QMessageBox.information(self, 'Export',
                    "The selected data has been correctly exported.",
                    QtGui.QMessageBox.Ok)
        if self.ui.openLayerCheckbox.isChecked():
            if destinationType == self.FILE:
                layer = QgsVectorLayer(filepath, path, "ogr")
            elif destinationType == self.SPATIALITE:
                #TODO
                pass
            elif destinationType == self.POSTGIS:
                uri = QgsDataSourceURI()
                uri.setConnection(host, port, database, user, password)
                uri.setDataSource(schema, table, "geom")
                layer = QgsVectorLayer(uri.uri(), path, "postgres")
            QgsMapLayerRegistry.instance().addMapLayers([layer])
            if layer.dataProvider().fieldNameIndex("geogigid") == -1:
                QtGui.QMessageBox.warning(None, "Warning", "The exported layer doesn't have an 'geogigid' field.\n"
                                                        "It will not be tracked and changes to the layer will\n"
                                                        "not be automatically updated in the Ujo repository.\n"
                                                        "Add a 'geogigid' field and re-import to correct this.")
            else:                
                addTrackedLayer(self.repo.url, layer, path)

        QtGui.QDialog.accept(self)
        self.close()

    def reject(self):
        QtGui.QDialog.reject(self)
        self.close()

class TreeListItem(QtGui.QListWidgetItem):

    layerIcon = QtGui.QIcon(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, "ui", "resources", "layer_group.gif"))

    def __init__(self, path):
        QtGui.QListWidgetItem.__init__(self, path)
        self.setIcon(self.layerIcon)
        self.path = path

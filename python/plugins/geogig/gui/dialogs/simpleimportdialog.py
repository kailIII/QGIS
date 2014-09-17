from qgis.core import *
from qgis.gui import *
from PyQt4 import QtGui
from geogig.tools.layers import *
import os
from geogigpy.geogigexception import GeoGigException, UnconfiguredUserException
from geogigpy import geogig
from geogig import config
from geogig.gui.dialogs.userconfigdialog import UserConfigDialog
from geogig.tools.exporter import exportVectorLayer
from geogig.tools.layertracking import addTrackedLayer
from geogig.gui.dialogs.batchimportdialog import BatchImportDialog
from geogig.tools.postgis_utils import DbError
from geogig.gui.dialogs.addgeogigiddialog import AddGeogigIdDialog
from processing.tools.dataobjects import getSupportedOutputVectorLayerExtensions

class SimpleImportDialog(QtGui.QDialog):

    def __init__(self, parent, repo):
        super(SimpleImportDialog, self).__init__(parent)
        self.repo = repo
        self.initGui()

    def initGui(self):
        self.setWindowTitle('Add/update layer in Ujo repository')
        verticalLayout = QtGui.QVBoxLayout()


        layerLabel = QtGui.QLabel('Layer')
        verticalLayout.addWidget(layerLabel)

        self.layerCombo = QtGui.QComboBox()
        self.layerCombo.setEditable(True)
        layerNames = [layer.name() for layer in getVectorLayers()]
        self.layerCombo.addItems(layerNames)
        self.selectLayerFileButton = QtGui.QToolButton()
        self.selectLayerFileButton.setText("...")
        self.selectLayerFileButton.clicked.connect(self.selectLayerFile)
        self.batchImportButton = QtGui.QToolButton()
        self.batchImportButton.setText("Batch...")
        self.batchImportButton.clicked.connect(self.batchImport)

        horizontalLayout = QtGui.QHBoxLayout()
        horizontalLayout.setSpacing(0)
        horizontalLayout.addWidget(self.layerCombo)
        horizontalLayout.addWidget(self.selectLayerFileButton)
        spacerItem = QtGui.QSpacerItem(20, 20, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        horizontalLayout.addItem(spacerItem)
        horizontalLayout.addWidget(self.batchImportButton)
        verticalLayout.addLayout(horizontalLayout)

        messageLabel = QtGui.QLabel('Message to describe this update')
        verticalLayout.addWidget(messageLabel)

        self.messageBox = QtGui.QPlainTextEdit()
        self.messageBox.textChanged.connect(self.messageHasChanged)
        verticalLayout.addWidget(self.messageBox)

        self.buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Cancel)
        self.importButton = QtGui.QPushButton("Add/update layer")
        self.importButton.clicked.connect(self.importClicked)
        self.importButton.setEnabled(False)
        self.buttonBox.addButton(self.importButton, QtGui.QDialogButtonBox.ApplyRole)
        self.buttonBox.rejected.connect(self.cancelPressed)
        verticalLayout.addWidget(self.buttonBox)

        self.setLayout(verticalLayout)

        self.resize(400,200)
        
    def batchImport(self):
        dlg = BatchImportDialog(self, self.repo)
        dlg.exec_()
        if dlg.ok:
            if config.explorer is not None and config.explorer.currentRepo is not None:
                if config.explorer.currentRepo.url == self.repo.url:
                    config.explorer.updateRepoStatusLabelAndToolbar()
                    config.explorer.updateCommitsList()
            self.close()        

    def messageHasChanged(self):
        self.importButton.setEnabled(self.messageBox.toPlainText() != "")

    def selectLayerFile(self):
        settings = QtCore.QSettings()
        path = settings.value("/GeoGig/LastImportFilePath", "")
        exts = getSupportedOutputVectorLayerExtensions()
        for i in range(len(exts)):
            exts[i] = exts[i].upper() + ' files(*.' + exts[i].lower() + ')'
        filefilter = ';;'.join(exts)
        filename = QtGui.QFileDialog.getOpenFileName(self, "Select import file", path, filefilter)
        if filename != "":
            self.layerCombo.setEditText(filename)
            settings.setValue("/GeoGig/LastImportFilePath", os.path.dirname(filename))

    def importClicked(self):
        isPostGis = False
        isSpatiaLite = False
        text = self.layerCombo.currentText()
        layer = None
        try:
            layer = resolveLayer(text)
            isPostGis = layer.dataProvider().name() == "postgres"
            isSpatiaLite = layer.dataProvider().name() == "sqlite"
            source = layer.source()
            hasIdField = layer.dataProvider().fieldNameIndex("geogigid") != -1
        except WrongLayerNameException, e:
            source = text
            name = os.path.splitext(os.path.basename(source))[0]
            layer = QgsVectorLayer(source, name, "ogr")
            if not layer.isValid() or layer.type() != QgsMapLayer.VectorLayer:
                raise GeoGigException ("Error reading file {} or it is not a valid vector layer file".format(source))
            hasIdField = layer.dataProvider().fieldNameIndex("geogigid") != -1
        if isPostGis:
            provider = layer.dataProvider()
            uri = QgsDataSourceURI(provider.dataSourceUri())
            username,password = getDatabaseCredentials(uri)            
            if password is None and username is None:
                self.close()
                return
            try:
                db =  GeoDB(uri.host(), int(uri.port()), uri.database(), username, password)
            except DbError:
                QtGui.QMessageBox.warning(self, "Error", 
                                "Could not connect to database.\n"
                                "Check that the provided credentials are correct.",
                                QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)
                removeCredentials(uri.database())
                return
            #look in the table directly, in case the layer is not refreshed
            tableFields = [f.name for f in db.get_table_fields(uri.table(), uri.schema())]
            hasIdField = 'geogigid' in tableFields
            func = lambda: self.repo.importpg(uri.database(), username, password, uri.table(),
                          uri.schema(), uri.host(), uri.port(), False, layer.name(), True)
        elif isSpatiaLite:
            provider = layer.dataProvider()
            uri = QgsDataSourceURI(provider.dataSourceUri())
            func = lambda: self.repo.importsl(uri.database(), uri.table(), False, layer.name())

        if not hasIdField:                          
            autoAddId = config.getConfigValue(config.GENERAL, config.AUTO_ADD_ID)
            if not autoAddId:
                dlg = AddGeogigIdDialog(self)
                ok, check = dlg.exec_()                
                if ok == QtGui.QMessageBox.No:
                    self.close()
                    return
                if check:
                    config.setConfigValue(config.GENERAL, config.AUTO_ADD_ID, True)                
            try:                   
                QtGui.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
                addIdField(layer)
                QtGui.QApplication.restoreOverrideCursor()
            except DbError, e:
                ret = QtGui.QMessageBox.warning(self, "Error", 
                                "Problem when accessing database:\n" +
                                unicode(e),
                                QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)                    
                removeCredentials(uri.database())
                return                

        if isPostGis:
            provider = layer.dataProvider()           
            pk = db.get_primary_key_column(uri.table())
            if pk != "geogigid":                
                ret = QtGui.QMessageBox.warning(self, "Warning", 
                                "The layer to import has a 'geogigid' field, but it is not the primary key\n"
                                "You need to set it as the primary key of the table.\n"
                                "Do you want to do it now to be able to import?",
                                QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)
                if ret == QtGui.QMessageBox.No:
                    return
                else:   
                    if pk:   
                        pks = [c for c in db.get_table_constraints(uri.table(), uri.schema()) 
                           if c.con_type == TableConstraint.TypePrimaryKey]              
                        db.table_delete_constraint(uri.table(), pks[0].name, uri.schema())        
                    db.table_add_primary_key(uri.table(), "geogigid", uri.schema())
                        
        if not isPostGis and not isSpatiaLite:
            exported = exportVectorLayer(layer)
            func = lambda: self.repo.importshp(exported, False, layer.name(), "geogigid", True)

        func()

        message = self.messageBox.toPlainText()
        self.repo.add()
        try:
            self.repo.commit(message)
        except UnconfiguredUserException, e:
            configdlg = UserConfigDialog(config.iface.mainWindow())
            configdlg.exec_()
            if configdlg.user is not None:
                self.repo.config(geogig.USER_NAME, configdlg.user)
                self.repo.config(geogig.USER_EMAIL, configdlg.email)
                self.repo.commit(message)
            else:
                return
        except GeoGigException, e:
            if "Nothing to commit" in e.args[0]:
                    config.iface.messageBar().pushMessage("No version has been created. Repository is already up to date",
                                                          level=QgsMessageBar.INFO, duration = 4)
            self.close()
            return
        except:
            self.close()
            raise
                
        addTrackedLayer(self.repo.url, layer or source, layer.name())

        if config.explorer is not None and config.explorer.currentRepo is not None:
            if config.explorer.currentRepo.url == self.repo.url:
                config.explorer.updateCommitsList()
        self.close()


    def cancelPressed(self):
        self.close()

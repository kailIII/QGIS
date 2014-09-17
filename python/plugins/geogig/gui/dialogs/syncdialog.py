from PyQt4 import QtGui, QtCore
from qgis.core import *
from geogig.ui.syncdialog import Ui_SyncDialog
from geogig.gui.dialogs.remotesdialog import RemotesDialog
from geogigpy.geogigexception import GeoGigConflictException
from geogigpy import geogig
from geogig import config
from geogigpy.geogigexception import GeoGigException

class SyncDialog(QtGui.QDialog):
    def __init__(self, repo, name, viewer):
        QtGui.QDialog.__init__(self, config.iface.mainWindow(), QtCore.Qt.WindowSystemMenuHint | QtCore.Qt.WindowTitleHint)
        self.repo = repo
        self.viewer = viewer        
        self.ui = Ui_SyncDialog()
        self.ui.setupUi(self)        
        self.ui.pushButton.clicked.connect(lambda : self.push(True))
        self.ui.pullButton.clicked.connect(lambda : self.pull(True))
        self.ui.syncButton.clicked.connect(self.sync)
        self.ui.closeButton.clicked.connect(self.close)
        self.ui.manageRemotesButton.clicked.connect(self.manageRemotes)
        
        self.updateRemotesList()
        
    def updateRemotesList(self):
        self.ui.comboBox.clear()
        remotes  = self.repo.remotes
        self.ui.comboBox.addItems(remotes.keys())
        self.ui.pullButton.setEnabled(len(remotes.keys()) > 0)
        self.ui.pushButton.setEnabled(len(remotes.keys()) > 0)
        self.ui.syncButton.setEnabled(len(remotes.keys()) > 0)
        
    
    def manageRemotes(self):
        dlg = RemotesDialog(self, self.repo)
        dlg.exec_()
        if dlg.changed:
            self.updateRemotesList()
            self.viewer.updateSyncLabel() 
        
    def pull(self, close):        
        remote = self.ui.comboBox.currentText()       
        try:
            head = self.repo.head.ref
            self.repo.pull(remote, head)
            if close:
                QtGui.QMessageBox.information(self, 'Pull',
                    "Local repository has correctly been updated.",
                    QtGui.QMessageBox.Ok)
                self.viewer.updateCommitsList()
                self.close()                
            return True
        except GeoGigConflictException:
            QtGui.QMessageBox.warning(self, 'Conflicts',
                    "There are some conflicted elements after updating the local repository\n."
                    + "Please solve the conflict and then commit the changes",
                    QtGui.QMessageBox.Ok)
            self.viewer.updateRepoStatusLabelAndToolbar()    
            self.viewer.updateCommitsList()        
            return False;        
        except GeoGigException, e:
            if "FileNotFound" in unicode(e):
                raise GeoGigException("Remote repository '%s' does not exist." % remote)
            else:
                raise e
             
    
    def push(self, close):   
        try:     
            remote = self.ui.comboBox.currentText()
            if self.ui.syncAllCheckBox.isChecked():
                self.repo.push(remote, all = True)
            else:
                head = self.repo.head.ref
                self.repo.push(remote, head)
            
            if close:
                QtGui.QMessageBox.information(self, 'Push',
                        "Remote repository has correctly been updated.",
                        QtGui.QMessageBox.Ok)
                self.viewer.updateSyncLabel()
                self.close()
        except GeoGigException, e:
            if "FileNotFound" in unicode(e):
                raise GeoGigException("Remote repository '%s' does not exist." % remote)
            else:
                raise e
    
    def sync(self):
        if self.pull(False):
            self.push(False)
            QtGui.QMessageBox.information(self, 'Synchronization correctly performed',
                    "Repositories have been successfully synchronized.",
                    QtGui.QMessageBox.Ok)
        self.viewer.updateCommitsList()
        self.close()
                
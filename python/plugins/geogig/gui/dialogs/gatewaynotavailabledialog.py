from PyQt4 import QtGui, QtCore
import os
import webbrowser

errorIcon = os.path.dirname(__file__) + "/../../ui/resources/error.png"
addupdateIcon = os.path.dirname(__file__) + "/../../ui/resources/addupdate.png"
    
class GatewayNotAvailableDialog(QtGui.QDialog):
    
    def __init__(self, parent = None):
        super(GatewayNotAvailableDialog, self).__init__(parent)        
        self.initGui()

    def initGui(self):                         
        layout = QtGui.QVBoxLayout()                                
        buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Close)
        class MyBrowser(QtGui.QTextBrowser):
            def loadResource(self, type_, name):                
                return None        
        self.textBrowser = MyBrowser()
        self.textBrowser.connect(self.textBrowser, QtCore.SIGNAL("anchorClicked(const QUrl&)"), self.linkClicked)        
        text = '"<html><img src="' + errorIcon + '"/><h3>Cannot connect to GeoGig.</h3>'
        text += "<p>To connect to GeoGig, you must install GeoGig and have the GeoGig gateway running:</p>"
        #text += '<p>Click <a href = "help">here</a> to know more about how to install and run GeoGig</p></html>'        
        self.textBrowser.setHtml(text)        
        layout.addWidget(self.textBrowser)        
        layout.addWidget(buttonBox)
        self.setLayout(layout)
        
        self.connect(buttonBox, QtCore.SIGNAL("rejected()"), self.close)
        
        self.resize(500, 400)
        self.setWindowTitle("Error connecting to GeoGig")
        
    def linkClicked(self):
        webbrowser.open_new_tab("http://ujo.com")  
        self.close()
        
class GatewayNotAvailableWhileEditingDialog(GatewayNotAvailableDialog): 
    
    def initGui(self):
        GatewayNotAvailableDialog.initGui(self)
        text = self.textBrowser.toHtml()        
        text += "<p>The layer has been modified, but the changes haven't been incorporated in the repository."
        text += " To update the repository once you have started the gateway, use the <i>Add/update<i> button</p>."
        text += '<img src="' + addupdateIcon + '"/>'  
        self.textBrowser.setHtml(text)  
        
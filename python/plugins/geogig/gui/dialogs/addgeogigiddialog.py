from PyQt4.QtCore import *
from PyQt4.QtGui import *
 
class AddGeogigIdDialog(QMessageBox):
 
    def __init__(self, parent= None):
        super(AddGeogigIdDialog, self).__init__()
 
        self.checkbox = QCheckBox()
        #Access the Layout of the MessageBox to add the Checkbox
        layout = self.layout()
        layout.addWidget(self.checkbox, 1,1)
        
        self.setWindowTitle("Missing Id field")
        self.setText("The layer to import doesn't have a 'geogigid' field\n"
                    "You need to create a 'geogigid' field before importing\n"
                    "Do you want to create one automatically before importing?")
        self.checkbox.setText("Do not ask again. Add 'geogigid' field automatically")
        self.setStandardButtons(QMessageBox.Yes |QMessageBox.No)
        self.setDefaultButton(QMessageBox.Yes)
        self.setIcon(QMessageBox.Warning)
 
    def exec_(self, *args, **kwargs):
        return QMessageBox.exec_(self, *args, **kwargs), self.checkbox.isChecked()
 

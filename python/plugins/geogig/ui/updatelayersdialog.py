# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'updatelayersdialog.ui'
#
# Created: Wed Aug 13 10:42:41 2014
#      by: PyQt4 UI code generator 4.11.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_UpdateLayersDialog(object):
    def setupUi(self, UpdateLayersDialog):
        UpdateLayersDialog.setObjectName(_fromUtf8("UpdateLayersDialog"))
        UpdateLayersDialog.resize(535, 342)
        self.horizontalLayout = QtGui.QHBoxLayout(UpdateLayersDialog)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.label = QtGui.QLabel(UpdateLayersDialog)
        self.label.setObjectName(_fromUtf8("label"))
        self.verticalLayout.addWidget(self.label)
        self.lstLayers = QtGui.QListView(UpdateLayersDialog)
        self.lstLayers.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.lstLayers.setAlternatingRowColors(True)
        self.lstLayers.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
        self.lstLayers.setObjectName(_fromUtf8("lstLayers"))
        self.verticalLayout.addWidget(self.lstLayers)
        self.progressBar = QtGui.QProgressBar(UpdateLayersDialog)
        self.progressBar.setProperty("value", 0)
        self.progressBar.setTextVisible(False)
        self.progressBar.setObjectName(_fromUtf8("progressBar"))
        self.verticalLayout.addWidget(self.progressBar)
        self.horizontalLayout.addLayout(self.verticalLayout)
        self.buttonBox = QtGui.QDialogButtonBox(UpdateLayersDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Vertical)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.horizontalLayout.addWidget(self.buttonBox)

        self.retranslateUi(UpdateLayersDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), UpdateLayersDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), UpdateLayersDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(UpdateLayersDialog)

    def retranslateUi(self, UpdateLayersDialog):
        UpdateLayersDialog.setWindowTitle(_translate("UpdateLayersDialog", "Update layers", None))
        self.label.setText(_translate("UpdateLayersDialog", "The repository head has changed. Do you want to update the following layers?", None))


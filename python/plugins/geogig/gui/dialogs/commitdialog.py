from PyQt4 import QtGui, QtCore
from geogigpy import geogig

class CommitDialog(QtGui.QDialog):

    def __init__(self, repo, parent = None, showSelector = True, allowCancel = True):
        super(CommitDialog, self).__init__(parent)
        self.repo = repo
        self.paths = None
        self.showSelector = showSelector
        self._closing = allowCancel
        self.allowCancel = allowCancel
        if showSelector:
            self.diffs = repo.difftreestats(geogig.HEAD, geogig.WORK_HEAD)
        self.initGui()

    def initGui(self):
        if self.showSelector:
            self.resize(600, 400)
        else:
            self.resize(600, 250)
        self.setWindowTitle('Ujo')

        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setMargin(5)

        self.msgLabel = QtGui.QLabel("Message to describe this update")
        self.verticalLayout.addWidget(self.msgLabel)

        if self.showSelector:
            self.splitter = QtGui.QSplitter(self)
            self.splitter.setOrientation(QtCore.Qt.Vertical)
            self.text = QtGui.QPlainTextEdit(self.splitter)

            self.verticalLayout2 = QtGui.QVBoxLayout(self.splitter)
            self.verticalLayout2.setSpacing(2)
            self.verticalLayout2.setMargin(5)

            self.table = QtGui.QTableWidget()
            self.table.setColumnCount(1)
            self.table.setShowGrid(False)
            self.table.verticalHeader().hide()
            self.table.setHorizontalHeaderLabels(["Path"])
            self.table.horizontalHeader().setMinimumSectionSize(150)
            self.table.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
            self.table.setRowCount(len(self.diffs))
            for i, path in enumerate(self.diffs.keys()):
                counts = self.diffs[path]
                widget = QtGui.QTableWidgetItem(path + " [+%i/-%i/~%i]" % counts)
                widget.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
                widget.setCheckState(QtCore.Qt.Checked)
                self.table.setItem(i, 0, widget);
            self.table.horizontalHeader().setStretchLastSection(True)
            self.table.resizeRowsToContents()
            self.linksLabel = QtGui.QLabel('  <qt> <a href = "all">All</a> &nbsp; &nbsp; &nbsp; <a href = "none">None</a></qt>')
            self.connect(self.linksLabel, QtCore.SIGNAL("linkActivated(QString)"), self.linkClicked)
            self.verticalLayout2.addWidget(self.linksLabel)
            self.verticalLayout2.addWidget(self.table)

            self.verticalLayout.addWidget(self.splitter)
        else:
            self.text = QtGui.QPlainTextEdit()
            self.verticalLayout.addWidget(self.text)

        if self.allowCancel:
            self.buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Close)
            self.buttonBox.rejected.connect(self.cancelPressed)
        else:
            self.buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok)
        self.verticalLayout.addWidget(self.buttonBox)
        self.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(False)
        self.setLayout(self.verticalLayout)

        self.buttonBox.accepted.connect(self.okPressed)

        self.text.textChanged.connect(self.textHasChanged)
        if self.repo.ismerging():
            self.text.setPlainText(self.repo.mergemessage())

    def linkClicked(self, s):
        if s == "all":
            self.selectAll()
        else:
            self.selectNone()

    def selectNone(self):
        for i, diff in enumerate(self.diffs):
            self.table.item(i, 0).setCheckState(QtCore.Qt.Unchecked);

    def selectAll(self):
        for i, diff in enumerate(self.diffs):
            self.table.item(i, 0).setCheckState(QtCore.Qt.Checked);

    def textHasChanged(self):
        self.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(self.text.toPlainText() != "")

    def getPaths(self):
        return self.paths

    def getMessage(self):
        return self.text.toPlainText()

    def okPressed(self):
        self.paths = []
        if self.showSelector:
            for i, path in enumerate(self.diffs):
                widget = self.table.item(i, 0)
                state = widget.checkState()
                if state == QtCore.Qt.Checked:
                    self.paths.append(path)
            if not self.paths:
                QtGui.QMessageBox.information(self, "Cannot create version",
                            "No elements has been selected.\n Empty versions are not allowed.")
            else:
                if len(self.paths) == len(self.diffs):
                    self.paths = []
                self.closeDialog()
        else:
            self.closeDialog()

    def cancelPressed(self):
        self.paths = None
        self.closeDialog()

    def closeDialog(self):
        self._closing = True
        self.close()

    def closeEvent(self, evnt):
        if self._closing:
            super(CommitDialog, self).closeEvent(evnt)
        else:
            evnt.ignore()

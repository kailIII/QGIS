import os
import datetime
import logging
from PyQt4 import QtGui, QtCore
from qgis.core import *
from qgis.gui import *
from geogig.ui.repoviewer import Ui_GeoGigSimpleViewer
from geogigpy.commitish import Commitish
from geogigpy.commit import Commit
from geogigpy.tree import Tree
from geogigpy.geogigexception import GeoGigConflictException, UnconfiguredUserException
from geogig.gui.dialogs.syncdialog import SyncDialog
from geogig.gui.dialogs.diffviewerdialog import DiffViewerDialog
from geogig.gui.dialogs.commitdialog import CommitDialog
from geogigpy import geogig
from geogig.gui.dialogs.geogigref import CommitListItem
from geogig.gui.dialogs.createbranch import CreateBranchDialog
from geogig.gui.dialogs import reposelector
from geogig.gui.dialogs.conflictdialog import ConflictDialog
from geogig import config
from geogig.gui.dialogs.checkoutdialog import CheckoutDialog
from geogig.gui.dialogs.mergedialog import MergeDialog
from geogig.tools.exporter import exportFromGeoGigToTempFile
from geogig.gui.dialogs.userconfigdialog import UserConfigDialog
from geogig.gui.dialogs.exportdialog import ExportDialog
from geogig.gui.dialogs.simpleimportdialog import SimpleImportDialog
from geogig.tools.layertracking import updateOpenTrackedLayers

_logger = logging.getLogger("geogigpy")

class GeoGigViewer(QtGui.QDockWidget):

    CHANGES_THRESHOLD = 300

    def __init__(self, repo):
        QtGui.QDialog.__init__(self)
        self.ui = Ui_GeoGigSimpleViewer()
        self.ui.setupUi(self)

        self.currentRepo = None
        self.currentRepoName = None
        self.currentCommit = None

        self.setRepo(repo)
        self.ui.commitRepoButton.clicked.connect(self.commit)
        self.ui.changeRepoButton.clicked.connect(self.changeRepo)
        self.ui.syncRepoButton.clicked.connect(self.syncRepo)
        self.ui.mergeButton.clicked.connect(self.merge)
        self.ui.importButton.clicked.connect(self.importButtonClicked)
        self.ui.exportButton.clicked.connect(self.exportButtonClicked)
        self.ui.commitsList.itemClicked.connect(self.commitClicked)
        self.ui.commitsList.itemDoubleClicked.connect(self.commitDoubleClicked)
        self.ui.commitsFilterBox.textChanged.connect(self.filterCommits)
        self.topLevelChanged.connect(self.dockStateChanged)
        self.ui.diffSelectedButton.clicked.connect(self.diffSelected)
        self.ui.commitDiffButton.clicked.connect(self.commitDiffs)
        self.connect(self.ui.repoStatusLabel, QtCore.SIGNAL("linkActivated(QString)"), self.repoStatusLabelLinkClicked)
        self.connect(self.ui.syncLabel, QtCore.SIGNAL("linkActivated(QString)"), self.syncRepo)
        self.connect(self.ui.branchLabel, QtCore.SIGNAL("linkActivated(QString)"), self.branchLabelLinkClicked)
        self.ui.commitsList.customContextMenuRequested.connect(self.showCommitContextMenu)
        self.ui.importButton.setText("Add/update layer")
        self.ui.commitRepoButton.setVisible(False)

    def changeRepo(self):
        repo = reposelector.getRepo()
        if repo is not None:
            self.setRepo(repo)                         

    def setRepo(self, repo):
        repo.repo.cleancache()
        self.currentRepo = repo.repo
        self.currentRepoName = repo.name
        self.updateCommitsList()

    def showCommitContextMenu(self, point):
        item = self.ui.commitsList.itemAt(point)
        menu = QtGui.QMenu()
        resetIcon = QtGui.QIcon(os.path.dirname(__file__) + "/../ui/resources/reset.png")
        resetAction = QtGui.QAction(resetIcon, "Reset current branch to this version (delete newer versions)", None)
        resetAction.triggered.connect(lambda: self.resetToCommit(item.commit))    
        menu.addAction(resetAction)    
        revertAction = QtGui.QAction(resetIcon, "Revert current branch to this version (add reverted changes)", None)
        revertAction.triggered.connect(lambda: self.revertToCommit(item.commit))
        menu.addAction(revertAction)
        checkoutIcon = QtGui.QIcon(os.path.join(os.path.dirname(__file__), os.pardir, "ui", "resources", "checkout.png"))
        checkoutAction = QtGui.QAction(checkoutIcon, "Checkout this version", None)
        checkoutAction.triggered.connect(lambda: self.checkoutCommit(item.commit))
        menu.addAction(checkoutAction)
        branchIcon = QtGui.QIcon(os.path.join(os.path.dirname(__file__), os.pardir, "ui", "resources", "create_branch.png"))
        branchAction = QtGui.QAction(branchIcon, "Create branch at this version...", None)
        branchAction.triggered.connect(lambda: self.createBranchAtCommit(item.commit))
        menu.addAction(branchAction)
        tagIcon = QtGui.QIcon(os.path.join(os.path.dirname(__file__), os.pardir, "ui", "resources", "tag.gif"))
        tagAction = QtGui.QAction(tagIcon, "Create tag at this version...", None)
        tagAction.triggered.connect(lambda: self.createTagAtCommit(item.commit))
        menu.addAction(tagAction)

        point = self.ui.commitsList.mapToGlobal(point)
        menu.exec_(point)

    def merge(self):
        dlg = MergeDialog(self.currentRepo)
        dlg.exec_()
        if dlg.ref is not None:
            try:
                self.currentRepo.merge(dlg.ref)
                self.updateCommitsList()
                updateOpenTrackedLayers(self.currentRepo)
            except GeoGigConflictException:
                QtGui.QMessageBox.warning(self, 'Conflicts',
                    "There are some conflicted elements after merging\n."
                    + "Please solve the conflicts and then commit the changes",
                    QtGui.QMessageBox.Ok)
                self.updateRepoStatusLabelAndToolbar()


    def createBranchAtCommit(self, commit):
        dlg = CreateBranchDialog(self.topLevelWidget())
        dlg.exec_()
        if dlg.ok:
            self.currentRepo.createbranch(commit.ref, dlg.getName(), dlg.isForce(), dlg.isCheckout())
            if dlg.isCheckout():
                self.updateCommitsList()
                updateOpenTrackedLayers(self.currentRepo)

    def createTagAtCommit(self, commit):
        name, ok = QtGui.QInputDialog.getText(self.topLevelWidget(), 'Tag name','Enter tag name:')
        if ok:
            self.currentRepo.createtag(commit.ref, unicode(name), unicode(name))

    def checkoutCommit(self, commit):
        self.currentRepo.checkout(commit.ref)
        self.updateCommitsList()
        updateOpenTrackedLayers(self.currentRepo)

    def resetToCommit(self, commit):
        self.currentRepo.reset(commit.ref, geogig.RESET_MODE_HARD)
        self.updateCommitsList()
        updateOpenTrackedLayers(self.currentRepo)
    
    def revertToCommit(self, commit):
        head = self.currentRepo.head.id
        self.currentRepo.reset(commit.ref, geogig.RESET_MODE_HARD)
        self.currentRepo.reset(head, geogig.RESET_MODE_MIXED)
        self.currentRepo.addandcommit("Reverted to commit %s (%s)" % (commit.ref, commit.message))
        self.updateCommitsList()
        updateOpenTrackedLayers(self.currentRepo)        

    def commit(self):
        dlg = CommitDialog(self.currentRepo, self, False)
        dlg.exec_()
        if dlg.getPaths() is not None:
            self.currentRepo.add(dlg.getPaths())
            try:
                self.currentRepo.commit(dlg.getMessage())
            except UnconfiguredUserException, e:
                configdlg = UserConfigDialog(config.iface.mainWindow())
                configdlg.exec_()
                if configdlg.user is not None:
                    self.currentRepo.config(geogig.USER_NAME, configdlg.user)
                    self.currentRepo.config(geogig.USER_EMAIL, configdlg.email)
                    self.currentRepo.commit(dlg.getMessage())
                else:
                    return

            self.updateRepoStatusLabelAndToolbar()
            self.updateCommitsList()

    def diffSelected(self):
        selected = self.ui.commitsList.selectedItems()
        if len(selected) == 0:
            QtGui.QMessageBox.warning(self, 'Cannot compare',
                    "Select 1 or 2 versions to compare.",
                    QtGui.QMessageBox.Ok)
        elif len(selected) == 1:
            self.diff(selected[0].commit.parent, selected[0].commit)
        elif len(selected) == 2:
            self.diff(selected[0].commit, selected[1].commit)
        else:
            QtGui.QMessageBox.warning(self, 'Cannot compare',
                    "Select at most 2 versions to compare.",
                    QtGui.QMessageBox.Ok)

    def commitDiffs(self):
        if self.currentCommit is not None:
            if len(self.currentCommit._parents) > 1:
                menu = QtGui.QMenu()
                actions = []
                for i in range(len(self.currentCommit._parents)):
                    action = QtGui.QAction("parent " + str(i + 1), None)
                    actions.append(action)
                for i, a in enumerate(actions):
                    a.triggered[()].connect(lambda i = i: self.showDiffWithParent(self.currentCommit,i))
                    menu.addAction(a)
                menu.exec_(QtGui.QCursor.pos())
            else:
                self.diff(self.currentCommit.parent, self.currentCommit)

    def showDiffWithParent(self, commit, parentidx):
        parentid = commit._parents[parentidx]
        parent = Commit.fromref(self.currentRepo, parentid)
        self.diff (commit, parent)

    def diff(self, refa, refb):
        dlg = DiffViewerDialog(self.currentRepo, refa, refb)
        dlg.exec_()

    def syncRepo(self):
        dlg = SyncDialog(self.currentRepo, self.currentRepoName, self)
        dlg.exec_()

    def importButtonClicked(self):
        dlg = SimpleImportDialog(self, self.currentRepo)
        dlg.exec_()

    def exportButtonClicked(self):
        dlg = ExportDialog(self, self.currentRepo)
        dlg.exec_()

    def dockStateChanged(self, floating):
        if floating:
            self.resize(900, 450)
            self.ui.splitter.setOrientation(QtCore.Qt.Horizontal)
        else:
            self.ui.splitter.setOrientation(QtCore.Qt.Vertical)


    def filterCommits(self):
        text = self.ui.commitsFilterBox.text().strip()
        try:
            t = datetime.datetime.strptime(text, "%d/%m/%Y")
            found = False
            for i in xrange(self.ui.commitsList.count()):
                item = self.ui.commitsList.item(i)
                if found:
                    item.setHidden(True)
                else:
                    delta = item.commit.committerdate - t
                    found = delta.days < 0
                    item.setHidden(not found)

        except ValueError, e:
            for i in xrange(self.ui.commitsList.count()):
                item = self.ui.commitsList.item(i)
                msg = item.commit.message
                item.setHidden(text != "" and text not in msg)


    def commitDoubleClicked(self):
        commit = self.ui.commitsList.currentItem().commit
        self.currentCommit = commit
        self.diff(self.currentCommit.parent, self.currentCommit)

    def commitClicked(self):
        commit = self.ui.commitsList.currentItem().commit
        if self.currentCommit is not None and commit.ref == self.currentCommit.ref:
            return
        self.currentCommit = commit
        self.updateCommitDescription()

    def updateCommitDescription(self):
        self.ui.commitDetailText.setText("")
        self.ui.commitMessageText.setText("")
        featureCounts = {}
        if self.currentCommit is None:
            if self.ui.commitsList.count():
                self.currentCommit = self.ui.commitsList.item(0).commit
            else:
                return
        commit = self.currentCommit
        s = ("<b>Version ID: %s</b><br> %s by %s<br>" %
            (str(commit.commitid[:20]), str(commit.committerdate), commit.committername))
        diffs = commit.difftreestats()
        #diffs = execute(commit.difftreestats,  "Retrieving current commit information")
        total = 0
        for path, counts in diffs.iteritems():
            subtotal = sum(counts)
            total += subtotal
        s += "<b> %i features</b> modified across <b> %i layers</b>" %( total, len(diffs))
        self.ui.commitDetailText.setText(s)
        self.ui.commitMessageText.setText(commit.message)
        self.ui.treeList.clear()
        tree = Tree(self.currentRepo, commit.ref)
        for subtree in tree.trees:
            item = LayerItem(subtree.path)
            featureCounts[item] = subtree.size
            self.ui.treeList.addItem(item)
        for item in featureCounts:
            widget = LayerWidget(self.currentRepo, self.currentCommit, item.path, self, featureCounts[item])
            self.ui.treeList.setItemWidget(item, widget)


    def updateCommitsList(self):
        def _update():
            self.currentCommit = None
            self.ui.commitsList.clear()
            self.ui.treeList.clear()
            log = self.currentRepo.log()
            for commit in log:
                item = CommitListItem(commit)
                self.ui.commitsList.addItem(item)
            self.ui.commitCountLabel.setText("%i versions:" % len(log))
            self.ui.repoTitle.setText("<b>Location:</b> " + self.currentRepo.url)
            self.ui.repoNameLabel.setText("REPOSITORY: " + self.currentRepoName)
            self.updateRepoStatusLabelAndToolbar()
            self.updateSyncLabel()
            self.updateBranchLabel()
        _update()
        self.updateCommitDescription()
        #execute(_update, "Updating repository viewer")


    def update(self):
        self.updateCommitsList()
        self.updateRepoStatusLabelAndToolbar()
        self.updateSyncLabel()

    def updateRepoStatusLabelAndToolbar(self):
        if self.currentRepo is None:
            return
        unstaged = self.currentRepo.difftreestats(geogig.HEAD, geogig.WORK_HEAD)
        total = 0
        for counts in unstaged.values():
            total += sum(counts)

        s = ""
        if total:
            s = ('%i features modified across %i layers '  % (total, len(unstaged))
                + '&nbsp; <a href="view">view</a> &nbsp; <a href="discard">discard'
                '</a> &nbsp; <a href="commit">commit</a> &nbsp; &nbsp; &nbsp;')
        conflicts = len(self.currentRepo.conflicts())
        if conflicts:
            s = 'There are %i conflicted features. &nbsp; <a href="solve">solve conflicts</a> &nbsp;  <a href="abort">abort</a>' % conflicts

        self.ui.repoStatusLabel.setText(s)
        self.ui.repoStatusLabel.setVisible(s != "")

        self.ui.mergeButton.setEnabled(not conflicts and total == 0)
        self.ui.commitRepoButton.setEnabled(not conflicts and total > 0)
        self.ui.syncRepoButton.setEnabled(not conflicts)

    def updateBranchLabel(self):
        if self.currentRepo.isdetached():
            ref = "no branch"
        else:
            ref = self.currentRepo.head.ref
        s = 'Current branch: <b>%s</b> '  % (ref) + '&nbsp; <a href="change">change</a>'
        self.ui.branchLabel.setText(s)

    def branchLabelLinkClicked(self, url):
        oldRef = self.currentRepo.head
        dialog = CheckoutDialog(self.currentRepo, self)
        dialog.exec_()
        ref = dialog.ref
        if ref is not None:
            if dialog.branchName is not None:
                self.currentRepo.createbranch(ref.ref, dialog.branchName, False, True)
            else:
                self.currentRepo.checkout(ref.ref)
            self.updateCommitsList()
            if ref.ref != oldRef.ref:
                updateOpenTrackedLayers(self.currentRepo)

    def repoStatusLabelLinkClicked(self, url):
        if url == "commit":
            self.commit()
        if url == "discard":
            if self.ui.commitsList.count() > 0:
                self.currentRepo.reset(geogig.HEAD, geogig.RESET_MODE_HARD)
            else:
                children = self.currentRepo.children(ref = geogig.WORK_HEAD, recursive = False)
                paths = [c.path for c in children if isinstance(c, Tree)]
                self.currentRepo.removetrees(paths)
            self.updateRepoStatusLabelAndToolbar()
        if url == "view":
            self.diff(Commitish(self.currentRepo, geogig.HEAD), Commitish(self.currentRepo, geogig.WORK_HEAD))
        if url =="solve":
            self.solveConflicts()
        if url =="abort":
            self.abort()

    def abort(self):
        self.currentRepo.abort()
        self.updateRepoStatusLabelAndToolbar()

    def updateSyncLabel(self):
        if self.currentRepo.isdetached():
            self.ui.syncLabel.setText("")
        else:
            try:
                ref = self.currentRepo.head.ref
                ahead, behind = self.currentRepo.synced(ref, 
                                        credentials = reposelector.getUjoCredentials())
                if ahead + behind != 0:
                    self.ui.syncLabel.setText(u'\u25B2 %i \u25BC %i <a href="sync"> sync </a>' % (ahead, behind))
                else:
                    self.ui.syncLabel.setText("")
            except Exception, e:
                self.ui.syncLabel.setText("")

    def solveConflicts(self):
        dlg = ConflictDialog(self, self.currentRepo)
        dlg.exec_()
        if dlg.solved:
            self.updateRepoStatusLabelAndToolbar()



class LayerItem(QtGui.QListWidgetItem):
    def __init__(self, path):
        QtGui.QTreeWidgetItem.__init__(self)
        self.path = path
        self.setSizeHint(QtCore.QSize(0, 22))

class LayerWidget(QtGui.QWidget):

    def __init__(self, repo, commit, path, viewer, count):
        QtGui.QWidget.__init__(self)
        self.repo = repo
        self.path = path
        self.commit = commit
        self.viewer = viewer
        layout = QtGui.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.hlayout = QtGui.QHBoxLayout()
        self.hlayout.setContentsMargins(0, 0, 0, 0)
        self.hlayout.setSpacing(0)
        layerLabel = QtGui.QLabel()
        layerLabel.setPixmap(QtGui.QPixmap(os.path.join(os.path.dirname(__file__), os.pardir, "ui", "resources", "layer.png")))
        self.hlayout.addWidget(layerLabel)
        if count is None:
            s = path
        else:
            s = " %s [%i features]" % (path, count)
        nameLabel = QtGui.QLabel(s)
        self.hlayout.addWidget(nameLabel)
        spacerItem = QtGui.QSpacerItem(10, 20, QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Minimum)
        self.hlayout.addItem(spacerItem)
        exportButton = QtGui.QToolButton()
        exportIcon = QtGui.QIcon(os.path.join(os.path.dirname(__file__), os.pardir, "ui", "resources", "export_geogig_tree.png"))
        exportButton.setIcon(exportIcon)
        exportButton.setAutoRaise(True)
        exportButton.setToolTip("Export this layer to QGIS project")
        exportButton.clicked.connect(self.export)
        self.hlayout.addWidget(exportButton)
        layout.addLayout(self.hlayout)
        self.setLayout(layout)


    def export(self):
        hasField = exportFromGeoGigToTempFile(self.repo, self.commit.ref, self.path)
        if not hasField:
            QtGui.QMessageBox.warning(None, "Warning", "The exported layer doesn't have an 'geogigid' field.\n"
                                                        "It will not be tracked and changes to the layer will\n"
                                                        "not be automatically updated in the Ujo repository.\n"
                                                        "Add a 'geogigid' field and re-import to correct this.")

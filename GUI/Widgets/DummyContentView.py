from GUI.ProjectSelection import ProjectSelection
from GUI.ViewModel.ViewModel import ProjectViewModel
from GUI.Widgets.SelectionView import SelectionView


from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QFrame, QVBoxLayout


class DummyContentView(QFrame):
    """
    A dummy content view that doesn't show the subtitles
    """
    onSelection = Signal()
    actionRequested = Signal(str, object)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.viewmodel = None
        self.selection_view = SelectionView()
        self.selection_view.actionRequested.connect(self.actionRequested)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.selection_view)
        self.setLayout(self.layout)

    def ShowSelection(self, selection : ProjectSelection):
        self.selection_view.ShowSelection(selection)

    def Populate(self, viewmodel : ProjectViewModel):
        self.viewmodel = viewmodel
        self.viewmodel.updatesPending.connect(self._update_view_model, type=Qt.ConnectionType.QueuedConnection)
        self.ShowSelection(ProjectSelection())

    def Clear(self):
        self.viewmodel = ProjectViewModel()
        self.ShowSelection(ProjectSelection())

    def GetSelectedLines(self):
        return []

    def ClearSelectedLines(self):
        pass

    @Slot()
    def _update_view_model(self):
        if self.viewmodel:
            self.viewmodel.ProcessUpdates()
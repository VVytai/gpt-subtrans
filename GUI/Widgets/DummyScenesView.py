from GUI.ScenesBatchesModel import ScenesBatchesModel
from GUI.ViewModel.BatchItem import BatchItem
from GUI.ViewModel.SceneItem import SceneItem

from PySide6.QtCore import QAbstractItemModel, QItemSelectionModel, Qt, Signal
from PySide6.QtWidgets import QAbstractItemView, QTreeView

class DummyScenesView(QTreeView):
    """
    Stripped down scenes view for debugging the viewmodel
    """
    onSelection = Signal()
    onSceneEdited = Signal(int, object)
    onBatchEdited = Signal(int, int, object)

    def __init__(self, parent=None, viewmodel=None):
        super().__init__(parent)

        self.setMinimumWidth(450)
        self.setIndentation(20)
        self.setHeaderHidden(True)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        self.Populate(viewmodel)

    def Clear(self):
        self.Populate([])

    def Populate(self, viewmodel):
        self.viewmodel = viewmodel
        model = ScenesBatchesModel(self.viewmodel)
        self.setModel(model)
        self.selectionModel().selectionChanged.connect(self._item_selected)

    def _item_selected(self, selected, deselected):
        model : QAbstractItemModel = self.model()

        for index in selected.indexes():
            data = model.data(index, role=Qt.ItemDataRole.UserRole)
            if isinstance(data, SceneItem):
                self._deselect_children(model, index, data)
                self.expand(index)
            elif isinstance(data, BatchItem):
                self._deselect_parent(model, index)

        self.onSelection.emit()

    def _select_children(self, model, index, data):
        scene_item = data
        selection_model = self.selectionModel()
        selection_flags = QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows

        for row in range(scene_item.rowCount()):
            batch_item_index = model.index(row, 0, index)
            selection_model.select(batch_item_index, selection_flags)

    def _deselect_children(self, model, index, item):
        selection_model = self.selectionModel()
        selection_flags = QItemSelectionModel.SelectionFlag.Deselect | QItemSelectionModel.SelectionFlag.Rows

        for row in range(item.rowCount()):
            batch_item_index = model.index(row, 0, index)
            selection_model.select(batch_item_index, selection_flags)

    def _deselect_parent(self, model, index):
        selection_model = self.selectionModel()
        selection_flags = QItemSelectionModel.SelectionFlag.Deselect | QItemSelectionModel.SelectionFlag.Rows
        selection_model.select(model.parent(index), selection_flags)
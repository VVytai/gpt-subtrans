import os
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QFrame, QHBoxLayout, QPushButton, QSizePolicy

from GUI.GuiInterface import GuiInterface
from GUI.ProjectActions import ProjectActions
from GUI.ProjectSelection import ProjectSelection
from PySubtitle.Instructions import DEFAULT_TASK_TYPE

def _show(widget, condition):
    if condition:
        widget.show()
    else:
        widget.hide()

class SelectionView(QFrame):
    resetSelection = Signal()

    def __init__(self, action_handler : ProjectActions, parent=None):
        super().__init__(parent=parent)

        self.action_handler = action_handler
        self.debug_view = os.environ.get("DEBUG_MODE") == "1"

        self._label = QLabel(self)
        self._label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)

        #TODO: Translate / Retranslate label
        self._translate_button = self._create_button("Translate Selection", self._on_translate_selection)
        self._autosplit_batch_button = self._create_button("Auto-Split Batch", self._on_auto_split_batch)
        self._reparse_button = self._create_button("Reparse Translation", self._on_reparse)
        self._split_batch_button = self._create_button("Split Batch", self._on_split_batch)
        self._split_scene_button = self._create_button("Split Scene", self._on_split_scene)
        self._merge_lines_button = self._create_button("Merge Lines", self._on_merge_selection)
        self._merge_scenes_button = self._create_button("Merge Scenes", self._on_merge_selection)
        self._merge_batches_button = self._create_button("Merge Batches", self._on_merge_selection)
        self._delete_lines_button = self._create_button("Delete Lines", self._on_delete_lines)
        self._swap_text_button = self._create_button("Swap Text", self._on_swap_text)

        self.ShowSelection(ProjectSelection())

        layout = QHBoxLayout(self)
        layout.addWidget(self._label)
        layout.addWidget(self._swap_text_button)
        layout.addWidget(self._split_scene_button)
        layout.addWidget(self._autosplit_batch_button)
        layout.addWidget(self._split_batch_button)
        layout.addWidget(self._merge_lines_button)
        layout.addWidget(self._merge_scenes_button)
        layout.addWidget(self._merge_batches_button)
        layout.addWidget(self._delete_lines_button)
        layout.addWidget(self._reparse_button)
        layout.addWidget(self._translate_button)

        self.setLayout(layout)

    def ShowSelection(self, selection : ProjectSelection):
        self.selection = selection

        if self.debug_view and self._debug_text(selection):
            self._label.setText(f"{str(selection)} {self._debug_text(selection)}")
        else:
            self._label.setText(str(selection))

        _show(self._translate_button, selection.lines and selection.Any())
        _show(self._reparse_button, selection.AnyBatches() and selection.AllTranslated())
        _show(self._autosplit_batch_button, selection.AnyBatches() and selection.OnlyBatches() and not selection.MultipleSelected())
        _show(self._split_batch_button, selection.AnyLines() and not selection.MultipleSelected() and not selection.IsFirstInBatchSelected())
        _show(self._split_scene_button, selection.AnyBatches() and not selection.MultipleSelected() and not selection.IsFirstInSceneSelected())
        _show(self._merge_scenes_button, selection.OnlyScenes() and selection.MultipleSelected() and selection.IsContiguous())
        _show(self._merge_batches_button, selection.OnlyBatches() and selection.MultipleSelected() and selection.IsContiguous())
        _show(self._merge_lines_button, selection.AnyLines() and selection.MultipleSelected(max=3) and selection.IsContiguous() and selection.AllLinesInSameBatch())
        _show(self._delete_lines_button, selection.AnyLines())
        _show(self._swap_text_button, False and selection.AnyBatches() and not selection.MultipleSelected())

    def SetTaskType(self, task_type : str):
        if task_type == DEFAULT_TASK_TYPE:
            self._translate_button.setText("Translate Selection")
        elif task_type == "Improvement":
            self._translate_button.setText("Improve Selection")
        else:
            self._translate_button.setText(f"Selection {task_type}")

    def _create_button(self, text, on_click):
        button = QPushButton(text, self)
        button.clicked.connect(on_click, Qt.ConnectionType.QueuedConnection)
        return button


    def _debug_text(self, selection : ProjectSelection):
        dbg = []
        if selection.MultipleSelected():
            dbg.append("multiple")
        if selection.MultipleSelected() and selection.IsContiguous():
            dbg.append("sequential")
        if selection.MultipleSelected() and selection.AllLinesInSameBatch():
            dbg.append("in the same batch")
        if selection.AnyBatches() and selection.AllTranslated():
            dbg.append("all translated")
        return f" ({' '.join(dbg)})" if dbg else None

    def _on_translate_selection(self):
        if self.selection:
            self.action_handler.TranslateSelection(self.selection)

    def _on_merge_selection(self):
        if self.selection:
            self.action_handler.MergeSelection(self.selection)

            # HACK: the selection should be updated automatically when lines are merged, but it doesn't work correctly
            self.resetSelection.emit()

    def _on_delete_lines(self):
        if self.selection and self.selection.AnyLines():
            self.action_handler.DeleteSelection(self.selection)

            # HACK: the selection should be updated automatically when lines are deleted, but it doesn't work correctly
            self.resetSelection.emit()

    def _on_split_batch(self):
        if self.selection and self.selection.AnyLines() and not self.selection.MultipleSelected():
            self.action_handler.SplitBatch(self.selection)

    def _on_split_scene(self):
        if self.selection and self.selection.AnyBatches() and not self.selection.MultipleSelected():
            self.action_handler.SplitScene(self.selection)

    def _on_auto_split_batch(self):
        if self.selection and self.selection.AnyBatches() and self.selection.OnlyBatches() and not self.selection.MultipleSelected():
            self.action_handler.AutoSplitBatch(self.selection)

    def _on_reparse(self):
        if self.selection and self.selection.AnyBatches() and self.selection.AllTranslated():
            self.action_handler.ReparseSelection(self.selection)

    def _on_swap_text(self):
        if self.selection:
            self.action_handler._swap_text_and_translation(self.selection)



from qtpy import QtWidgets, QtCore

import puzzlepiece as pzp


class DataGrid(QtWidgets.QWidget):
    #: A Qt signal emitted when a row is added or removed.
    rows_changed = QtCore.Signal()
    #: A Qt signal emitted when any data in the DataGrid changes (including when rows are added/removed).
    data_changed = QtCore.Signal()

    def __init__(self, row_class, puzzle=None):
        super().__init__()
        self.puzzle = puzzle or pzp.puzzle.PretendPuzzle()
        self._row_class = row_class
        row_example = row_class(self.puzzle)
        self.param_names = row_example.params.keys()

        self._tree = QtWidgets.QTreeWidget()
        self._tree.setHeaderLabels(("ID", *row_example.params.keys(), "actions"))

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self._tree)
        self.setLayout(layout)

        self.rows = []
        self._items = []
        self._root = self._tree.invisibleRootItem()
        self._slots = {}
        self.rows_changed.connect(self.data_changed.emit)

    def add_row(self, **kwargs):
        item = QtWidgets.QTreeWidgetItem(self._tree, (str(len(self.rows)),))
        row = self._row_class(self, self.puzzle)
        row._populate_item(self._tree, item)
        self.rows.append(row)
        self._items.append(item)
        for key in kwargs:
            row.params[key].set_value(kwargs[key])
        for param_name in self.param_names:
            if param_name in self._slots:
                for slot in self._slots[param_name]:
                    row.params[param_name].changed.connect(slot)
            row.params[param_name].changed.connect(self.data_changed.emit)
        self.rows_changed.emit()
        return row

    def remove_row(self, id):
        self._root.removeChild(self._items[id])
        del self._items[id]
        del self.rows[id]
        for i in range(len(self.rows)):
            self._items[i].setText(0, str(i))
        self.rows_changed.emit()

    def get_index(self, row):
        return self.rows.index(row)

    def clear(self):
        self._tree.clear()
        self.rows = []
        self._items = []
        self.rows_changed.emit()

    def add_changed_slot(self, param_name, function):
        if param_name in self._slots:
            self._slots[param_name].append(function)
        else:
            self._slots[param_name] = [function]
        for row in self.rows:
            row.params[param_name].changed.connect(function)


class Row:
    def __init__(self, parent=None, puzzle=None):
        self.puzzle = puzzle or pzp.puzzle.PretendPuzzle()
        self.parent = parent
        self.params = {}
        self.actions = {}
        self.define_params()
        self.define_actions()
        for key in self.params:
            self.params[key]._main_layout.removeWidget(self.params[key].label)

    def define_params(self):
        pass

    def define_actions(self):
        pass

    def elevate(self):
        pass

    def _populate_item(self, tree, item):
        for i, key in enumerate(self.params):
            tree.setItemWidget(item, i + 1, self.params[key])
        tree.setItemWidget(item, i + 2, self._action_buttons())

    def _action_buttons(self):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout()
        widget.setLayout(layout)

        visible_actions = [key for key in self.actions if self.actions[key].visible]
        for i, key in enumerate(visible_actions):
            button = QtWidgets.QPushButton(key)
            button.clicked.connect(lambda x=False, _key=key: self.actions[_key]())
            layout.addWidget(button)
        return widget

    def __iter__(self):
        for key in self.params:
            yield key

    def __getitem__(self, key):
        return self.params[key]

    def __contains__(self, item):
        return item in self.params

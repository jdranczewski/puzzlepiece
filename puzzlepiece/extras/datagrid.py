from qtpy import QtWidgets, QtCore

import puzzlepiece as pzp


class DataGrid(QtWidgets.QWidget):
    """
    A table containing multiple :class:`~puzzlepiece.extras.datagrid.Row` objects, each acting kind of like
    a :class:`~puzzlepiece.piece.Piece` object, in that it has params and actions
    (see :class:`~puzzlepiece.param.BaseParam` and :class:`~puzzlepiece.action.Action`).

    This is a QWidget, co it can be added to your Piece's :func:`~puzzlepiece.piece.Piece.custom_layout`
    or used as a standalone Widget if you know what you're doing.

    **This is not very performant, very large numbers of Rows should be avoided!** Consider using
    Qt's QTableWidget instead.

    :param row_class: The :class:`~puzzlepiece.extras.datagrid.Row` class that will be used to construct Rows.
    :param puzzle: (optional) The parent :class:`~puzzlepiece.puzzle.Puzzle`.
    """

    #: A Qt signal emitted when a row is added or removed.
    rows_changed = QtCore.Signal()
    #: A Qt signal emitted when any data in the DataGrid changes (including when rows are added/removed).
    data_changed = QtCore.Signal()

    def __init__(self, row_class, puzzle=None, parent_piece=None):
        super().__init__()
        #: Reference to the parent :class:`~puzzlepiece.puzzle.Puzzle`.
        self.puzzle = puzzle or pzp.puzzle.PretendPuzzle()
        self.parent_piece = parent_piece
        self._row_class = row_class
        row_example = row_class(self.puzzle)
        self.param_names = row_example.params.keys()

        self._tree = QtWidgets.QTreeWidget()
        if len(row_example.actions.keys()):
            self._tree.setHeaderLabels(("ID", *row_example.params.keys(), "actions"))
        else:
            self._tree.setHeaderLabels(("ID", *row_example.params.keys()))

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self._tree)
        self.setLayout(layout)

        #: A list of Rows.
        self.rows = []
        self._items = []
        self._root = self._tree.invisibleRootItem()
        self._slots = {}
        self.rows_changed.connect(self.data_changed.emit)

    @property
    def values(self):
        """
        The current values for all params in the Rows (this does not invoke their getters).
        """
        return [{key: x[key].value for key in x.params} for x in self.rows]

    def add_row(self, row_class=None, **kwargs):
        """
        Add a Row with default param values.

        :param row_class: row class to use, if not specified uses the one provided
          when the DataGrid was created. The class provided here should have the same
          params and actions as the original one!
        :param kwargs: keyword arguments matching param names can be passed
          to set param values in the new row
        """
        item = QtWidgets.QTreeWidgetItem(self._tree, (str(len(self.rows)),))
        row_class = row_class or self._row_class
        row = row_class(self, self.puzzle)
        row._populate_item(self._tree, item)
        self.rows.append(row)
        self._items.append(item)
        for key in kwargs:
            row.params[key].set_value(kwargs[key])
        for param_name in row.params:
            if param_name in self._slots:
                for slot in self._slots[param_name]:
                    row.params[param_name].changed.connect(slot)
            row.params[param_name].changed.connect(self.data_changed.emit)
        self.rows_changed.emit()
        return row

    def remove_row(self, id):
        """
        Remove the row with the given id.

        :param id: id of the row to remove.
        """
        self._root.removeChild(self._items[id])
        del self._items[id]
        del self.rows[id]
        for i in range(len(self.rows)):
            self._items[i].setText(0, str(i))
        self.rows_changed.emit()

    def select_row(self, id):
        self._tree.setCurrentItem(self._items[id])

    def get_index(self, row):
        """
        Get the current index of a given :class:`~puzzlepiece.extras.datagrid.Row` object.

        :param row: the row object.
        :rtype: int
        """
        return self.rows.index(row)

    def clear(self):
        """
        Remove all rows.
        """
        self._tree.clear()
        self.rows = []
        self._items = []
        self.rows_changed.emit()

    def add_changed_slot(self, param_name, function):
        """
        Connect a Slot (usually a method) to the :attr:`~puzzlepiece.param.BaseParam.changed`
        Signal of the given param in all the rows (including Rows added in the future).

        :param param_name: The name of the param whose changed Signal we're connecting to.
        :param function: any method or other Qt Slot to connect.
        """
        if param_name in self._slots:
            self._slots[param_name].append(function)
        else:
            self._slots[param_name] = [function]
        for row in self.rows:
            row.params[param_name].changed.connect(function)


class Row:
    """
    A Row is a template for a :class:`~puzzlepiece.extras.datagrid.DataGrid` object, holding the data (params)
    and actions that the DataGrid displays.

    It acts kind of like a :class:`~puzzlepiece.piece.Piece` object, in that it has params and actions
    (see :class:`~puzzlepiece.param.BaseParam` and :class:`~puzzlepiece.action.Action`).

    :param parent: (optional) The parent DataGrid.
    :parem puzzle: (optional) The parent Puzzle.
    """

    def __init__(self, parent=None, puzzle=None):
        self.puzzle = puzzle or pzp.puzzle.PretendPuzzle()
        self.parent = parent
        #: dict: A dictionary of this Row's params (see :class:`~puzzlepiece.param.BaseParam`). You can also directly index the Row object with the param name.
        self.params = {}
        #: dict: A dictionary of this Row's actions (see :class:`~puzzlepiece.action.Action`).
        self.actions = {}
        self.define_params()
        self.define_actions()
        for key in self.params:
            self.params[key]._main_layout.removeWidget(self.params[key].label)

    def define_params(self):
        """
        Override to define params using decorators from :mod:`puzzlepiece.param`.
        """
        pass

    def define_actions(self):
        """
        Override to define actions using decorators from :mod:`puzzlepiece.action`.
        """
        pass

    def open_popup(self, popup, name=None):
        """
        Open a popup window for this Row.
        See :func:`puzzlepiece.piece.Piece.open_popup`.

        :param popup: a :class:`puzzlepiece.piece.Popup` _class_ to instantiate
        :param name: text to show as the window title
        :rtype: puzzlepiece.piece.Popup
        """
        # Instantiate the popup
        if isinstance(popup, type):
            popup = popup(self, self.puzzle)
        popup.setStyleSheet("QGroupBox {border:0;}")

        # Make a dialog window for the popup to live in
        dialog = pzp.piece._QDialog(self.parent, popup)
        layout = QtWidgets.QVBoxLayout()
        dialog.setLayout(layout)
        layout.addWidget(popup)
        dialog.setWindowTitle(name or "Popup")

        # Display the dialog
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()
        self.puzzle._close_popups.connect(dialog.accept)

        return popup

    def elevate(self):
        """
        For compatibility with the Piece's API.

        :meta private:
        """
        pass

    def _populate_item(self, tree, item):
        visible_params = [x for x in self.params if self.params[x].visible]
        for i, key in enumerate(visible_params):
            tree.setItemWidget(item, i + 1, self.params[key])
        if len(self.actions.keys()):
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

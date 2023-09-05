from pyqtgraph.Qt import QtWidgets, QtCore
from . import parse
import sys

class PieceDict:
    """
    A dictionary wrapper that enforces single-use of keys, and raises a more useful error when
    a Piece tries to use another Piece that hasn't been registered.
    """
    def __init__(self):
        self._dict = {}

    def __setitem__(self, key, value):
        if key in self._dict:
            raise KeyError("A Piece with id '{}' already exists".format(key))
        self._dict[key] = value

    def __iter__(self):
        for key in self._dict:
            yield key
    
    def __getitem__(self, key):
        if key not in self._dict:
            raise KeyError("A Piece with id '{}' is required, but doesn't exist".format(key))
        return self._dict[key]
    
    def __contains__(self, item):
        return item in self._dict
    
    def keys(self):
        return self._dict.keys()
    
    def __repr__(self):
        return "PieceDict({})".format(", ".join(self._dict.keys()))

class Puzzle(QtWidgets.QWidget):
    """
    A container for :class:`puzzlepiece.piece.Piece` objects, meant to be the main QWidget (window)
    of an automation application. It keeps track of the :class:`~puzzlepiece.piece.Piece` objects
    it contains and lets them communicate.

    :param app: A QtApp created to contain this QWidget.
    :param name: A name for the window.
    :param debug: Sets the Puzzle.debug property, if True the app should launch in debug mode and Pieces
        shouldn't communicate with hardware.
    :type debug: bool 
    """
    def __init__(self, app, name, debug=True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pieces can handle the debug flag as they wish
        self._debug = debug
        self.app = app
        self.setWindowTitle(name)
        self._pieces = PieceDict()
        # toplevel is used to send keypresses down the QWidget tree,
        # instead of up (which is how they normally propagate).
        # The list stores all the direct children of this QWidget
        self._toplevel = []

        self.wrapper_layout = QtWidgets.QGridLayout()
        self.setLayout(self.wrapper_layout)

        self.layout = QtWidgets.QGridLayout()
        self.wrapper_layout.addLayout(self.layout, 0, 0)

        self.wrapper_layout.addLayout(self._button_layout(), 1, 0)

        sys.excepthook = self._excepthook

    @property
    def pieces(self):
        """
        A :class:`~puzzlepiece.puzzle.PieceDict`, effectively a dictionary of
        :class:`~puzzlepiece.piece.Piece` objects. Can be used to access Pieces from within other Pieces.
        """
        return self._pieces
    
    @property
    def debug(self):
        """
        A `bool` flag. Pieces should act in debug mode if `True`.
        """
        return self._debug

    # Adding elements

    def add_piece(self, name, piece, row, column, rowspan=1, colspan=1):
        """
        Adds a :class:`~puzzlepiece.piece.Piece` to the grid layout, and registers it with the Puzzle.

        :param name: Identifying string for the Piece.
        :param piece: A :class:`~puzzlepiece.piece.Piece` object.
        :param row: Row index for the grid layout.
        :param column: Column index for the grid layout.
        :param rowspan: Height in rows.
        :param column: Width in columns.
        """
        self.layout.addWidget(piece, row, column, rowspan, colspan)
        self._toplevel.append(piece)
        self.register_piece(name, piece)
    
    def add_folder(self, row, column, rowspan=1, colspan=1):
        """
        Adds a tabbed :class:`~puzzlepiece.puzzle.Folder` to the grid layout, and returns it.

        :param row: Row index for the grid layout.
        :param column: Column index for the grid layout.
        :param rowspan: Height in rows.
        :param column: Width in columns.

        :rtype: puzzlepiece.puzzle.Folder
        """
        folder = Folder(self)
        self.layout.addWidget(folder, row, column, rowspan, colspan)
        self._toplevel.append(folder)
        return folder

    def register_piece(self, name, piece):
        """
        Registers a :class:`~puzzlepiece.piece.Piece` object with the Puzzle.
        This is done by default when a :class:`~puzzlepiece.piece.Piece` is added with
        :func:`~puzzlepiece.puzzle.Puzzle.add_piece`, :func:`puzzlepiece.puzzle.Folder.add_piece`,
        or :func:`puzzlepiece.puzzle.Grid.add_piece`, so this method should rarely be called manually.
        """
        self.pieces[name] = piece
        piece.setTitle(name)

    # Other methods

    def process_events(self):
        """
        Forces the QApplication to process events that happened while a callback was executing.
        Can for example update plots while a long process is running, or run any keyboard
        shortcuts pressed while proecessing.
        """
        self.app.processEvents()

    def _excepthook(self, exctype, value, traceback):
        sys.__excepthook__(exctype, value, traceback)

        self.custom_excepthook(exctype, value, traceback)

        box = QtWidgets.QMessageBox()
        box.setText(str(value)+"\n\nCheck console for details.")
        box.exec()

    def custom_excepthook(self, exctype, value, traceback):
        """
        Override or replace this method to call a custom handler whenever an exception is raised.
        This will run after the defatult exception handler (``sys.__excepthook__``), but before a
        GUI alert is displayed.
        """
        pass

    # Convenience methods
    
    def _docs(self):
        dialog = QtWidgets.QDialog(self)
        layout = QtWidgets.QVBoxLayout()
        tree = QtWidgets.QTreeWidget()
        tree.setHeaderLabels(('pieces', 'get?', 'set?'))

        def copy_item(item):
            if hasattr(item, 'puzzlepiece_descriptor'):
                self.app.clipboard().setText(item.puzzlepiece_descriptor)
        tree.itemDoubleClicked.connect(copy_item)

        for piece_name in self.pieces:
            piece_item = QtWidgets.QTreeWidgetItem(tree, (piece_name,))

            # First, params
            tree_item = QtWidgets.QTreeWidgetItem(piece_item, ('params',))
            for param_name in self.pieces[piece_name].params:
                param = self.pieces[piece_name].params[param_name]
                G = '⟳' if param._getter is not None else ''
                S = '✓' if param._setter is not None else ''
                param_item = QtWidgets.QTreeWidgetItem(tree_item, (param_name, G, S))
                param_item.puzzlepiece_descriptor = "{}:{}".format(piece_name, param_name)

            # Then, actions
            tree_item = QtWidgets.QTreeWidgetItem(piece_item, ('actions',))
            for action_name in self.pieces[piece_name].actions:
                action = self.pieces[piece_name].actions[action_name]
                action_item = QtWidgets.QTreeWidgetItem(tree_item, (action_name, ))
                action_item.puzzlepiece_descriptor = "{}:{}".format(piece_name, action_name)

                button = QtWidgets.QToolButton()
                icon = self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaPlay)
                button.setIcon(icon)
                button.clicked.connect(lambda x=False, action=action: action())
                tree.setItemWidget(action_item, 1, button)

        for i in range(0, 3):
            tree.header().setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

        label = QtWidgets.QLabel()
        label.setText("Double-click on any row to copy the param/action identifier for use in scripts.")
        label.setWordWrap(True)
        
        layout.addWidget(tree)
        layout.addWidget(label)

        dialog.setLayout(layout)
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    def _export_setup(self):
        dialog = QtWidgets.QDialog(self)
        layout = QtWidgets.QVBoxLayout()

        label = QtWidgets.QLabel()
        label.setText("The script below sets all currently params that don't have setters or getters to the current values.")
        label.setWordWrap(True)
        layout.addWidget(label)

        text = ""
        for piece_name in self.pieces:
            keys = self.pieces[piece_name].params
            for key in keys:
                param = self.pieces[piece_name].params[key]
                if param.visible and param._setter is None and param._getter is None:
                    text += "set:{}:{}:{}\n".format(piece_name, key, param.get_value())

        text_box = QtWidgets.QPlainTextEdit()
        text_box.setPlainText(text)
        layout.addWidget(text_box)

        button = QtWidgets.QPushButton("Save")
        def __save_export():
            fname = str(QtWidgets.QFileDialog.getSaveFileName(self, "Save file...")[0])
            with open(fname, 'w') as f:
                f.write(text_box.toPlainText())
        button.clicked.connect(__save_export)
        layout.addWidget(button)

        dialog.setLayout(layout)
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    def _call_stop(self):
        for piece_name in self.pieces:
            self.pieces[piece_name].call_stop()

    def _button_layout(self):
        layout = QtWidgets.QHBoxLayout()

        for function, icon, text in zip(
            (self._docs, self._export_setup, self._call_stop),
            (
                QtWidgets.QStyle.StandardPixmap.SP_MessageBoxInformation,
                QtWidgets.QStyle.StandardPixmap.SP_DialogSaveButton,
                QtWidgets.QStyle.StandardPixmap.SP_BrowserStop
            ),
            (
                "Tree (F1)",
                "Export (F2)",
                "STOP (F3)"
            )
        ):
            button = QtWidgets.QPushButton(text)
            icon = self.style().standardIcon(icon)
            button.setIcon(icon)
            button.clicked.connect(lambda x=False, action=function: action())
            layout.addWidget(button)

        return layout

    def __getitem__(self, name):
        return self.pieces[name]
    
    def _ipython_key_completions_(self):
        return self.pieces.keys()
    
    def run(self, text):
        """
        Execute script commands for this Puzzle as described in :func:`puzzlepiece.parse.run`.
        """
        parse.run(text, self)

    # Qt overrides
        
    def keyPressEvent(self, event):
        """
        Pass down keypress events to child Pieces and Folders.
        Overwrites a QT method.

        :meta private:
        """
        if event.key() == QtCore.Qt.Key.Key_F1:
            self._docs()
        elif event.key() == QtCore.Qt.Key.Key_F2:
            self._export_setup()
        elif event.key() == QtCore.Qt.Key.Key_F3:
            self._call_stop()
        for widget in self._toplevel:
            widget.handle_shortcut(event)

    def closeEvent(self, event):
        """
        Tell the Pieces the window is closing, so they can for example disconnect hardware.
        Overwrites a QT method.

        :meta private:
        """
        for piece_name in self.pieces:
            self.pieces[piece_name].handle_close(event)
        super().closeEvent(event)


class Folder(QtWidgets.QTabWidget):
    """
    A tabbed group of :class:`~puzzlepiece.puzzle.Piece` or :class:`~puzzlepiece.puzzle.Grid`
    objects within the :class:`~puzzlepiece.puzzle.Puzzle`.

    Best created with :func:`puzzlepiece.puzzle.Puzzle.add_folder`.
    """
    def __init__(self, puzzle, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.puzzle = puzzle
        self.pieces = []

    def add_piece(self, name, piece):
        """
        Adds a :class:`~puzzlepiece.piece.Piece` as a tab to this Folder, and registers it with the
        parent :class:`~puzzlepiece.puzzle.Puzzle`.

        :param name: Identifying string for the Piece.
        :param piece: A :class:`~puzzlepiece.piece.Piece` object.
        """

        self.addTab(piece, name)
        self.pieces.append(piece)
        self.puzzle.register_piece(name, piece)
        piece.folder = self

        # No title or border displayed when Piece in Folder
        piece.setTitle(None)
        piece.setStyleSheet("QGroupBox {border:0;}")

    def add_grid(self, name):
        """
        Adds a :class:`~puzzlepiece.puzzle.Grid` as a tab to this Folder.

        :param name: Identifying string for the :class:`~puzzlepiece.puzzle.Grid`.
        :rtype: puzzlepiece.puzzle.Grid
        """

        grid = Grid(self.puzzle)

        self.addTab(grid, name)
        self.pieces.append(grid)
        grid.folder = self

        return grid

    def handle_shortcut(self, event):
        """
        Pass down keypress events only to the **active** child :class:`~puzzlepiece.piece.Piece` or
        :class:`~puzzlepiece.puzzle.Grid`.

        :meta private:
        """
        self.currentWidget().handle_shortcut(event)


class Grid(QtWidgets.QWidget):
    """
    A grid layout for :class:`~puzzlepiece.piece.Piece` objects. For when you need multiple Pieces
    within a single :class:`~puzzlepiece.puzzle.Folder` tab.
    
    Best created with :func:`puzzlepiece.puzzle.Puzzle.add_folder`.
    """
    def __init__(self, puzzle, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.puzzle = puzzle
        self.pieces = []
        self.layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)

    def add_piece(self, name, piece, row, column, rowspan=1, colspan=1):
        """
        Adds a :class:`~puzzlepiece.piece.Piece` to the grid layout, and registers it with the parent
        :class:`~puzzlepiece.puzzle.Puzzle`.

        :param name: Identifying string for the Piece.
        :param piece: A :class:`~puzzlepiece.piece.Piece` object.
        :param row: Row index for the grid layout.
        :param column: Column index for the grid layout.
        :param rowspan: Height in rows.
        :param column: Width in columns.
        """
        self.layout.addWidget(piece, row, column, rowspan, colspan)
        self.pieces.append(piece)
        self.puzzle.register_piece(name, piece)
        piece.folder = self

    def handle_shortcut(self, event):
        """
        Pass down keypress events to child Pieces.

        :meta private:
        """
        for widget in self.pieces:
            widget.handle_shortcut(event)

    def setCurrentWidget(self, piece):
        """
        Passes the `setCurrentWidget` to this Grid's Folder, allowing Pieces within this Grid
        to correctly call :func:`puzzlepiece.piece.Piece.elevate`.

        :meta private:
        """
        if self.folder is not None:
            self.folder.setCurrentWidget(self)

        
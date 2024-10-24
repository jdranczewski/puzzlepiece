from . import parse

from pyqtgraph.Qt import QtWidgets, QtCore
import sys


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
    :param bottom_buttons: Whether the bottom buttons of the Puzzle (Tree, Export, STOP) should be shown.
    :type bottom_buttons: bool
    """

    def __init__(
        self, app=None, name="Puzzle", debug=True, bottom_buttons=True, *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        # Pieces can handle the debug flag as they wish
        self._debug = debug
        self.app = app or QtWidgets.QApplication.instance()
        self.setWindowTitle(name)
        self._pieces = PieceDict()
        self._globals = Globals()
        # toplevel is used to send keypresses down the QWidget tree,
        # instead of up (which is how they normally propagate).
        # The list stores all the direct children of this QWidget
        self._toplevel = []
        self._threadpool = QtCore.QThreadPool()

        self.wrapper_layout = QtWidgets.QGridLayout()
        self.setLayout(self.wrapper_layout)

        self.layout = QtWidgets.QGridLayout()
        self.wrapper_layout.addLayout(self.layout, 0, 0)

        if bottom_buttons:
            self.wrapper_layout.addLayout(self._button_layout(), 1, 0)

        try:
            # If this doesn't raise a NameError, we're in IPython
            shell = get_ipython()
            # _orig_sys_module_state stores the original IPKernelApp excepthook,
            # irrespective of possible modifications in other cells
            self._old_excepthook = shell._orig_sys_module_state["excepthook"]

            # The following hack allows us to handle exceptions through the Puzzle in IPython.
            # Normally when a cell is executed in an IPython InteractiveShell,
            # sys.excepthook is overwritten with shell.excepthook, and then restored
            # to sys.excepthook after the cell run finishes. Any changes we make to
            # sys.excepthook in here directly will thus be overwritten as soon as the
            # cell that defines the Puzzle finishes running.

            # Instead, we schedule set_excepthook on a QTimer, meaning that it will
            # execute in the Qt loop rather than in a cell, so it can modify
            # sys.excepthook without risk of the changes being immediately overwritten,

            # For bonus points, we could set _old_excepthook to shell.excepthook,
            # which would result in all tracebacks appearing in the Notebook rather
            # than the console, but I think that is not desireable.
            def set_excepthook():
                # Make sure we're out of the cell execution context
                if (
                    set_excepthook.counter < 100
                    and sys.excepthook is not self._old_excepthook
                ):
                    # if not, we wait a little bit more
                    set_excepthook.counter += 1
                    QtCore.QTimer.singleShot(500, set_excepthook)
                else:
                    sys.excepthook = self._excepthook

            set_excepthook.counter = 0

            QtCore.QTimer.singleShot(0, set_excepthook)
        except NameError:
            # In normal Python (not IPython) this is comparatively easy.
            # We use the original system hook here instead of sys.excepthook
            # to avoid unexpected behaviour if multiple things try to override
            # the hook in various ways.
            # If you need to implement custom exception handling, please assign
            # a value to your Puzzle's ``custom_excepthook`` method.
            self._old_excepthook = sys.__excepthook__
            sys.excepthook = self._excepthook

    @property
    def pieces(self):
        """
        A :class:`~puzzlepiece.puzzle.PieceDict`, effectively a dictionary of
        :class:`~puzzlepiece.piece.Piece` objects. Can be used to access Pieces from within other Pieces.

        You can also directly index the Puzzle object with the :class:`~puzzlepiece.piece.Piece` name,
        or even with a :class:`~puzzlepiece.piece.Piece` and a :class:`~puzzlepiece.param.BaseParam`::

            # These two are equivalent
            puzzle.pieces["piece_name"]
            puzzle["piece_name"]

            # These three are equivalent
            puzzle.pieces["piece_name"].params["piece_name"]
            puzzle["piece_name"]["param_name"]
            puzzle["piece_name:param_name"]

        The valid keys for indexing a Puzzle object are available when autocompleting the key in IPython.
        """
        return self._pieces

    @property
    def globals(self):
        """
        A dictionary, can be used for API modules that need to be shared by multiple Pieces.
        """
        return self._globals

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
        :param piece: A :class:`~puzzlepiece.piece.Piece` object or a class defining one (which will
          be automatically instantiated).
        :param row: Row index for the grid layout.
        :param column: Column index for the grid layout.
        :param rowspan: Height in rows.
        :param column: Width in columns.
        :rtype: puzzlepiece.piece.Piece
        """
        if isinstance(piece, type):
            piece = piece(self)
        self.layout.addWidget(piece, row, column, rowspan, colspan)
        self._toplevel.append(piece)
        self.register_piece(name, piece)

        return piece

    def replace_piece(self, name, new_piece):
        """
        Replace a named :class:`~puzzlepiece.piece.Piece` with a new one. Can be
        combined with ``importlib.reload`` to do live development on Pieces.

        This method is **experimental** and can sometimes fail. It's useful for development,
        but shouldn't really be used in production applications.

        :param name: Name of the Piece to be replaced.
        :param piece: A :class:`~puzzlepiece.piece.Piece` object or a class defining one (which will
          be automatically instantiated).
        """
        old_piece = self.pieces[name]
        if isinstance(new_piece, type):
            new_piece = new_piece(self)

        if old_piece in self._toplevel:
            self.layout.replaceWidget(
                old_piece,
                new_piece,
                options=QtCore.Qt.FindChildOption.FindDirectChildrenOnly,
            )
            new_piece.setTitle(name)
            self._toplevel.remove(old_piece)
            self._toplevel.append(new_piece)
        else:
            for widget in self._toplevel:
                if isinstance(widget, Folder):
                    widget._replace_piece(name, old_piece, new_piece)

        self._pieces._replace_item(name, new_piece)
        old_piece.handle_close(None)
        # old_piece.deleteLater()
        old_piece.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose, True)
        old_piece.close()

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

    _shutdown_threads = QtCore.Signal()

    def run_worker(self, worker):
        """
        Add a Worker to the Puzzle's Threadpool and runs it. See :class:`puzzlepiece.threads`
        for more details on how to set up a Worker.
        """
        if hasattr(worker, "stop"):
            # This signal is emitted when the application is shutting down,
            # so we're telling the LiveWorker to stop
            self._shutdown_threads.connect(worker.stop)
        self._threadpool.start(worker)

    def _excepthook(self, exctype, value, traceback):
        self._old_excepthook(exctype, value, traceback)

        # Stop any threads that may be running
        self._shutdown_threads.emit()

        # Only do custom exception handling in the main thread, otherwise the messagebox
        # or other such things are likely to break things.
        if QtCore.QThread.currentThread() == self.app.thread():
            self.custom_excepthook(exctype, value, traceback)

            box = QtWidgets.QMessageBox()
            box.setText(str(value) + "\n\nCheck console for details.")
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
        tree.setHeaderLabels(("pieces", "get?", "set?"))

        def copy_item(item):
            if hasattr(item, "puzzlepiece_descriptor"):
                self.app.clipboard().setText(item.puzzlepiece_descriptor)

        tree.itemDoubleClicked.connect(copy_item)

        for piece_name in self.pieces:
            piece_item = QtWidgets.QTreeWidgetItem(tree, (piece_name,))

            # First, params
            tree_item = QtWidgets.QTreeWidgetItem(piece_item, ("params",))
            for param_name in self.pieces[piece_name].params:
                param = self.pieces[piece_name].params[param_name]
                G = "⟳" if param._getter is not None else ""
                S = "✓" if param._setter is not None else ""
                param_item = QtWidgets.QTreeWidgetItem(tree_item, (param_name, G, S))
                param_item.puzzlepiece_descriptor = "{}:{}".format(
                    piece_name, param_name
                )

            # Then, actions
            tree_item = QtWidgets.QTreeWidgetItem(piece_item, ("actions",))
            for action_name in self.pieces[piece_name].actions:
                action = self.pieces[piece_name].actions[action_name]
                action_item = QtWidgets.QTreeWidgetItem(tree_item, (action_name,))
                action_item.puzzlepiece_descriptor = "{}:{}".format(
                    piece_name, action_name
                )

                button = QtWidgets.QToolButton()
                icon = self.style().standardIcon(
                    QtWidgets.QStyle.StandardPixmap.SP_MediaPlay
                )
                button.setIcon(icon)
                button.clicked.connect(lambda x=False, action=action: action())
                tree.setItemWidget(action_item, 1, button)

        for i in range(0, 3):
            tree.header().setSectionResizeMode(
                i, QtWidgets.QHeaderView.ResizeMode.ResizeToContents
            )

        label = QtWidgets.QLabel()
        label.setText(
            "Double-click on any row to copy the param/action identifier for use in scripts."
        )
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
        label.setText(
            "The script below sets all currently params that don't have setters or getters to the current values."
        )
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
            with open(fname, "w") as f:
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
        self._shutdown_threads.emit()

    def _button_layout(self):
        layout = QtWidgets.QHBoxLayout()

        for function, icon, text in zip(
            (self._docs, self._export_setup, self._call_stop),
            (
                QtWidgets.QStyle.StandardPixmap.SP_MessageBoxInformation,
                QtWidgets.QStyle.StandardPixmap.SP_DialogSaveButton,
                QtWidgets.QStyle.StandardPixmap.SP_BrowserStop,
            ),
            ("Tree (F1)", "Export (F2)", "STOP (F3)"),
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
        values = list(self.pieces.keys())
        for piece in self.pieces.keys():
            values.extend([f"{piece}:{param}" for param in self.pieces[piece].params])
        return values

    def run(self, text):
        """
        Execute script commands for this Puzzle as described in :func:`puzzlepiece.parse.run`.
        """
        parse.run(text, self)

    def get_values(self, text):
        """
        Get the values from multiple params as a list.

        :param text: A string of comma-separated param strings
          as described in :func:`puzzlepiece.parse.parse_params`.
        :rtype: list
        """
        return [param.get_value() for param in parse.parse_params(text, self)]

    def record_values(self, text, dictionary=None):
        """
        Get the values from multiple params and record them in a dictionary.
        Useful for storing metadata about a measurement.

        :param text: A string of comma-separated param strings
          as described in :func:`puzzlepiece.parse.parse_params`.
        :param dictionary: If provided, this function will write the param names
          and values to this dictionary. Otherwise, a new one is created and returned.
        :rtype: dict
        """
        params = parse.parse_params(text, self)
        names = text.split(", ")

        if dictionary is None:
            dictionary = {}

        for name, param in zip(names, params):
            dictionary[name] = param.get_value()

        return dictionary

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

    _close_popups = QtCore.Signal()

    def closeEvent(self, event):
        """
        Tell the Pieces the window is closing, so they can for example disconnect hardware.
        Overwrites a QT method.

        :meta private:
        """
        self._shutdown_threads.emit()
        self._close_popups.emit()

        if not self.debug:
            for piece_name in self.pieces:
                self.pieces[piece_name].handle_close(event)

        # Reinstate the original excepthook
        sys.excepthook = self._old_excepthook
        super().closeEvent(event)


QApp = QtWidgets.QApplication
"""A QApplication has to be constructed before any Qt objects
(including the Puzzle and the Pieces), so this is a convenient shortcut to
the QApplication class (see https://doc.qt.io/qt-6/qapplication.html).
"""


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
        :param piece: A :class:`~puzzlepiece.piece.Piece` object or a class defining one (which will
          be automatically instantiated).
        :rtype: puzzlepiece.piece.Piece
        """
        if isinstance(piece, type):
            piece = piece(self.puzzle)
        self.addTab(piece, name)
        self.pieces.append(piece)
        self.puzzle.register_piece(name, piece)
        piece.folder = self

        # No title or border displayed when Piece in Folder
        piece.setTitle(None)
        piece.setStyleSheet("QGroupBox {border:0;}")
        # Remove most of the border if the stylesheet fails
        piece.setFlat(True)

        return piece

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

    def _replace_piece(self, name, old_piece, new_piece):
        if old_piece in self.pieces:
            index = self.indexOf(old_piece)
            self.insertTab(index, new_piece, name)
            new_piece.folder = self
            # No title or border displayed when Piece in Folder
            new_piece.setTitle(None)
            new_piece.setStyleSheet("QGroupBox {border:0;}")
            new_piece.setFlat(True)

            self.pieces.remove(old_piece)
            self.pieces.append(new_piece)
        else:
            for widget in self.pieces:
                if isinstance(widget, Grid):
                    widget._replace_piece(name, old_piece, new_piece)


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
        :param piece: A :class:`~puzzlepiece.piece.Piece` object or a class defining one (which will
          be automatically instantiated).
        :param row: Row index for the grid layout.
        :param column: Column index for the grid layout.
        :param rowspan: Height in rows.
        :param column: Width in columns.
        :rtype: puzzlepiece.piece.Piece
        """
        if isinstance(piece, type):
            piece = piece(self.puzzle)
        self.layout.addWidget(piece, row, column, rowspan, colspan)
        self.pieces.append(piece)
        self.puzzle.register_piece(name, piece)
        piece.folder = self

        return piece

    def _replace_piece(self, name, old_piece, new_piece):
        if old_piece in self.pieces:
            self.layout.replaceWidget(old_piece, new_piece)
            new_piece.setTitle(name)
            new_piece.folder = self
            self.pieces.remove(old_piece)
            self.pieces.append(new_piece)

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


class PieceDict:
    """
    A dictionary wrapper that enforces single-use of keys, and raises a more useful error when
    a Piece tries to use another Piece that hasn't been registered.

    It also allows indexing params directly by using this key format: ``[piece_name]:[param_name]``.
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
            try:
                piece, param = key.split(":")
                return self._dict[piece][param]
            except ValueError:
                # key is not in the piece:param format
                pass
            raise KeyError(
                "A Piece with id '{}' is required, but doesn't exist".format(key)
            )
        return self._dict[key]

    def _replace_item(self, key, value):
        self._dict[key] = value

    def __contains__(self, item):
        return item in self._dict

    def keys(self):
        return self._dict.keys()

    def __repr__(self):
        return "PieceDict({})".format(", ".join(self._dict.keys()))


class Globals:
    """
    A dictionary wrapper used for :attr:`puzzlepiece.puzzle.Puzzle.globals`. It behaves like
    a dictionary, allowing :class:`puzzlepiece.piece.Piece` objects to share device APIs
    with each other.

    Additionally, :func:`~puzzlepiece.puzzle.Globals.require` and
    :func:`~puzzlepiece.puzzle.Globals.release` can be used to keep track of the Pieces
    using a given variable, so that the API can be loaded once and then unloaded once
    all the Pieces are done with it.
    """

    def __init__(self):
        self._dict = {}
        self._counts = {}

    def require(self, name):
        """
        Register that a Piece is using the variable with a given name. This will increase
        an internal counter to indicate the Piece having a hold on the variable.

        Returns `False` if this is the first time a variable is being registered (and thus
        setup is needed) or `True` if the variable has been registered already.

        For example, this can be used within :func:`~puzzlepiece.piece.Piece.setup`::

            def setup(self):
                if not self.puzzle.globals.require('sdk'):
                    # Load the SDK if not done already by a different Piece
                    self.puzzle.globals['sdk'] = self.load_sdk()

        :param name: a dictionary key for the required variable
        :rtype: bool
        """
        if name not in self._dict:
            self._dict[name] = None
            self._counts[name] = 1
            return False
        else:
            self._counts[name] += 1
            return True

    def release(self, name):
        """
        Indicate that a Piece is done using the variable with a given name.
        This will decrease an internal counter to indicate the Piece is releasing
        its hold on the variable.

        Returns `False` if the counter is non-zero (so different Pieces are still using
        this variable) or `True` if all Pieces are done with the variable (in that case
        the SDK can be safely shut down for example).

        For example, this can be used within :func:`~puzzlepiece.piece.Piece.handle_close`::

            def handle_close(self):
                if self.puzzle.globals.release('sdk'):
                    # Unload the SDK if all Pieces are done with it
                    self.puzzle.globals['sdk'].stop()

        :param name: a dictionary key for the variable being released
        :rtype: bool
        """
        if name not in self._dict:
            raise KeyError(f"No global variable with id '{name}' to release")
        if name not in self._counts:
            raise KeyError(
                f"Cannot release '{name}' since it hasn't been registered with 'require'"
            )
        self._counts[name] -= 1
        return self._counts[name] < 1

    def __setitem__(self, key, value):
        self._dict[key] = value

    def __getitem__(self, key):
        if key not in self._dict:
            raise KeyError("No global variable with id '{}'".format(key))
        return self._dict[key]

    def __delitem__(self, key):
        del self._dict[key]
        if key in self._counts:
            del self._counts[key]

    def __contains__(self, item):
        return item in self._dict

    def keys(self):
        return self._dict.keys()

    def __repr__(self):
        return "Globals({})".format(", ".join(self._dict.keys()))


class PretendPuzzle:
    """
    A placeholder object used if no :class:`~puzzlepiece.puzzle.Puzzle` is provided
    when creating a :class:`puzzlepiece.puzzle.Piece`. Its `debug` attribute is
    always True.
    """

    debug = True

    def process_events(self):
        """
        Like :func:`puzzlepiece.puzzle.Puzzle.process_events()`.
        """
        QtWidgets.QApplication.instance().processEvents()

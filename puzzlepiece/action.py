from pyqtgraph.Qt import QtCore, QtWidgets
from functools import wraps

class Action(QtCore.QObject):
    """
    An action is a function that a :class:`~puzzlepiece.piece.Piece` object can call.

    It will be given a button in the GUI (if ``visible`` is True), and can be executed from code
    in other Pieces or elsewhere as if it was a method::

        puzzle['piece_name'].actions['action_name']()

    Any arguments provided when calling an action will be passed to the registered function.

    To register an action, use the :func:`~puzzlepiece.action.define` decorator as shown below.

    :param function: The function to call when the action is executed.
    :param parent: The Piece this action belongs to.
    :param shortcut: A keyboard shortcut for this action, works only when the Piece is visible.
    :param visible: Bool flag, whether a button for the action is generated in the GUI.
    """
    #: A Qt signal emitted when the action is executed.
    called = QtCore.Signal()

    def __init__(self, function, parent, shortcut=None, visible=True):
        self.function = function
        self.parent = parent
        #: Keyboard shortcut associated with the param.
        self.shortcut = shortcut
        # See https://doc.qt.io/qt-6/qt.html#Key-enum for acceptable values
        self._visible = visible
        super().__init__()

    def __call__(self, *args, **kwargs):
        # Bring the Piece into view if in a folder
        self.parent.elevate()
        self.function(*args, **kwargs)
        self.called.emit()

    @property
    def visible(self):
        """
        Bool flag, indicates whether this action is visible as a button in the GUI.
        """
        return self._visible

def define(piece, name, shortcut=None, visible=True):
    """
    A decorator generator for registering a :class:`~puzzlepiece.action.Action` in a Piece's
    :func:`~puzzlepiece.piece.Piece.define_action` method with a given function.

    To register an action for a function, do this::

        @puzzlepiece.action.define(self, 'action_name')
        def action(self):
            print("Hello world!")

    :param piece: The :class:`~puzzle.piece.Piece` this param should be registered with. Usually `self`, as this method should
      be called from within :func:`puzzlepiece.piece.Piece.define_actions`
    :param name: a unique (per Piece) name for the action
    :param shortcut: The keyboard shortcut for this action. See https://doc.qt.io/qt-6/qt.html#Key-enum for possible values.
      Example: ``QtCore.Qt.Key.Key_F1``
    :param visible: bool flag, determined if a GUI button will be shown for this param.
    """
    def decorator(action):
        @wraps(action)
        def wrapper(*args, **kwargs):
            return action(piece, *args, **kwargs)
        action_object = Action(wrapper, piece, shortcut, visible)
        piece.actions[name] = action_object
        if shortcut:
            piece.shortcuts[shortcut] = action_object
        return action_object
    return decorator
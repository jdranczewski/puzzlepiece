from qtpy import QtCore
import inspect

from . import _snippets
from . import piece


class Action(QtCore.QObject):
    """
    An action is a function that a :class:`~puzzlepiece.piece.Piece` object can call.

    It will be given a button in the GUI (if ``visible`` is True), and can be executed from code
    in other Pieces or elsewhere as if it was a method::

        puzzle['piece_name'].actions['action_name']()

    Any arguments provided when calling an action will be passed to the registered function.

    To register an action, use the :func:`~puzzlepiece.action.define` decorator as shown below.
    The action will return the values your function returns.

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
        result = self.function(*args, **kwargs)
        self.called.emit()
        return result

    @property
    def visible(self):
        """
        Bool flag, indicates whether this action is visible as a button in the GUI.
        """
        return self._visible

    def make_child_action(self):
        """
        Create and return a child action that calls the same callable.

        See :func:`puzzlepiece.piece.Popup.add_child_actions` for a quick way of adding child
        actions to a popup.
        """
        child = Action(self.function, self.parent, self.shortcut)
        return child


def define(piece, name, shortcut=None, visible=True):
    """
    A decorator generator for registering a :class:`~puzzlepiece.action.Action` in a Piece's
    :func:`~puzzlepiece.piece.Piece.define_actions` method with a given function.

    To register an action for a function, do this::

        @puzzlepiece.action.define(self, 'action_name')
        def action():
            print(f"Hello world from {self}!")

    It's also allowed to provide "self" as the first argument of the action method
    for added clarity, but since self exists locally within :func:`~puzzlepiece.piece.Piece.define_actions`
    this is technically not required::

        @puzzlepiece.action.define(self, 'action_name')
        def action(self):
            print(f"Hello world from {self}!")

    The method you're decorating can take arguments, but all should in general be optional, as invoking
    the action with a GUI button will not provide arguments to it::

        @puzzlepiece.action.define(self, 'Say Hello')
        def say_hello(name="test user"):
            print(f"Hello {name}!")

    This can be invoked as::

        puzzle["piece_name"].actions["Say Hello"]()
        puzzle["piece_name"].actions["Say Hello"]("another user")
        puzzle["piece_name"].actions["Say Hello"](name="another user")

    :param piece: The :class:`~puzzle.piece.Piece` this action should be registered with. Usually `self`, as this method should
      be called from within :func:`puzzlepiece.piece.Piece.define_actions`
    :param name: a unique (per Piece) name for the action
    :param shortcut: The keyboard shortcut for this action. See https://doc.qt.io/qt-6/qt.html#Key-enum for possible values.
      Example: ``QtCore.Qt.Key.Key_F1``
    :param visible: bool flag, determined if a GUI button will be shown for this param.
    """

    def decorator(action):
        if "self" in inspect.signature(action).parameters:

            def wrapper(*args, **kwargs):
                return action(piece, *args, **kwargs)

            # Update the wrapper's function name, so that it shows up in profile traces correctly.
            new_name = f"wrap__{action.__name__}"
            _snippets.update_function_name(wrapper, new_name)
        else:
            wrapper = action

        action_object = Action(wrapper, piece, shortcut, visible)
        piece.actions[name] = action_object
        if shortcut:
            piece.shortcuts[shortcut] = action_object
        return action_object

    return decorator


class _Settings(piece.Popup):
    def define_params(self):
        self.add_invisible_params()

    def define_actions(self):
        self.add_invisible_actions()


def settings(piece, name="Settings", shortcut=None, visible=True):
    """
    Define a "Settings" action in a Piece's :func:`~puzzlepiece.piece.Piece.define_actions` method.
    This action will create a :class:`puzzlepiece.piece.Popup` that includes all of the Piece's
    invisible params and actions. This is equivalent to using :func:`puzzlepiece.piece.Popup.add_invisible_params`
    and :func:`puzzlepiece.piece.Popup.add_invisible_actions` in a custom Popup subclass.

    This is useful when you want to display a couple of important params in the main Piece, but relegate detailed
    settings to a sub-menu::

        def define_actions(self):
            # Add a hidden action
            @pzp.action.define(self, "Hidden")
            def hidden_action():
                print("Surprise!")

            # Add a Settings button
            pzp.action.settings(self)

    :param piece: The :class:`~puzzle.piece.Piece` this action should be registered with. Usually `self`, as this method should
      be called from within :func:`puzzlepiece.piece.Piece.define_actions`
    :param name: a unique (per Piece) name for the action
    :param shortcut: The keyboard shortcut for this action. See https://doc.qt.io/qt-6/qt.html#Key-enum for possible values.
      Example: ``QtCore.Qt.Key.Key_F1``
    :param visible: bool flag, determined if a GUI button will be shown for this param.
    """

    def open_settings():
        piece.open_popup(
            _Settings,
            f"{piece._name} settings" if piece._name is not None else "Settings",
        )

    action_object = Action(open_settings, piece, shortcut, visible)
    piece.actions[name] = action_object
    if shortcut:
        piece.shortcuts[shortcut] = action_object
    return action_object

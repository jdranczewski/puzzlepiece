from pyqtgraph.Qt import QtWidgets
from functools import wraps
import math

from .puzzle import PretendPuzzle


class Piece(QtWidgets.QGroupBox):
    """
    A single `Piece` object is an unit of automation - an object that is meant to represent a single
    physical instrument (like a laser) or a particular functionality (like a plotter or a parameter scan).

    Pieces can be assembled into a :class:`~puzzlepiece.puzzle.Puzzle` using the Puzzle's
    :func:`~puzzlepiece.puzzle.Puzzle.add_piece` method.

    :param puzzle: The parent :class:`~puzzlepiece.puzzle.Puzzle`.
    :param custom_horizontal: A bool, the custom layout is displayed to the right of the main controls
                              if True.
    """

    def __init__(self, puzzle=None, custom_horizontal=False, *args, **kwargs):
        super().__init__()
        #: Reference to the parent :class:`~puzzlepiece.puzzle.Puzzle`.
        self.puzzle = puzzle or PretendPuzzle()
        #: Boolean flag. See :func:`~puzzlepiece.piece.Piece.call_stop`
        self.stop = False

        #: dict: A dictionary of this Piece's params (see :class:`~puzzlepiece.param.BaseParam`). You can also directly index the Piece object with the param name.
        self.params = {}
        # A reference to the param dictionary for backwards-compatibility
        self.readouts = self.params
        #: dict: A dictionary of this Piece's actions (see :class:`~puzzlepiece.action.Action`)
        self.actions = {}
        self.shortcuts = {}

        if not self.puzzle.debug:
            self.setup()

        self.define_params()
        self.define_readouts()
        self.define_actions()
        self.folder = None

        if custom_horizontal:
            self.layout = QtWidgets.QHBoxLayout()
        else:
            self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        control_layout = QtWidgets.QVBoxLayout()
        control_layout.addLayout(self.param_layout())
        control_layout.addLayout(self.action_layout())
        self.layout.addLayout(control_layout)

        custom_layout = self.custom_layout()
        if custom_layout is not None:
            self.layout.addLayout(custom_layout)

        if custom_layout is None or custom_horizontal:
            control_layout.addStretch()

    def param_layout(self, wrap=1):
        """
        Genereates a `QGridLayout` for the params. Override to set a different wrapping.

        :param wrap: the number of columns the params are displayed in .
        :rtype: QtWidgets.QGridLayout
        """
        layout = QtWidgets.QGridLayout()
        visible_params = [key for key in self.params if self.params[key].visible]
        numrows = math.ceil(len(visible_params) / wrap)
        for i, key in enumerate(visible_params):
            layout.addWidget(self.params[key], i % numrows, i // numrows)
        return layout

    def action_layout(self, wrap=2):
        """
        Genereates a `QGridLayout` for the actions. Override to set a different wrapping.

        :param wrap: the number of columns the actions are displayed in.
        :rtype: QtWidgets.QGridLayout
        """
        layout = QtWidgets.QGridLayout()
        visible_actions = [key for key in self.actions if self.actions[key].visible]
        for i, key in enumerate(visible_actions):
            button = QtWidgets.QPushButton(key)
            button.clicked.connect(lambda x=False, _key=key: self.actions[_key]())
            layout.addWidget(button, i // wrap, i % wrap)
        return layout

    def custom_layout(self):
        """
        Override to generate a custom `QLayout` that this Piece will display.

        :rtype: QtWidgets.QLayout
        """
        return None

    def define_params(self):
        """
        Override to define params using decorators from :mod:`puzzlepiece.param`.
        """
        pass

    def define_readouts(self):
        """
        Mostly deprecated.

        Override to define readouts (params with getters). This is no different that defining them in
        :func:`~puzzlepiece.piece.Piece.define_params`, but may be a convenient way to organise the
        definitions within your custom class.
        """
        pass

    def define_actions(self):
        """
        Override to define actions using decorators from :mod:`puzzlepiece.action`.
        """
        pass

    def setup(self):
        """
        Only called if the :class:`~puzzlepiece.puzzle.Puzzle` debug flag is False.
        Override to set up necessary hardware libraries.
        """
        pass

    def open_popup(self, popup, name=None):
        """
        Open a popup window for this Piece. A popup is a :class:`puzzlepiece.piece.Popup`
        object, which is like a Piece but floats in a separate window attached to the main
        :class:`~puzzlepiece.puzzle.Puzzle`. This can be used for handling additional tasks
        that you don't want to clutter the main Piece. See :class:`puzzlepiece.piece.Popup`
        for details on implementing a Popup.

        :param popup: a :class:`puzzlepiece.piece.Popup` _class_ to instantiate
        :param name: text to show as the window title
        :rtype: puzzlepiece.piece.Popup
        """
        # Instantiate the popup
        if isinstance(popup, type):
            popup = popup(self, self.puzzle)
        popup.setStyleSheet("QGroupBox {border:0;}")

        # Make a dialog window for the popup to live in
        dialog = _QDialog(self, popup)
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

    def call_stop(self):
        """
        This method is called by the parent Puzzle when a global stop is called.

        By default, it sets the stop flag to True. Detect the flag in you code to stop processes.

        Alternatively, this can be overriden to support more complex actions.
        """
        self.stop = True

    def handle_close(self, event):
        """
        Only called if the :class:`~puzzlepiece.puzzle.Puzzle` :attr:`~puzzlepiece.puzzle.Puzzle.debug`
        flag is False. Override to disconnect hardware etc when the main window closes.
        """
        pass

    def handle_shortcut(self, event):
        """
        Calls an Action if a keyboard shortcut has been registered.

        :meta private:
        """
        if event.key() in self.shortcuts:
            self.shortcuts[event.key()]()

    def elevate(self):
        """
        If this Piece resides in a :class:`~puzzlepiece.puzzle.Folder`, this method switches the tab
        to make this Piece visible.
        """
        if self.folder is not None:
            self.folder.setCurrentWidget(self)

    def __getitem__(self, name):
        return self.params[name]

    def _ipython_key_completions_(self):
        return self.params.keys()


def ensurer(ensure_function):
    """
    An ensurer is a decorator that can be placed on getters, setters, and actions, and it will run
    ahead of these functions. The intended behaviour is performing checks ahead of running the
    function - for example checking if a laser is connected ahead of trying to set its power.
    This way one ensurer can be written and used in multiple places easily.

    Note that **the method being decorated should raise an exception if the check fails!** This way
    execution will stop if the condition is not met. This is not mandatory though - custom behaviour
    is allowed.

    For example, an ensurer can be defined as a Piece's method (in the main body of the class).::

        @puzzlepiece.piece.ensurer
        def _ensure_connected(self):
            if not self.params['connected'].get_value():
                raise Exception('Laser not connected')

    This can then be used when defining a param (below the param-defining decorator)::

        @puzzlepiece.param.spinbox(self, 'power', 0.)
        @self._ensure_connected
        def power(self, value):
            self.laser.set_power(value)

        @puzzlepiece.param.spinbox(self, 'wavelength', 0.)
        @self._ensure_connected
        def wavelength(self, value):
            self.laser.set_wavelength(value)

    It can also be called directly if preferred, optionally with `capture_exception=True`
    which will return True if the check passes, or False if the check raises an Exception::

        # This should raise an Exception is the check fails
        self._ensure_connected()

        # This will not raise an Exception is the check fails
        if self._ensure_connected(capture_exception=True):
            print("laser is connected!")
    """

    # Decorating a class method with ensure makes it a decorator.
    # Here we create this decorator and return it.
    @wraps(ensure_function)
    def ensure_decorator(self, main_function=None, capture_exception=False):
        if main_function is not None:
            # This means ensure_decorator was used as a decorator, and
            # main_function is the function being decorated. We therefore
            # wrap it with the ensuring functionality and return it
            @wraps(main_function)
            def wrapped_main(self, *args, **kwargs):
                ensure_function(self)
                return main_function(self, *args, **kwargs)

            return wrapped_main
        else:
            # If main_function is None, ensure_decorator has been called
            # directly instead of being used as a decorator, so we
            # just execute ensure_function
            if capture_exception:
                try:
                    ensure_function(self)
                except Exception:
                    return False
                return True
            else:
                ensure_function(self)

    return ensure_decorator


class _QDialog(QtWidgets.QDialog):
    """
    A variant of the QDialog specifically for popups, handles closing them
    with a custom function.
    """

    def __init__(self, parent, popup, *args, **kwargs):
        self.popup = popup
        super().__init__(parent, *args, **kwargs)

    def closeEvent(self, event):
        self.popup.handle_close()
        self.popup.parent_piece.puzzle._close_popups.disconnect(self.accept)
        super().closeEvent(event)


class Popup(Piece):
    """
    A Popup is similar to a Piece, but floats in a separate window attached to the main
    :class:`~puzzlepiece.puzzle.Puzzle`. This can be used for handling additional tasks
    that you don't want to clutter the main Piece. For example you can have a camera
    Piece which can open a Popup to set the camera's region of interest with an interactive
    plot window.

    A Popup can be created and displayed by calling :func:`puzzlepiece.piece.Piece.open_popup`.

    A Popup is attached to a specific Piece and knows it through its
    :attr:`~puzzlepiece.piece.Popup.parent_piece` attribute, but it can also access other
    Pieces through the Puzzle, which it knows through its :attr:`~puzzlepiece.piece.Piece.puzzle`
    attribute.

    A Popup can have params, actions, and custom layouts just like a normal Piece, and are created by
    overriding :func:`~puzzlepiece.piece.Piece.define_params`, :func:`~puzzlepiece.piece.Piece.define_actions`,
    and :func:`~puzzlepiece.piece.Piece.custom_layout` like for a Piece.

    :param puzzle: The parent :class:`~puzzlepiece.puzzle.Puzzle`.
    :param parent_piece: The parent :class:`~puzzlepiece.piece.Piece`.
    :param custom_horizontal: A bool, the custom layout is displayed to the right of the main controls
                              if True.
    """

    def __init__(self, parent_piece, puzzle, custom_horizontal=False, *args, **kwargs):
        self._parent_piece = parent_piece
        super().__init__(puzzle, custom_horizontal, *args, **kwargs)
        self.layout.setContentsMargins(0, 0, 0, 0)

    @property
    def parent_piece(self):
        """
        A reference to this Popup's parent :class:`~puzzlepiece.piece.Piece`,
        the one that created it through :func:`puzzlepiece.piece.Piece.open_popup`.
        """
        return self._parent_piece

    def add_child_params(self, param_names):
        """
        Given a list of param names referring to params of the parent :class:`~puzzlepiece.piece.Piece`,
        add corresponding child params to this Popup.

        This lets you quickly make a Settings popup that adjusts the hidden params of a Piece.

        See :func:`puzzlepiece.param.BaseParam.make_child_param` for details.

        :param param_names: List of the parent_piece's param names to make children from.
        """
        for name in param_names:
            self.params[name] = self.parent_piece.params[name].make_child_param()

    def add_child_actions(self, action_names):
        """
        Given a list of action names referring to actions of the parent :class:`~puzzlepiece.piece.Piece`,
        add corresponding child actions to this Popup.

        This lets you surface additional actions in a Popup without cluttering the main Piece.

        See :func:`puzzlepiece.action.Action.make_child_action` for details.

        :param action_names: List of the parent_piece's action names to make children from.
        """
        for name in action_names:
            self.actions[name] = self.parent_piece.actions[name].make_child_action()

    # TODO: A way to close the Popup from 'within'

    def handle_close(self):
        """
        Called when the Popup is closed. Override to perform actions when the user
        closes this Popup - for example delete related plot elements.

        In contrast to :func:`puzzlepiece.piece.Piece.handle_close`, this is called even
        if the :class:`~puzzlepiece.puzzle.Puzzle` :attr:`~puzzlepiece.puzzle.Puzzle.debug`
        flag is True.
        """
        pass

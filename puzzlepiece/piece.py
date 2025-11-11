from pyqtgraph.Qt import QtWidgets, QtCore, QtGui
from functools import wraps
import inspect
import math
import os

from .puzzle import PretendPuzzle
from . import _snippets


class Piece(QtWidgets.QGroupBox):
    """
    A single `Piece` object is an unit of automation - an object that is meant to represent a single
    physical instrument (like a laser) or a particular functionality (like a plotter or a parameter scan).

    Pieces can be assembled into a :class:`~puzzlepiece.puzzle.Puzzle` using the Puzzle's
    :func:`~puzzlepiece.puzzle.Puzzle.add_piece` method.

    Create custom Pieces by inheriting from this class, and overriding
    :func:`~puzzlepiece.piece.Piece.define_params`, :func:`~puzzlepiece.piece.Piece.define_actions`,
    and :func:`~puzzlepiece.piece.Piece.custom_layout`.

    :param puzzle: The parent :class:`~puzzlepiece.puzzle.Puzzle`.
    :param custom_horizontal: Display the custom layout to the right of the main controls.
        (**Deprecated**, use :attr:`~puzzlepiece.piece.Piece.custom_horizontal`).
    :param param_defaults: An optional dictionary of default param values. These will be set
        without calling the corresponding param setters or :attr:`~puzzlepiece.param.BaseParam.changed`
        signals. See also ``param_defaults`` in :func:`puzzlepiece.puzzle.Puzzle.add_piece`,
    """

    def __init__(
        self, puzzle=None, custom_horizontal=None, param_defaults=None, *args, **kwargs
    ):
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
        self._name = None

        if not self.puzzle.debug:
            self.setup()

        self.folder = None
        self.define_params()
        self.define_readouts()
        self.define_actions()
        if param_defaults:
            self._set_param_defaults(param_defaults)

        if custom_horizontal:
            self.custom_horizontal = custom_horizontal
        if self.custom_horizontal:
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

        if custom_layout is None or self.custom_horizontal:
            control_layout.addStretch()

    custom_horizontal = False
    """
    You can specify a couple options when creating your Piece::

        class MyPiece(pzp.Piece):
            # These settings are optional
            custom_horizontal = True # Show your custom layout to the right of the params and actions
            param_wrap = 2 # The number of columns the params are displayed in
            action_wrap = 3 # The number of columns the actions are displayed in
    """
    #: See above (:attr:`~puzzlepiece.piece.Piece.custom_horizontal`).
    param_wrap = 1
    #: See above (:attr:`~puzzlepiece.piece.Piece.custom_horizontal`).
    action_wrap = 2

    def param_layout(self, wrap=None):
        """
        Genereates a `QGridLayout` for the params.

        :meta private:
        :param wrap: the number of columns the params are displayed in. (**Deprecated**,
            use :attr:`~puzzlepiece.piece.Piece.param_wrap`).
        :rtype: QtWidgets.QGridLayout
        """
        layout = QtWidgets.QGridLayout()
        visible_params = [key for key in self.params if self.params[key].visible]
        done = set()
        # Compute how many rows the params should span
        if wrap:
            self.param_wrap = wrap
        numrows = math.ceil(len(visible_params) / self.param_wrap)
        group_offset = 0
        # Iterate over the params and add them to the grid
        for i, key in enumerate(visible_params):
            if key in done:
                # All params in a group are added immediately when the group is
                # first encountered, so we can skip adding them subsequently
                group_offset -= 1
                continue
            if self.params[key]._group:
                # Group found, prepare to add all its params!
                group = self.params[key]._group
                group_widget = QtWidgets.QGroupBox(group)
                group_layout = QtWidgets.QGridLayout()
                group_widget.setLayout(group_layout)
                group_params = [
                    key for key in visible_params if self.params[key]._group == group
                ]
                # Iterate on the found params and add them to the sub-grid
                for j, key in enumerate(group_params):
                    group_layout.addWidget(self.params[key], j, 0)
                    done.add(key)
                layout.addWidget(
                    group_widget,
                    (i + group_offset) % numrows,
                    (i + group_offset) // numrows,
                    len(group_params),
                    1,
                )
                # Compute the offset for the main grid layout
                # How much does this group stick out from the desired number of rows?
                out = len(group_params) + (i + group_offset) % numrows - numrows
                # How many rows does the group take?
                group_offset += len(group_params) - 1
                if out > 0:
                    group_offset -= out
            else:
                # Add the param to the main grid directly if it is not in a group
                layout.addWidget(
                    self.params[key],
                    (i + group_offset) % numrows,
                    (i + group_offset) // numrows,
                )
                done.add(key)
        return layout

    def action_layout(self, wrap=None):
        """
        Genereates a `QGridLayout` for the actions.

        :meta private:
        :param wrap: the number of columns the actions are displayed in. (**Deprecated**,
            use :attr:`~puzzlepiece.piece.Piece.action_wrap`)
        :rtype: QtWidgets.QGridLayout
        """
        layout = QtWidgets.QGridLayout()
        visible_actions = [key for key in self.actions if self.actions[key].visible]
        if wrap:
            self.action_wrap = wrap
        for i, key in enumerate(visible_actions):
            button = QtWidgets.QPushButton(key)
            button.clicked.connect(lambda x=False, _key=key: self.actions[_key]())
            layout.addWidget(button, i // self.action_wrap, i % self.action_wrap)
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
        **Deprecated**.

        Override to define readouts (params with getters). This is no different that defining them in
        :func:`~puzzlepiece.piece.Piece.define_params`, but may be a convenient way to organise the
        definitions within your custom class.

        :meta private:
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

    def open_popup(self, popup, name=None, modal=True):
        """
        Open a popup window for this Piece. A popup is a :class:`puzzlepiece.piece.Popup`
        object, which is like a Piece but floats in a separate window attached to the main
        :class:`~puzzlepiece.puzzle.Puzzle`. This can be used for handling additional tasks
        that you don't want to clutter the main Piece. See :class:`puzzlepiece.piece.Popup`
        for details on implementing a Popup.

        :param popup: a :class:`puzzlepiece.piece.Popup` _class_ to instantiate
        :param name: text to show as the window title
        :param modal: if True, the Popup will be attached to the Puzzle, always appearing with
            it and without a taskbar entry. If False, it will be an independent window that can
            be minimised.
        :rtype: puzzlepiece.piece.Popup
        """
        # Instantiate the popup
        if isinstance(popup, type):
            popup = popup(self, self.puzzle)

        # Make a dialog window for the popup to live in
        dialog = _QDialog(self if modal else None, popup)
        layout = QtWidgets.QVBoxLayout()
        dialog.setLayout(layout)
        layout.addWidget(popup)
        dialog.setWindowTitle(name or "Popup")
        dirname = os.path.dirname(__file__)
        dialog.setWindowIcon(QtGui.QIcon(os.path.join(dirname, "icon.png")))

        # Add buttons to non-modal windows
        if not modal:
            dialog.setWindowFlags(
                dialog.windowFlags()
                | QtCore.Qt.WindowType.WindowMinimizeButtonHint
                | QtCore.Qt.WindowType.WindowMaximizeButtonHint
            )
            # Since the Puzzle is not a parent when the dialog is not modal,
            # we have to add the puzzle's stylesheet to the dialog manually
            if self.puzzle._stylesheet:
                dialog.setStyleSheet(self.puzzle._stylesheet)

        if not hasattr(self, "_popups"):
            self._popups = []
        self._popups.append(dialog)

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

    def handle_close(self, event=None):
        """
        Only called if the :class:`~puzzlepiece.puzzle.Puzzle` :attr:`~puzzlepiece.puzzle.Puzzle.debug`
        flag is False. Override to disconnect hardware etc when the main window closes.

        If there is a param with the name "connected", it will be set to False in this method by
        default (see :func:`puzzlepiece.param.connect` and :func:`puzzlepiece.param.connect` for
        hardware connection handling).
        """
        if "connected" in self.params:
            self["connected"].set_value(False)

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

    def _set_param_defaults(self, param_defaults):
        """
        Set default values for the params, without emitting the changed
        signal or calling the setters.
        """
        for param_name in param_defaults:
            param = self.params[param_name]
            value = param._type(param_defaults[param_name])
            param._input_set_value(value)
            if param._setter is None:
                param._value = value

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
            if "self" in inspect.signature(main_function).parameters:

                def wrapped_main(self, *args, **kwargs):
                    ensure_function(self)
                    return main_function(self, *args, **kwargs)
            else:

                def wrapped_main(self, *args, **kwargs):
                    ensure_function(self)
                    return main_function(*args, **kwargs)

            # Update the wrapper's function name, so that it shows up in profile traces correctly.
            new_name = f"{ensure_function.__name__}__{main_function.__name__}"
            _snippets.update_function_name(wrapped_main, new_name)
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
        if parent is not None:
            super().__init__(parent, *args, **kwargs)
        else:
            super().__init__(*args, **kwargs)
        # Mark the Dialog for deletion once it is closed
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose, True)

    def closeEvent(self, event):
        self.popup.handle_close()
        self.popup.parent_piece.puzzle._close_popups.disconnect(self.accept)
        super().closeEvent(event)

    def keyPressEvent(self, event):
        """
        Pass down keypress events to the Popup and the Puzzle.
        Overwrites a QT method.

        :meta private:
        """
        self.popup.handle_shortcut(event)
        self.popup.parent_piece.puzzle.keyPressEvent(event)


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

    You can access the QDialog the Popup resides in by using its ``parent()`` method (a general method
    that all QWidgets have).

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

    def add_invisible_params(self):
        """
        Add all hidden params from the parent :class:`~puzzlepiece.piece.Piece` to this Popup.
        This lets you quickly make a Settings popup that adjusts the hidden params of a Piece.

        See :func:`puzzlepiece.param.BaseParam.make_child_param` for details, as well as
        :func:`puzzlepiece.action.settings` for a quick way to define a Settings Popup.
        """
        invisible_params = [
            key
            for key in self.parent_piece.params
            if not self.parent_piece.params[key].visible
        ]
        for name in invisible_params:
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

    def add_invisible_actions(self):
        """
        Add all hidden actions from the parent :class:`~puzzlepiece.piece.Piece` to this Popup.
        This lets you quickly make a Settings popup that displays additional actions for a Piece.

        See :func:`puzzlepiece.param.BaseParam.make_child_action` for details, as well as
        :func:`puzzlepiece.action.settings` for a quick way to define a Settings Popup.
        """
        invisible_actions = [
            key
            for key in self.parent_piece.actions
            if not self.parent_piece.actions[key].visible
        ]
        for name in invisible_actions:
            self.actions[name] = self.parent_piece.actions[name].make_child_action()

    def close(self):
        """
        Close the popup.
        """
        self.parent().accept()

    def handle_close(self):
        """
        Called when the Popup is closed. Override to perform actions when the user
        closes this Popup - for example delete related plot elements.

        In contrast to :func:`puzzlepiece.piece.Piece.handle_close`, this is called even
        if the :class:`~puzzlepiece.puzzle.Puzzle` :attr:`~puzzlepiece.puzzle.Puzzle.debug`
        flag is True.
        """
        pass

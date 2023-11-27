from pyqtgraph.Qt import QtWidgets
import math

class Piece(QtWidgets.QGroupBox):
    """
    A single `Piece` object is an unit of automation - an object that is meant to represent a single
    physical instrument (like a laser) or a particular functionality (like a plotter or a parameter scan).

    Pieces can be assembled into a :class:`~puzzlepiece.puzzle.Puzzle`.

    :param puzzle: The parent :class:`~puzzlepiece.puzzle.Puzzle`.
    :param custom_horizontal: A bool flat, the custom layout is displayed to the right of the main controls
                                if True.
    """
    def __init__(self, puzzle, custom_horizontal=False, *args, **kwargs):
        super().__init__()
        #: Reference to the parent :class:`~puzzlepiece.puzzle.Puzzle`.
        self.puzzle = puzzle
        #: Boolean flag. See :func:`~puzzlepiece.piece.Piece.call_stop`
        self.stop = False

        #: dict: A dictionary of this Piece's params (see :class:`~puzzlepiece.param.BaseParam`)
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
            layout.addWidget(self.params[key], i%numrows, i//numrows)
        return layout

    def action_layout(self, wrap=2):
        """
        Genereates a `QGridLayout` for the actions. Override to set a different wrapping.

        :param wrap: the number of columns the actions are displayed in .
        :rtype: QtWidgets.QGridLayout
        """
        layout = QtWidgets.QGridLayout()
        visible_actions = [key for key in self.actions if self.actions[key].visible]
        for i, key in enumerate(visible_actions):
            button = QtWidgets.QPushButton(key)
            button.clicked.connect(lambda x=False, _key=key: self.actions[_key]())
            layout.addWidget(button, i//wrap, i%wrap)
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

    def call_stop(self):
        """
        This method is called by the parent Puzzle when a global stop is called.

        By default, it sets the stop flag to True. Detect the flag in you code to stop processes.

        Alternatively, this can be overriden to support more complex actions.
        """
        self.stop = True

    def handle_close(self, event):
        """
        Only called if the :class:`~puzzlepiece.puzzle.Puzzle` debug flag is False.
        Override to disconnect hardware etc when the main window closes.
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

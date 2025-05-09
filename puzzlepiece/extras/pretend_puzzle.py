from qtpy import QtCore, QtWidgets


class PretendPuzzle(QtCore.QObject):
    """
    A placeholder object used if no :class:`~puzzlepiece.puzzle.Puzzle` is provided
    when creating a :class:`puzzlepiece.puzzle.Piece`. Its `debug` attribute is
    always True.
    """

    debug = True
    _close_popups = QtCore.Signal()

    def process_events(self):
        """
        Like :func:`puzzlepiece.puzzle.Puzzle.process_events()`.
        """
        if (app := QtWidgets.QApplication.instance()) is not None:
            app.processEvents()

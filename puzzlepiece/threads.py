from qtpy import QtCore, QtWidgets
import time

class _Emitter(QtCore.QObject):
    # The Emitter is needed as a QRunnable is not a QObject, and cannot emit it's own signals.
    # So we set up the Signal here, and let a Worker instance an Emitter for its use
    signal = QtCore.Signal(object)

class Worker(QtCore.QRunnable):
    """
    Generic worker (QRunnable) that calls a function in a thread.

    :param function: The function for the Worker to run.
    :param args: list of arguments to be forwarded to the function when run.
    :param kwargs: dictionary of keyword arguments to be forwarded to the function when run.
    """
    def __init__(self, function, args=None, kwargs=None):
        self.function = function
        self.args = args if args is not None else []
        self.kwargs = kwargs if kwargs is not None else {}
        self.done = False
        self._emitter = _Emitter()
        #: A Qt signal emitted when the function returns, passes the returned value to the connected Slot.
        self.returned = self._emitter.signal
        super().__init__()

    @QtCore.Slot()
    def run(self):
        """
        Run the Worker. Shouldn't be excecuted directly, instead
        use :func:`puzzlepiece.puzzle.Puzzle.run_worker`.
        """
        try:
            r = self.function(*self.args, **self.kwargs)
            self.returned.emit(r)
        finally:
            self.done=True


class LiveWorker(Worker):
    """
    A Worker that calls a function repeatedly in a thread,
    separated by specified time intervals.

    :param function: The function for the Worker to run.
    :param sleep: Time to sleep between function calls in seconds.
    :param args: list of arguments to be forwarded to the function when run.
    :param kwargs: dictionary of keyword arguments to be forwarded to the function when run.
    """
    def __init__(self, function, sleep=.1, args=None, kwargs=None):
        self.stopping = False
        self.sleep = sleep
        super().__init__(function, args, kwargs)
        #: A Qt signal emitted each time the function returns, passes the returned value to the connected Slot.
        self.returned = self.returned

    def stop(self):
        """
        Ask the Worker to stop. This will only take effect once the current
        execution of the function is over.
        """
        self.stopping = True

    @QtCore.Slot()
    def run(self):
        """
        Run the Worker. Shouldn't be excecuted directly, instead
        use :func:`puzzlepiece.puzzle.Puzzle.run_worker`.
        """
        try:
            while not self.stopping:
                r = self.function(*self.args, **self.kwargs)
                self.returned.emit(r)
                if not self.stopping:
                    time.sleep(self.sleep)
        finally:
            self.done = True


class PuzzleTimer(QtWidgets.QWidget):
    """
    A Widget that displays a checkbox. When the checkbox is checked, an associated
    function is called repeatedly in a thread, separated by specified time intervals.

    :param name: The display name for this PuzzleTimer.
    :param puzzle: The parent :class:`~puzzlepiece.puzzle.Puzzle` (needed as the Puzzle
      is charged with the QThreadPool that runs the tasks).
    :param function: The function for the PuzzleTimer to run.
    :param sleep: Time to sleep between function calls in seconds.
    :param args: list of arguments to be forwarded to the function when run.
    :param kwargs: dictionary of keyword arguments to be forwarded to the function when run.
    """
    #: A Qt signal emitted each time the associated LiveWorker returns, passes the returned value to the connected Slot.
    returned = QtCore.Signal(object)
    def __init__(self, name, puzzle, function, sleep=.1, args=None, kwargs=None):
        self.name = name
        self.puzzle = puzzle
        self.function = function
        self._sleep = sleep
        self.args = args
        self.kwargs = kwargs
        self.worker = None

        super().__init__()

        layout = QtWidgets.QGridLayout()
        layout.setContentsMargins(0,0,0,0)
        self.setLayout(layout)

        self.input = QtWidgets.QCheckBox(self.name)
        layout.addWidget(self.input)
        self.input.stateChanged.connect(self._state_handler)

    def _state_handler(self, state):
        if state and (self.worker is None or self.worker.done):
            self.worker = LiveWorker(self.function, self._sleep, self.args, self.kwargs)
            self.worker.returned.connect(self._return_handler)
            self.puzzle.run_worker(self.worker)
        elif self.worker is not None:
            self.worker.stop()

    def _return_handler(self, value):
        self.returned.emit(value)

    def stop(self):
        """
        Ask the PuzzleTimer to stop.
        
        This will only take effect once the current execution of the function is over,
        see :func:`puzzlepiece.threads.LiveWorker.stop`.
        """
        self.input.setChecked(False)

    @property
    def sleep(self):
        """
        Interval in seconds between executions of the associated function.
        The property can be modified to change the interval for the associated Worker,
        even if it's already running.
        """
        return self._sleep
    
    @sleep.setter
    def sleep(self, value):
        if self.worker is not None:
            self.worker.sleep = float(value)
        self._sleep = float(value)
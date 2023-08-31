from pyqtgraph.Qt import QtCore, QtWidgets
from functools import wraps
# import traceback

class Action(QtCore.QObject):
    called = QtCore.Signal()
    """A Signal"""

    def __init__(self, function, parent, shortcut=None, visible=True):
        self.function = function
        self.parent = parent
        # See https://doc.qt.io/qt-6/qt.html#Key-enum for acceptable values
        self.shortcut = shortcut
        self.visible = visible
        super().__init__()

    def __call__(self, *args, **kwargs):
        self.parent.elevate()
        self.function(*args, **kwargs)
        self.called.emit()

def define(self, name, shortcut=None, visible=True):
    def decorator(action):
        @wraps(action)
        def wrapper():
            return action(self)
        action_object = Action(wrapper, self, shortcut, visible)
        self.actions[name] = action_object
        if shortcut:
            self.shortcuts[shortcut] = action_object
        return wrapper
    return decorator
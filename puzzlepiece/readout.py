from pyqtgraph.Qt import QtWidgets, QtCore
from functools import wraps

class Readout(QtWidgets.QWidget):
    changed = QtCore.Signal()

    def __init__(self, name, getter, format, visible=True, *args, **kwargs):
        super().__init__()
        self._getter = getter
        self._format = format
        self.visible = visible
        self._value = None

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        self.setLayout(layout)

        # Give it a label
        self.label = QtWidgets.QLabel()
        self.label.setText(name+':')
        layout.addWidget(self.label)

        # Give it a value display
        self.value_label = QtWidgets.QLabel()
        layout.addWidget(self.value_label)
        # self.get_value()

        # Give it a button for getting the value
        self.button = QtWidgets.QPushButton("Get")
        # Using a lambda as the clicked signal always passes False as the first argument
        self.button.clicked.connect(lambda x: self.get_value())
        layout.addWidget(self.button)

    def get_value(self):
        value = self._getter()
        return self.set_value(value)

    @property
    def value(self):
        """
        A getter for obtaining the current value of this readout without performing
        the readoud getter function
        """
        return self._value

    def set_value(self, value):
        self._value = value
        self.value_label.setText(self._format.format(self._value))
        self.changed.emit()
        return self._value


def define(self, name, format="{}", visible=True):
    def decorator(getter):
        @wraps(getter)
        def wrapper():
            return getter(self)
        self.readouts[name] = Readout(name, wrapper, format, visible)
        return wrapper
    return decorator
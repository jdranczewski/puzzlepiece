from pyqtgraph.Qt import QtWidgets, QtCore
from functools import wraps
import traceback

class AbstractParam(QtWidgets.QWidget):
    changed = QtCore.Signal()
    _type = None

    def __init__(self, name, value, setter, visible=True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setter = setter
        self.visible = visible
        # Cache the actual value, this is updated only when the setter is called
        self._value = None

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        self.setLayout(layout)

        # Give it a label
        self.label = QtWidgets.QLabel()
        self.label.setText(name+':')
        layout.addWidget(self.label)

        # Give it an input box
        self.input, make_button = self.make_input(value, self.value_change_handler)
        if self._setter is None:
            self._value = value
        else:
            # Highlight that the setter hasn't been called yet
            self.input.setStyleSheet("QWidget { background-color: #fcd9ca; }")
        layout.addWidget(self.input)
        # self.set_value(value)

        # Give it a button for setting the value
        if self._setter is not None and make_button:
            self.button = QtWidgets.QPushButton("Set")
            # Using a lambda as the clicked signal always passes False as the first argument
            self.button.clicked.connect(lambda x: self.set_value())
            layout.addWidget(self.button)

    def value_change_handler(self):
        if self._setter is not None:
            # Highlight the input box if a setter is set
            self.input.setStyleSheet("QWidget { background-color: #fcd9ca; }")
        else:
            # If there's no setter, we write the value directly to the internal _value variable
            self._value = self.input_get_value()
            self.changed.emit()

    def make_input(self, value=None, connect=None):
        raise NotImplementedError
    
    def input_set_value(self, value):
        raise NotImplementedError
    
    def input_get_value(self, value):
        raise NotImplementedError

    def set_value(self, value=None):
        if value is None:
            value = self.input_get_value()
        else:
            value = self._type(value)
            self.input_set_value(value)
        self._value = value
        if self._setter is not None:
            self._value = self._setter(value)
            self.input_set_value(self._value)
            self.changed.emit()
            self.input.setStyleSheet("")

    def get_value(self):
        return self._value

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Enter or event.key() == QtCore.Qt.Key_Return:
            self.set_value()
            # Move focus out of the input, so other keyboard shortcuts can be processed
            self.setFocus()
        else:
            super().keyPressEvent(event)


class ParamInt(AbstractParam):
    _type = int

    def __init__(self, name, value, v_min, v_max, setter, visible=True, *args, **kwargs):
        self._v_min = v_min
        self._v_max = v_max
        super().__init__(name, value, setter, visible, *args, **kwargs)

    def make_input(self, value=None, connect=None):
        input = QtWidgets.QSpinBox()
        input.setMinimum(self._v_min)
        input.setMaximum(self._v_max)
        input.setGroupSeparatorShown(True)
        if value is not None:
            input.setValue(value)
        if connect is not None:
            input.valueChanged.connect(lambda x: connect())
        return input, True

    def input_set_value(self, value):
        self.input.setValue(value)

    def input_get_value(self):
        return self.input.value()


class ParamFloat(ParamInt):
    _type = float

    def make_input(self, value=None, connect=None):
        input = QtWidgets.QDoubleSpinBox()
        input.setGroupSeparatorShown(True)
        input.setMinimum(self._v_min)
        input.setMaximum(self._v_max)
        if value is not None:
            input.setValue(value)
        if connect is not None:
            input.valueChanged.connect(connect)
        return input, True


class ParamText(AbstractParam):
    _type = str

    def make_input(self, value=None, connect=None):
        input = QtWidgets.QLineEdit()
        if value is not None:
            input.setText(value)
        if connect is not None:
            input.textChanged.connect(connect)
        return input, True

    def input_set_value(self, value):
        self.input.setText(value)

    def input_get_value(self):
        return self.input.text()
    

class ParamCheckbox(AbstractParam):
    _type = int

    def __init__(self, name, value, setter, visible=True, *args, **kwargs):
        super().__init__(name, value, setter, visible, *args, **kwargs)

    def make_input(self, value=None, connect=None):
        input = QtWidgets.QCheckBox()
        if value is not None:
            input.setChecked(bool(value))
        if connect is not None:
            input.stateChanged.connect(connect)
        input.clicked.connect(lambda x: self.set_value())
        return input, False

    def input_set_value(self, value):
        self.input.setChecked(bool(value))

    def input_get_value(self):
        return int(self.input.isChecked())


# I do apologise for how messy the decorator syntax is in Python
def spinbox(self, name, value, v_min=-1e9, v_max=1e9, visible=True):
    # The spinbox function *returns a decorator*,
    # it's just the way to enable passing parameters to decorators
    def decorator(setter):
        # We wrap the setter function such that it can be called without passing
        # a class instance as the first argument
        if setter is None:
            if isinstance(value, int):
                self.params[name] = ParamInt(name, value, int(v_min), int(v_max), None, visible)
            else:
                self.params[name] = ParamFloat(name, value, v_min, v_max, None, visible)
            return None
        else:
            @wraps(setter)
            def wrapper(value):
                return setter(self, value)
            # Here we make a Param object and add it to the dictionary of the Piece this was called from
            if isinstance(value, int):
                self.params[name] = ParamInt(name, value, int(v_min), int(v_max), wrapper, visible)
            else:
                self.params[name] = ParamFloat(name, value, v_min, v_max, wrapper, visible)
            return wrapper
    return decorator

def text(self, name, value, visible=True):
    def decorator(setter):
        if setter is None:
            self.params[name] = ParamText(name, value, None, visible)
            return None
        else:
            @wraps(setter)
            def wrapper(value):
                return setter(self, value)
            self.params[name] = ParamText(name, value, wrapper, visible)
            return wrapper
    return decorator

def checkbox(self, name, value, visible=True):
    def decorator(setter):
        if setter is None:
            self.params[name] = ParamCheckbox(name, value, None, visible)
            return None
        else:
            @wraps(setter)
            def wrapper(value):
                return setter(self, value)
            self.params[name] = ParamCheckbox(name, value, wrapper, visible)
            return wrapper
    return decorator
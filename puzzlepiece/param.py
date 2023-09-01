from pyqtgraph.Qt import QtWidgets, QtCore
from functools import wraps

class BaseParam(QtWidgets.QWidget):
    changed = QtCore.Signal()
    _type = None

    def __init__(self, name, value, setter, getter=None, visible=True, format='{}', _type=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setter = setter
        self._getter = getter
        self._value = None
        self._visible = visible
        self._format = format
        if _type is not None:
            self._type = _type
        if self._type is None:
            if value is not None:
                # Infer type if not provided by subclassing
                self._type = type(value)
            else:
                # Bypass type conversion if type not known
                self._type = lambda x: x

        self._main_layout = layout = QtWidgets.QGridLayout()
        layout.setContentsMargins(0,0,0,0)
        self.setLayout(layout)

        # Give the param a label
        self.label = QtWidgets.QLabel()
        self.label.setText(name+':')
        layout.addWidget(self.label, 0, 0)

        # Give the param an input box
        self.input, make_set_button = self._make_input(value, self._value_change_handler)
        if self._setter is None:
            self._value = value
        if self._value is None:
            # Highlight that the setter or getter haven't been called yet
            self.input.setStyleSheet("QWidget { background-color: #fcd9ca; }")
        layout.addWidget(self.input, 0, 1)
        # self.set_value(value)

        # Give it buttons for setting and getting the value
        if self._getter is not None:
            self._make_get_button()
        if self._setter is not None and make_set_button:
            self._make_set_button()
    
    def _make_set_button(self):
        self._set_button = QtWidgets.QToolButton()
        # Icon list: https://www.pythonguis.com/faq/built-in-qicons-pyqt/
        icon = self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DialogApplyButton)
        self._set_button.setIcon(icon)
        # Using a lambda as the clicked signal always passes False as the first argument
        self._set_button.clicked.connect(lambda x: self.set_value())
        self._main_layout.addWidget(self._set_button, 0, 3)

    def _make_get_button(self):
        self._get_button = QtWidgets.QToolButton()
        icon = self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_BrowserReload)
        self._get_button.setIcon(icon)
        self._get_button.clicked.connect(lambda x: self.get_value())
        self._main_layout.addWidget(self._get_button, 0, 2)

    def _value_change_handler(self):
        if self._setter is not None:
            # Highlight the input box if a setter is set
            self.input.setStyleSheet("QWidget { background-color: #fcd9ca; }")
        else:
            # If there's no setter, we write the value directly to the internal _value variable
            self._value = self._input_get_value()
            self.changed.emit()

    def _make_input(self, value=None, connect=None):
        input = QtWidgets.QLabel()
        if value is not None:
            input.setText(self._format.format(value))
        self.__label_input_connection = connect
        return input, True
    
    def _input_set_value(self, value):
        self.input.setText(self._format.format(value))
        self.__label_input_connection()
    
    def _input_get_value(self):
        return self._type(self.input.text())

    def set_value(self, value=None):
        # If a value is not provided, grab one from the input
        if value is None:
            value = self._input_get_value()
        else:
            # Otherwise push the given value to the input
            value = self._type(value)
            self._input_set_value(value)
        
        if self._setter is not None:
            # Call setter if it exists. It may return a new value.
            new_value = self._setter(value)
            if new_value is None:
                # If the setter did not return a value, see if there is a getter
                if self._getter is not None:
                    new_value = self._getter()
                else:
                    # Otherwise the new value is just the value we're setting
                    new_value = value
            # Update the value stored to the new value
            self._value = new_value
            # Update the input as well, clearing the highlight
            self._input_set_value(new_value)
            self.input.setStyleSheet("")
            # Emit the changes signal (_value_change_handler doesn't emit if there's a setter)
            self.changed.emit()
        # If a setter doesn't exist, _value_change_handler handles updating the internal _value
        # and emits the changed signal, so no further action needed

    def get_value(self):
        if self._getter is not None:
            new_value = self._getter()
            new_value = self._type(new_value)

            # Set the value to the input and emit signal if needed
            self._input_set_value(new_value)
            self.input.setStyleSheet("")
            if self._setter is not None:
                # _value_change_handler doesn't emit the signal if there's a setter
                self.changed.emit()

            return new_value
        else:
            return self._value
        
    def set_getter(self, piece):
        def decorator(getter):
            wrapper = wrap_getter(piece, getter)
            self._getter = wrapper
            self._make_get_button()
            return self
        return decorator
        
    @property
    def value(self):
        """
        Current, internally stored value.
        The getter is not called when this property is accessed.
        """
        return self._value
    
    @property
    def visible(self):
        return self._visible

    def keyPressEvent(self, event):
        # Allow pressing enter to trigger the set action
        if event.key() == QtCore.Qt.Key.Key_Enter or event.key() == QtCore.Qt.Key.Key_Return:
            self.set_value()
            # Move focus out of the input, so other keyboard shortcuts can be processed
            self.setFocus()
        else:
            super().keyPressEvent(event)


class ParamInt(BaseParam):
    _type = int
    def __init__(self, name, value, v_min, v_max, setter, getter=None, visible=True, *args, **kwargs):
        self._v_min = v_min
        self._v_max = v_max
        super().__init__(name, value, setter, getter, visible, *args, **kwargs)

    def _make_input(self, value=None, connect=None):
        input = QtWidgets.QSpinBox()
        input.setMinimum(self._v_min)
        input.setMaximum(self._v_max)
        input.setGroupSeparatorShown(True)
        if value is not None:
            input.setValue(value)
        if connect is not None:
            input.valueChanged.connect(lambda x: connect())
        return input, True

    def _input_set_value(self, value):
        self.input.setValue(value)

    def _input_get_value(self):
        return self.input.value()


class ParamFloat(ParamInt):
    _type = float

    def _make_input(self, value=None, connect=None):
        input = QtWidgets.QDoubleSpinBox()
        input.setGroupSeparatorShown(True)
        input.setMinimum(self._v_min)
        input.setMaximum(self._v_max)
        if value is not None:
            input.setValue(value)
        if connect is not None:
            input.valueChanged.connect(connect)
        return input, True


class ParamText(BaseParam):
    _type = str

    def _make_input(self, value=None, connect=None):
        input = QtWidgets.QLineEdit()
        if value is not None:
            input.setText(value)
        if connect is not None:
            input.textChanged.connect(connect)
        return input, True

    def _input_set_value(self, value):
        self.input.setText(value)

    def _input_get_value(self):
        return self.input.text()


class ParamCheckbox(BaseParam):
    _type = int
    #TODO: handle exceptions better!

    def __init__(self, name, value, setter, getter=None, visible=True, *args, **kwargs):
        super().__init__(name, value, setter, getter, visible, *args, **kwargs)

    def _make_input(self, value=None, connect=None):
        input = QtWidgets.QCheckBox()
        if value is not None:
            input.setChecked(bool(value))
        if connect is not None:
            input.stateChanged.connect(connect)
        input.clicked.connect(lambda x: self.set_value())
        return input, False

    def _input_set_value(self, value):
        self.input.setChecked(bool(value))

    def _input_get_value(self):
        return int(self.input.isChecked())


def wrap_setter(piece, setter):
    if setter is not None:
        # We wrap the setter function such that it can be called without passing
        # a reference to the Piece as the first argument
        @wraps(setter)
        def wrapper(value):
            return setter(piece, value)
    else:
        wrapper = None
    return wrapper

def wrap_getter(piece, getter):
    if getter is not None:
        @wraps(getter)
        def wrapper():
            return getter(piece)
    else:
        wrapper = None
    return wrapper


# The decorator syntax in Python is a little confusing
def base_param(piece, name, value, visible=True, format='{}'):
    # The base_param function *creates and returns a decorator*,
    # it's just the way to enable passing parameters when decorating something
    def decorator(setter):
        wrapper = wrap_setter(piece, setter)

        # Register the param with the Piece
        piece.params[name] = BaseParam(name, value, setter=wrapper, getter=None, visible=visible, format=format)

        # Return the newly created Param
        return piece.params[name]
    return decorator

def readout(piece, name, visible=True, format="{}", _type=None):
    def decorator(getter):
        wrapper = wrap_getter(piece, getter)
        piece.params[name] = BaseParam(name, None, setter=None, getter=wrapper, visible=visible, format=format, _type=_type)
        return piece.params[name]
    return decorator

def spinbox(piece, name, value, v_min=-1e9, v_max=1e9, visible=True):
    def decorator(setter):
        wrapper = wrap_setter(piece, setter)
        
        if isinstance(value, int):
            piece.params[name] = ParamInt(name, value, int(v_min), int(v_max), setter=wrapper, getter=None, visible=visible)
        else:
            piece.params[name] = ParamFloat(name, value, v_min, v_max, wrapper, None, visible)
        return piece.params[name]
    return decorator

def text(piece, name, value, visible=True):
    def decorator(setter):
        wrapper = wrap_setter(piece, setter)  
        piece.params[name] = ParamText(name, value, wrapper, None, visible)
        return piece.params[name]
    return decorator

def checkbox(piece, name, value, visible=True):
    def decorator(setter):
        wrapper = wrap_setter(piece, setter)
        piece.params[name] = ParamCheckbox(name, value, wrapper, None, visible)
        return piece.params[name]
    return decorator
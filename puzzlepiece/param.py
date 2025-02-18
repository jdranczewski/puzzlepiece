from qtpy import QtWidgets, QtCore, QtGui
import inspect
import numpy as np

from . import _snippets
from . import threads


_red_bg_palette = QtGui.QPalette()
_red_bg_palette.setColor(
    _red_bg_palette.ColorRole.Window, QtGui.QColor(252, 217, 202, 255)
)


class BaseParam(QtWidgets.QWidget):
    """
    A param object represents a gettable/settable value within a :class:`~puzzlepiece.piece.Piece`. This can be
    a general variable for some operation, a setting of a physical device (like laser power), a readout from a
    physical device (counts from a spectrometer), or something that can be measured and set (the position of a
    movable stage).

    A general param is just a variable with a GUI presence (if needed) that can be read from and written to by
    Pieces. It can then have getter and setter functions that are called when you get/set the value of the param.

    To set and get the value of the param, use the :func:`~puzzlepiece.param.BaseParam.set_value` and
    :func:`~puzzlepiece.param.get_value` methods.

    **In most cases, you will not instantiate a param directly, but rather use decorators defined within this module
    (like** :func:`puzzlepiece.param.spinbox` **)
    to register params within a Piece's** :func:`~puzzlepiece.piece.Piece.define_params` **method.**

    :param name: A unique (per Piece) id name for the param
    :param value: Default value (can be None)
    :param setter: A function to be called when setting the param, taking the value as argument. It may return a new value.
    :param getter: A function to be called when obtaining the value of the param, raturning the new value.
    :param visible: If True, the Piece will generate display a GUI component for the param.
    :param format: Default format for displaying the param if a custom input is not defined, and in
      :func:`puzzplepiece.parse.format`. For example `{:.2f}`, see https://pyformat.info/ for further details.
    :param _type: int, float, str etc - the type of the param value. Can be inferred if a default value is passed.
    :param piece: The parent Piece, can be None (currently only used for threaded sets and gets).
    """

    #: A Qt signal emitted when the value changes
    changed = QtCore.Signal()
    _sig_input_set_value = QtCore.Signal(object)
    _sig_setAutoFillBackground = QtCore.Signal(bool)
    _type = None

    def __init__(
        self,
        name,
        value,
        setter=None,
        getter=None,
        visible=True,
        format="{}",
        _type=None,
        piece=None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self._name = name
        self._setter = setter
        self._getter = getter
        self._value = None
        self._visible = visible
        self._format = format
        self._piece = piece

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
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.setPalette(_red_bg_palette)

        # Give the param a label
        self.label = QtWidgets.QLabel()
        self.label.setText(name + ":")
        layout.addWidget(self.label, 0, 0)

        # Give the param an input box
        self.input, make_set_button = self._make_input(
            value, self._value_change_handler
        )
        if self._setter is None and value is not None:
            self._value = self._type(value)
        if self._value is None:
            # Highlight that the setter or getter haven't been called yet
            self.setAutoFillBackground(True)
        layout.addWidget(self.input, 0, 1)

        # Allow for setting the input value and background colour through a signal
        # This allows us to make `set_value` and `get_value` thread-safe
        # see https://github.com/jdranczewski/puzzlepiece/issues/7
        self._sig_input_set_value.connect(self._input_set_value)
        self._sig_setAutoFillBackground.connect(self.setAutoFillBackground)

        # Give it buttons for setting and getting the value
        if self._getter is not None:
            self._make_get_button()
        if self._setter is not None and make_set_button:
            self._make_set_button()

    def _make_set_button(self):
        self._set_button = QtWidgets.QToolButton()
        # Icon list: https://www.pythonguis.com/faq/built-in-qicons-pyqt/
        icon = self.style().standardIcon(
            QtWidgets.QStyle.StandardPixmap.SP_DialogApplyButton
        )
        self._set_button.setIcon(icon)

        # False always passed as the first argument
        def set_callback(_):
            if (
                self._piece is not None
                and self._piece.puzzle.app.keyboardModifiers()
                == QtCore.Qt.KeyboardModifier.ControlModifier
            ):
                self.set_value_threaded()
            else:
                self.set_value()

        self._set_button.clicked.connect(set_callback)
        self._main_layout.addWidget(self._set_button, 0, 3)

    def _make_get_button(self):
        self._get_button = QtWidgets.QToolButton()
        icon = self.style().standardIcon(
            QtWidgets.QStyle.StandardPixmap.SP_BrowserReload
        )
        self._get_button.setIcon(icon)

        def get_callback(_):
            if (
                self._piece is not None
                and self._piece.puzzle.app.keyboardModifiers()
                == QtCore.Qt.KeyboardModifier.ControlModifier
            ):
                self.get_value_threaded()
            else:
                self.get_value()

        self._get_button.clicked.connect(get_callback)
        self._main_layout.addWidget(self._get_button, 0, 2)

    def _value_change_handler(self):
        if self._setter is not None:
            # Highlight the param box if a setter is set
            self.setAutoFillBackground(True)
        else:
            # If there's no setter, we call set_value to set the value from input
            self.set_value()

    def set_value(self, value=None):
        """
        Set the value of the param. If a setter is registered, it will be called.

        If the setter returns a value, this will become the new value of this param.

        If the setter doesn't return a value, the getter will be called if present,
        and the value it returns will become the new value of this param.

        If the setter doesn't return a value, and there is no getter, the value
        provided as an argument will become the new value of this param

        :param value: The value this param should be set to (if None, we grab the value from
          the param's input box.)
        :returns: The new value of the param.
        """
        # If a value is not provided, grab one from the input
        if value is None:
            value = self._input_get_value()
        else:
            # Otherwise push the given value to the input
            value = self._type(value)
            self._sig_input_set_value.emit(value)

        if self._setter is not None:
            # Colour the background to indicate setter is running
            self._sig_setAutoFillBackground.emit(True)
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
            new_value = self._type(new_value)
            self._value = new_value
            # Update the input as well
            self._sig_input_set_value.emit(new_value)
        else:
            self._value = value

        # Clear the highlight and emit the changed signal
        self._sig_setAutoFillBackground.emit(False)
        self.changed.emit()
        return self._value

    def get_value(self):
        """
        Get the value for this param. If a getter is registered, it will be called, and the
        returned value becomes the params new value, and is returned by this method.

        :returns: Value of the param (retuned by the getter if registered, otherwise the value
          currently stored by the param).
        """
        if self._getter is not None:
            new_value = self._getter()
            new_value = self._type(new_value)
            self._value = new_value

            # Set the value to the input and emit signal if needed
            self._sig_input_set_value.emit(new_value)
            self._sig_setAutoFillBackground.emit(False)
            self.changed.emit()

            return new_value
        else:
            return self._value

    def set_value_threaded(self, value=None):
        """
        Call :func:`~puzzlepiece.param.BaseParam.set_value` in a thread. While
        :func:`~puzzlepiece.param.BaseParam.set_value` itself is by default threadsafe,
        the setter/getter may not be depending on the user's implementation. See
        :mod:`puzzlepiece.threads` for further notes, and be mindful when using this.

        Can also be called by holding control while clicking the set button or pressing
        enter in a param's input box.
        """
        if self._piece.puzzle is not None:
            self._piece.puzzle.run_worker(threads.Worker(lambda: self.set_value(value)))
        else:
            self.set_value(value)

    def get_value_threaded(self):
        """
        Call :func:`~puzzlepiece.param.BaseParam.get_value` in a thread. While
        :func:`~puzzlepiece.param.BaseParam.get_value` itself is by default threadsafe,
        the getter may not be depending on the user's implementation. See
        :mod:`puzzlepiece.threads` for further notes, and be mindful when using this.

        Can also be called by holding control while clicking the set button or pressing
        enter in a param's input box.
        """
        if self._piece.puzzle is not None:
            # Colour the background to indicate getter is running
            self._sig_setAutoFillBackground.emit(True)
            self._piece.puzzle.run_worker(threads.Worker(lambda: self.get_value()))
        else:
            self.get_value()

    def set_setter(self, piece):
        """
        Create a decorator to register a setter for this param. This would be used within
        :func:`puzzlepiece.piece.Piece.define_params` as ``@param.set_setter(self)`` decorating
        a function.
        """

        def decorator(setter):
            wrapper = wrap_setter(piece, setter)
            self._setter = wrapper
            self._make_set_button()
            return self

        return decorator

    def set_getter(self, piece):
        """
        Create a decorator to register a getter for this param. This would be used within
        :func:`puzzlepiece.piece.Piece.define_params` as ``@param.set_getter(self)`` decorating
        a function.
        """

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

    def _make_input(self, value=None, connect=None):
        """
        Create an input box for the GUI display of this param. This should be overriden to implement
        custom param display types (like the spinboxes, text inputs, and checkboxes provided by default).

        :param value: The value to put into the input box by default.
        :param connect: A function that will be connected to the value changed signal of the input.
        :rtype: (QWidget - input box, bool - whether a setter button is needed)

        :meta public:
        """
        input = QtWidgets.QLabel()
        if value is not None:
            input.setText(self._format.format(value))
        return input, True

    def _input_set_value(self, value):
        """
        Set the value of the input box. This should be overriden to implement
        custom param display types.

        As this is a low-level method used internally, it **should not** emit valueChanged
        signals for its input box. To stop this from happening, use Qt's `blockSignals`
        method::

            self.input.blockSignals(True)
            self.input.setText(value)
            self.input.blockSignals(False)

        :meta public:
        """
        self.input.setText(self._format.format(value))

    def _input_get_value(self):
        """
        Set the value of the input box. This should be overriden to implement
        custom param display types.

        :rtype: Should return the velue with correct type, as specified by `self._type`

        :meta public:
        """
        return self._type(self.input.text())

    def make_child_param(self, kwargs=None):
        """
        Create and return a child param. Changing the value of the child changes the value
        of the parent, but not vice versa - each child has a getter that allows for refreshing
        the value from the parent.

        The child will be of the same type as the parent - a checkbox, spinbox, etc.

        The parent's getter will be called when you :func:`~puzzlepiece.param.BaseParam.get_value`
        on the child. The parent's setter will be called when you
        :func:`~puzzlepiece.param.BaseParam.set_value` on a child.

        You may need to override this method when creating params that have a different call
        signature for ``__init__``. Additional arguments can then be provided with ``kwargs``.

        See :func:`puzzlepiece.piece.Popup.add_child_params` for a quick way of adding child
        params to a popup.

        :param kwargs: Additional arguments to pass when creating the child.
        """
        # Only make an explicit setter if this param has an explicit setter.
        # The other case is handled via a Signal below, once the child
        # param is created.
        setter = None if self._setter is None else (lambda value: self.set_value(value))

        # child params always have a getter, to make the direction of data flow clear.
        def getter():
            return self.get_value()

        kwargs = kwargs or {}

        child = type(self)(
            self._name,
            self._value,
            setter=setter,
            getter=getter,
            format=self._format,
            _type=self._type,
            **kwargs,
        )

        if self._setter is None:
            # If no explicit setter, just set the parent param whenever the child updates
            child.changed.connect(lambda: self.set_value(child.value))
        elif self._value is not None:
            # When a param is created and has an explicit setter, it will be highlighted
            # red to indicate the setter has not been called. Here we remove the highlight
            # for the child if the parent's setter has been called already.
            child.setAutoFillBackground(False)

        return child

    @property
    def type(self):
        """
        The fixed type of this param. The values set with
        :func:`puzzlepiece.param.BaseParam.set_value` will be cast to this type,
        and those returned by :func:`puzzlepiece.param.BaseParam.get_value`
        will be of this type.
        """
        return self._type

    @property
    def visible(self):
        """
        Bool flag indicating whether the param is displayed in the GUI.
        """
        return self._visible

    def keyPressEvent(self, event):
        """
        # Pressing enter triggers the set action.

        :meta private:
        """
        if (
            event.key() == QtCore.Qt.Key.Key_Enter
            or event.key() == QtCore.Qt.Key.Key_Return
        ):
            if event.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier:
                self.set_value_threaded()
            else:
                self.set_value()
            # Move focus out of the input, so other keyboard shortcuts can be processed
            self.setFocus()
        else:
            super().keyPressEvent(event)


class ParamInt(BaseParam):
    """
    A param with an integer input field. See the :func:`~puzzlepiece.param.spinbox` decorator below
    for how to use this in your Piece.
    """

    _type = int

    def __init__(
        self,
        name,
        value,
        v_min,
        v_max,
        setter,
        getter=None,
        visible=True,
        v_step=1,
        *args,
        **kwargs,
    ):
        self._v_min = v_min
        self._v_max = v_max
        self._v_step = v_step
        super().__init__(name, value, setter, getter, visible, *args, **kwargs)

    def _make_input(self, value=None, connect=None):
        """:meta private:"""
        input = QtWidgets.QSpinBox()
        input.setMinimum(self._v_min)
        input.setMaximum(self._v_max)
        input.setSingleStep(self._v_step)
        input.setGroupSeparatorShown(True)
        if value is not None:
            input.setValue(value)
        if connect is not None:
            input.valueChanged.connect(lambda x: connect())
        return input, True

    def _input_set_value(self, value):
        """:meta private:"""
        self.input.blockSignals(True)
        self.input.setValue(value)
        self.input.blockSignals(False)

    def _input_get_value(self):
        """:meta private:"""
        return self.input.value()

    def make_child_param(self, kwargs=None):
        """:meta private:"""
        return super().make_child_param(
            kwargs={
                "v_min": self._v_min,
                "v_max": self._v_max,
                "v_step": self._v_step,
            }
        )


class ParamFloat(ParamInt):
    """
    A param with a float input field. See the :func:`~puzzlepiece.param.spinbox` decorator below
    for how to use this in your Piece.
    """

    _type = float

    def _make_input(self, value=None, connect=None):
        """:meta private:"""
        input = QtWidgets.QDoubleSpinBox()
        input.setGroupSeparatorShown(True)
        input.setMinimum(self._v_min)
        input.setMaximum(self._v_max)
        input.setSingleStep(self._v_step)
        if value is not None:
            input.setValue(value)
        if connect is not None:
            input.valueChanged.connect(connect)
        return input, True


class _Slider(QtWidgets.QWidget):
    def __init__(self, value, v_min, v_max, v_step, format="{:.2f}"):
        self._v_min = v_min
        self._v_max = v_max
        self._v_step = v_step
        self._format = format
        super().__init__()

        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)

        self.input = input = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        input.setMinimum(int(np.round(v_min / v_step)))
        input.setMaximum(int(np.round(v_max / v_step)))
        input.setTickPosition(input.TickPosition.TicksBelow)
        layout.addWidget(input)
        self.valueChanged = self.input.valueChanged
        self.input.valueChanged.connect(self._set_label)

        self.input_label = QtWidgets.QLabel()
        layout.addWidget(self.input_label)

        if value is not None:
            input.setValue(int(np.round(value) / v_step))
            self._set_label()

    def _set_label(self):
        value = self.input.value() * self._v_step
        self.input_label.setText(self._format.format(value))

    def setValue(self, value):
        self.input.setValue(int(np.round(value / self._v_step)))
        # Label should work in situations where the Signals are blocked too
        self._set_label()

    def value(self):
        return self.input.value() * self._v_step

    def blockSignals(self, b):
        self.input.blockSignals(b)
        super().blockSignals(b)


class ParamSlider(ParamFloat):
    """
    A param with a slider, float or int depending on provided value and step.
    See the :func:`~puzzlepiece.param.slider` decorator below
    for how to use this in your Piece.
    """

    def _make_input(self, value=None, connect=None):
        if (
            isinstance(value, int)
            and isinstance(self._v_min, int)
            and isinstance(self._v_min, int)
            and isinstance(self._v_step, int)
        ):
            self._type = int

        format = "{:.2f}" if self._type is float else "{}"
        input = _Slider(value, self._v_min, self._v_max, self._v_step, format)
        if value is not None:
            input.setValue(value)
        if connect is not None:
            input.valueChanged.connect(connect)
        return input, True


class ParamText(BaseParam):
    """
    A param with a text input field. See the :func:`~puzzlepiece.param.text` decorator below
    for how to use this in your Piece.
    """

    _type = str

    def _make_input(self, value=None, connect=None):
        """:meta private:"""
        input = QtWidgets.QLineEdit()
        if value is not None:
            input.setText(value)
        if connect is not None:
            input.textChanged.connect(connect)
        return input, True

    def _input_set_value(self, value):
        """:meta private:"""
        self.input.blockSignals(True)
        self.input.setText(value)
        self.input.blockSignals(False)

    def _input_get_value(self):
        """:meta private:"""
        return self.input.text()


class ParamCheckbox(BaseParam):
    """
    A param with a checkbox input field. See the :func:`~puzzlepiece.param.checkbox` decorator below
    for how to use this in your Piece.

    This param runs :func:`puzzlepiece.param.Param.set_value` automatically when the checkbox
    is pressed, so an additional setter button is not displayed.
    """

    _type = int
    # TODO: handle exceptions better!

    def __init__(self, name, value, setter, getter=None, visible=True, *args, **kwargs):
        super().__init__(name, value, setter, getter, visible, *args, **kwargs)

    def _make_input(self, value=None, connect=None):
        """:meta private:"""
        input = QtWidgets.QCheckBox()
        if value is not None:
            input.setChecked(bool(value))
        # Handling the input change signal differently here to allow for some error handling
        # when the checkbox is clicked
        self._connected_click_handler = connect
        input.clicked.connect(self._click_handler)
        return input, False

    def _input_set_value(self, value):
        """:meta private:"""
        self.input.setChecked(bool(value))
        # if self._connected_click_handler is not None:
        #     self._connected_click_handler()

    def _input_get_value(self):
        """:meta private:"""
        return int(self.input.isChecked())

    def _click_handler(self, _):
        try:
            if self._connected_click_handler is not None:
                self._connected_click_handler()
            if self._setter is not None:
                # If there's a setter, we need to explicitly call set_value here
                self.set_value()
        except Exception as e:
            # Flip back the checkbox if the click resulted in an error
            self.input.setChecked(not (self.input.isChecked()))
            raise e


class _PartialAccessor:
    def __init__(self, param):
        self.param = param

    def __setitem__(self, key, value):
        self.param._value.__setitem__(key, value)
        self.param.set_value()


class ParamArray(BaseParam):
    """
    A param that stores a numpy array. There is no GUI input, the Param simply displays the
    dimensions of the array, and indicates when the data has been updated.

    The array can be modified through programmatic interaction with setter or getter functions
    (for example the array can be obtained from a hardware spectrometer), or treated as a variable
    and set using :func:`~puzzlepiece.param.BaseParam.set_value`.
    """

    _type = np.asarray

    def __init__(
        self,
        name,
        value,
        setter=None,
        getter=None,
        visible=True,
        _type=None,
        *args,
        **kwargs,
    ):
        self._indicator_state = True
        self._partial_accessor = _PartialAccessor(self)
        super().__init__(
            name, value, setter, getter, visible, _type=_type, *args, **kwargs
        )
        self.changed.connect(self._flip_indicator)

    @property
    def set_partial(self):
        """
        Use this property to set values to slices of the stored numpy array, using
        any slicing methods that a numpy array accepts::

            puzzle['piece'].params['image'].set_partial[100:200, :] = 128

        This will call the param's setter if there's one, and in general
        acts like :func:`~puzzlepiece.param.BaseParam.set_value`.
        """
        return self._partial_accessor

    def _make_input(self, value=None, connect=None):
        """
        :meta private:
        """
        input = QtWidgets.QLabel()
        if value is not None:
            input.setText(self._format_array(value))
        return input, True

    def _input_set_value(self, value):
        """
        :meta private:
        """
        self.input.setText(self._format_array(value))

    def _input_get_value(self):
        """
        :meta private:
        """
        return self._value

    def _flip_indicator(self):
        self._indicator_state = not self._indicator_state

    def _format_array(self, value):
        return f"array{value.shape} {'◧' if self._indicator_state else '◨'}"


class ParamDropdown(BaseParam):
    """
    A param storing a string that also provides a dropdown. The user can edit the text field directly,
    and pressing enter will add the current value to the dropdown. A list of values can also be provided
    when creating this param, and they will populate the dropdown as soon as the app starts.

    The default param value provided here as `value` will either be selected from the dropdown if
    in `values`, or inserted into the text field as if a user typed it if not in `values`.

    :param values: List of default values available in the dropdown (can be None)
    """

    _type = str

    def __init__(
        self,
        name,
        value,
        values,
        setter=None,
        getter=None,
        visible=True,
        *args,
        **kwargs,
    ):
        if values is None:
            self._values = []
        else:
            self._values = list(values)
        super().__init__(name, value, setter, getter, visible, *args, **kwargs)

    def _make_input(self, value=None, connect=None):
        """:meta private:"""
        input = QtWidgets.QComboBox(editable=True)

        # Add the possible values
        input.addItems([str(x) for x in self._values])

        if value is not None:
            value = str(value)
            if index := input.findData(value) > -1:
                input.setCurrentIndex(index)
            else:
                input.setCurrentText(value)

        if connect is not None:
            input.currentTextChanged.connect(connect)

        return input, True

    def _input_set_value(self, value):
        """:meta private:"""
        value = str(value)
        self.input.blockSignals(True)

        if index := self.input.findData(value) > -1:
            self.input.setCurrentIndex(index)
        else:
            self.input.setCurrentText(value)

        self.input.blockSignals(False)

    def _input_get_value(self):
        """:meta private:"""
        return self.input.currentText()

    def make_child_param(self, kwargs=None):
        return super().make_child_param(
            kwargs={
                "values": self._values,
            }
        )


class ParamProgress(BaseParam):
    """
    A param with a progress bar. See the :func:`~puzzlepiece.param.progress` decorator below
    for how to use this in your Piece.
    """

    _type = float

    def _make_input(self, value=None, connect=None):
        """:meta private:"""
        input = QtWidgets.QProgressBar()
        input.setMinimum(0)
        input.setMaximum(1000)
        if value is not None:
            input.setValue(value)
        return input, True

    def _input_set_value(self, value):
        """:meta private:"""
        if value < 0:
            self.input.setMaximum(0)
        else:
            self.input.setMaximum(1000)
            self.input.setValue(int(value * 1000))

    def _input_get_value(self):
        """:meta private:"""
        return self.input.value()

    def iter(self, iterable):
        """
        Iterable wrapper that automatically updates the progress bar while the provided
        iterable is iterated over. This is quite similar to how the console progress bar
        ``tqdm`` works: https://tqdm.github.io/

        For example::

            for i in piece.params['progress'].iter(range(10)):
                print(i)
                # this will automatically update the progress bar as the iteration goes on
                puzzle.process_events() # you may need to refresh the Puzzle to display changes

        :param iterable: an iterable to wrap
        :rtype: iterable
        """
        if hasattr(iterable, "__len__"):
            length = len(iterable)
        else:
            length = -1

        for i, value in enumerate(iterable):
            self.set_value(i / length)
            yield value
        self.set_value(1)


def wrap_setter(piece, setter):
    """
    We wrap the setter function such that it can be called without passing
    a reference to the Piece as the first argument

    :meta private:
    """
    if setter is not None:
        if "self" in inspect.signature(setter).parameters:

            def wrapper(value):
                return setter(piece, value)

            # Update the wrapper's function name, so that it shows up in profile traces correctly.
            new_name = f"wrap__{setter.__name__}"
            _snippets.update_function_name(wrapper, new_name)
        else:
            wrapper = setter
    else:
        wrapper = None
    return wrapper


def wrap_getter(piece, getter):
    """
    We wrap the getter function such that it can be called without passing
    a reference to the Piece as the first argument

    :meta private:
    """
    if getter is not None:
        if "self" in inspect.signature(getter).parameters:

            def wrapper():
                return getter(piece)

            # Update the wrapper's function name, so that it shows up in profile traces correctly.
            new_name = f"wrap__{getter.__name__}"
            _snippets.update_function_name(wrapper, new_name)
        else:
            wrapper = getter
    else:
        wrapper = None
    return wrapper


# The decorator syntax in Python is a little confusing
def base_param(piece, name, value, visible=True, format="{}"):
    """
    A decorator generator for registering a :class:`~puzzlepiece.param.BaseParam` in a Piece's
    :func:`~puzzlepiece.piece.Piece.define_params` method with a given **setter**.

    This will simply display the current value with no option to edit it.

    To register a param and mark a function as its setter, do this::

        @puzzlepiece.param.base_param(self, 'param_name', 0)
        def param_setter(value):
            print(self, value)

    To register a param without a setter, call this function to get a decorator, and then pass ``None`` to that to indicate
    that a setter doesn't exist::

        puzzlepiece.param.base_param(self, 'param_name', 0)(None)

    Some of the decorators here decorate getters, and some decorate setters, depending on what is the more sensible default
    -- a :func:`~puzzlepiece.param.readout` decorates a getter, as it is meant to display obtained values, and a
    :func:`~puzzlepiece.param.spinbox` decorates a setter, as it's meant to be an easy way to input and set values. If you
    need to also register the other function, use the :func:`puzzlepiece.param.BaseParam.set_getter`
    and :func:`puzzlepiece.param.BaseParam.set_setter` decorators::

        @puzzlepiece.param.base_param(self, 'position', 0)
        def position(value):
            self.sdk.set_position(value)

        @position.set_getter(self)
        def position():
            return self.sdk.get_position()

    It's also allowed to provide "self" as the first argument of the setter/getter method
    for added clarity, but since self exists locally within :func:`~puzzlepiece.piece.Piece.define_params`
    this is technically not required::

        @puzzlepiece.param.base_param(self, 'param_name', 0)
        def param_setter(self, value):
            print(self, value)

    :param piece: The :class:`~puzzle.piece.Piece` this param should be registered with. Usually `self`, as this method should
      be called from within :func:`puzzlepiece.piece.Piece.define_params`
    :param name: a unique (per Piece) name for the param
    :param value: default display value for the param. If there is a setter, the setter will not be called, and the stored value
      will remain None until the param is explicitly set (either through :func:`~puzzlepiece.param.BaseParam.set_value`, or
      pressing the set button.)
    :param visible: bool flag, determined if a GUI component will be shown for this param.
    :param format: Default format for displaying the param if a custom input is not defined, and in
      :func:`puzzplepiece.parse.format`. For example `{:.2f}`, see https://pyformat.info/ for further details.

    :returns: A decorator that can be applied to a setter function. The decorator returns the param object when called.
    """

    # The base_param function *creates and returns a decorator*,
    # it's just the way to enable passing parameters when decorating something
    def decorator(setter):
        wrapper = wrap_setter(piece, setter)

        # Register the param with the Piece
        piece.params[name] = BaseParam(
            name,
            value,
            setter=wrapper,
            getter=None,
            visible=visible,
            format=format,
            piece=piece,
        )

        # Return the newly created Param
        return piece.params[name]

    return decorator


def readout(piece, name, visible=True, format="{}", _type=None):
    """
    A decorator generator for registering a :class:`~puzzlepiece.param.BaseParam` in a Piece's
    :func:`~puzzlepiece.piece.Piece.define_params` method with a given **getter**.

    This will simply display the current value with no option to edit it.

    See :func:`~puzzlepiece.param.base_param` for more details.
    """

    def decorator(getter):
        wrapper = wrap_getter(piece, getter)
        piece.params[name] = BaseParam(
            name,
            None,
            setter=None,
            getter=wrapper,
            visible=visible,
            format=format,
            _type=_type,
            piece=piece,
        )
        return piece.params[name]

    return decorator


def spinbox(piece, name, value, v_min=-1e9, v_max=1e9, visible=True, v_step=1):
    """
    A decorator generator for registering a :class:`~puzzlepiece.param.ParamInt` or :class:`~puzzlepiece.param.ParamFloat`
    in a Piece's :func:`~puzzlepiece.piece.Piece.define_params` method with a given **setter**.

    The type of param registered depends on whether the ``value`` given is an int of a float.

    This will display a Qt spinbox - a numeric input box.

    See :func:`~puzzlepiece.param.base_param` for more details.

    :param v_min: The minimum value accepted by the spinbox.
    :param v_max: The maximum value accepted by the spinbox.
    :param v_step: The step change when spinbox buttons are used.
    """

    def decorator(setter):
        wrapper = wrap_setter(piece, setter)

        if isinstance(value, int):
            piece.params[name] = ParamInt(
                name,
                value,
                int(v_min),
                int(v_max),
                setter=wrapper,
                getter=None,
                visible=visible,
                v_step=int(v_step),
                piece=piece,
            )
        else:
            piece.params[name] = ParamFloat(
                name, value, v_min, v_max, wrapper, None, visible, v_step, piece=piece
            )
        return piece.params[name]

    return decorator


def slider(piece, name, value, v_min=0, v_max=1, visible=True, v_step=0.05):
    """
    A decorator generator for registering a :class:`~puzzlepiece.param.ParamSlider`
    in a Piece's :func:`~puzzlepiece.piece.Piece.define_params` method with a given **setter**.

    This will display a slider with the specified properties and a label.
    It will be an int or a float slider depending on the type of the values provided here.

    See :func:`~puzzlepiece.param.base_param` for more details.
    """

    def decorator(setter):
        wrapper = wrap_setter(piece, setter)
        piece.params[name] = ParamSlider(
            name, value, v_min, v_max, wrapper, None, visible, v_step, piece=piece
        )
        return piece.params[name]

    return decorator


def text(piece, name, value, visible=True):
    """
    A decorator generator for registering a :class:`~puzzlepiece.param.ParamText`
    in a Piece's :func:`~puzzlepiece.piece.Piece.define_params` method with a given **setter**.

    This will display a single line textbox.

    See :func:`~puzzlepiece.param.base_param` for more details.
    """

    def decorator(setter):
        wrapper = wrap_setter(piece, setter)
        piece.params[name] = ParamText(name, value, wrapper, None, visible, piece=piece)
        return piece.params[name]

    return decorator


def checkbox(piece, name, value, visible=True):
    """
    A decorator generator for registering a :class:`~puzzlepiece.param.ParamCheckbox`
    in a Piece's :func:`~puzzlepiece.piece.Piece.define_params` method with a given **setter**.

    This will display a checkbox as the input, and the param takes the values 0 and 1 for
    unchecked and checked states.

    This param runs puzzlepiece.param.Param.set_value() automatically when the checkbox is pressed,
    so an additional setter button is not displayed.

    See :func:`~puzzlepiece.param.base_param` for more details.
    """

    def decorator(setter):
        wrapper = wrap_setter(piece, setter)
        piece.params[name] = ParamCheckbox(
            name, value, wrapper, None, visible, piece=piece
        )
        return piece.params[name]

    return decorator


def array(piece, name, visible=True):
    """
    A decorator generator for registering a :class:`~puzzlepiece.param.ParamArray`
    in a Piece's :func:`~puzzlepiece.piece.Piece.define_params` method with a given **getter**.

    This will display the shape of the stored array with no option to edit it and an indicator
    showing when the value changes.

    See :func:`~puzzlepiece.param.base_param` for more details.
    """

    def decorator(getter):
        wrapper = wrap_getter(piece, getter)
        piece.params[name] = ParamArray(
            name, None, setter=None, getter=wrapper, visible=visible, piece=piece
        )
        return piece.params[name]

    return decorator


def dropdown(piece, name, value, visible=True):
    """
    A decorator generator for registering a :class:`~puzzlepiece.param.ParamDropdown`
    in a Piece's :func:`~puzzlepiece.piece.Piece.define_params`.

    It should decorate a function that returns a list of default values to populate the dropdown,
    for example::

        @puzzlepiece.param.dropdown(self, 'param_name', '')
        def param_values(self, value):
            return self.sdk.discover_devices()

    It can also be used with a set list of defaults, or with no defaults at all::

        puzzlepiece.param.dropdown(self, 'param_name', 'one')(['one', 'two', 'three'])
        puzzlepiece.param.dropdown(self, 'param_name', 'four')(None)

    Setters and getters can then be added using :func:`puzzlepiece.param.BaseParam.set_getter`
    and :func:`puzzlepiece.param.BaseParam.set_setter` decorators::

        @puzzlepiece.param.dropdown(self, 'serial_number', '')
        def serial_number(self, value):
            return self.sdk.discover_devices()

        @serial_number.set_getter(self)
        def serial_number(self):
            return self.sdk.get_serial()

        @serial_number.set_setter(self)
        def serial_number(self, value):
            return self.sdk.set_serial(value)

    The returned param displays a dropdown and stores a string. The user can edit the dropdown's
    text field directly, and pressing enter will add the current value to the dropdown.

    The default param value provided here as `value` will either be selected from the dropdown if
    available, or inserted into the text field as if a user typed it otherwise.
    """

    def decorator(values):
        if callable(values):
            # `values` can be a function that returns a list of values
            values = values(piece)
        piece.params[name] = ParamDropdown(
            name, value, values, None, None, visible, piece=piece
        )
        return piece.params[name]

    return decorator


def progress(piece, name, visible=True):
    """
    A decorator generator for registering a :class:`~puzzlepiece.param.ParamProgress` in a Piece's
    :func:`~puzzlepiece.piece.Piece.define_params` method with a given **getter**.

    This will display the current progress value on a scale of 0 to 1 with no option to edit it.

    See :func:`~puzzlepiece.param.base_param` for more details.
    """

    def decorator(getter):
        wrapper = wrap_getter(piece, getter)
        piece.params[name] = ParamProgress(
            name, None, setter=None, getter=wrapper, visible=visible, piece=piece
        )
        return piece.params[name]

    return decorator

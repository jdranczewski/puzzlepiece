import puzzlepiece as pzp
from pyqtgraph.Qt import QtWidgets

class TParamPiece(pzp.Piece):
    def define_params(self):
        pzp.param.base_param(self, 'base_param', 0)(None)

        self._setter_param_value = None
        @pzp.param.base_param(self, 'setter_param', 1)
        def setter_param(self, value):
            self._setter_param_value = value

        @pzp.param.base_param(self, 'setter_return_param', 0)
        def setter_param(self, value):
            return value + 1

        @pzp.param.readout(self, 'getter_param', _type=int)
        def getter_param(self):
            return 1

        self._setter_getter_param_value = 0
        @pzp.param.base_param(self, 'setter_getter_param', 0)
        def setter_getter_param(self, value):
            self._setter_getter_param_value = value
        
        @setter_getter_param.set_getter(self)
        def setter_getter_param_getter(self):
            return self._setter_getter_param_value + 1
        
        self._setter_getter_return_param_value = 0
        @pzp.param.base_param(self, 'setter_getter_return_param', 0)
        def setter_getter_return_param(self, value):
            self._setter_getter_return_param_value = value
            return value
        
        @setter_getter_return_param.set_getter(self)
        def setter_getter_return_param_getter(self):
            return self._setter_getter_return_param_value + 1

        @pzp.param.base_param(self, 'error_param', 0)
        def error_param(self, value):
            # return 0
            raise Exception('Setter exception')
        
        @error_param.set_getter(self)
        def error_param_getter(self):
            # return 0
            raise Exception('Getter exception')

        @pzp.param.checkbox(self, 'error_checkbox', 0)
        def error_param(self, value):
            raise Exception('Setter exception')
        

def test_base_param(qtbot, qapp):
    puzzle = pzp.Puzzle(qapp, "Test params")
    puzzle.add_piece("test", TParamPiece(puzzle), 0, 0)
    puzzle.show()

    count = [0]
    def count_calls(count=count):
        count[0] += 1
    puzzle['test'].params['base_param'].changed.connect(count_calls)

    assert count[0] == 0
    assert puzzle['test'].params['base_param'].value == 0
    assert puzzle['test'].params['base_param'].get_value() == 0
    assert puzzle['test'].params['base_param'].input.text() == '0'
    assert count[0] == 0

    puzzle['test'].params['base_param'].set_value(1)
    assert count[0] == 1
    assert puzzle['test'].params['base_param'].value == 1
    assert puzzle['test'].params['base_param'].get_value() == 1
    assert puzzle['test'].params['base_param'].input.text() == '1'

def test_setter_param(qtbot, qapp):
    puzzle = pzp.Puzzle(qapp, "Test params")
    puzzle.add_piece("test", TParamPiece(puzzle), 0, 0)
    puzzle.show()

    count = [0]
    def count_calls(count=count):
        count[0] += 1
    puzzle['test'].params['setter_param'].changed.connect(count_calls)

    assert count[0] == 0
    assert puzzle['test']._setter_param_value is None
    assert puzzle['test'].params['setter_param'].value is None
    assert puzzle['test'].params['setter_param'].get_value() is None
    assert puzzle['test'].params['setter_param'].input.text() == '1'
    assert count[0] == 0

    puzzle['test'].params['setter_param'].set_value()
    assert count[0] == 1
    assert puzzle['test']._setter_param_value == 1
    assert puzzle['test'].params['setter_param'].value == 1
    assert puzzle['test'].params['setter_param'].get_value() == 1
    assert puzzle['test'].params['setter_param'].input.text() == '1'

    puzzle['test'].params['setter_param'].set_value(2)
    assert count[0] == 2
    assert puzzle['test']._setter_param_value == 2
    assert puzzle['test'].params['setter_param'].value == 2
    assert puzzle['test'].params['setter_param'].get_value() == 2
    assert puzzle['test'].params['setter_param'].input.text() == '2'

    puzzle['test'].params['setter_param']._input_set_value(3)
    assert count[0] == 2
    assert puzzle['test'].params['setter_param'].input.text() == '3'
    puzzle['test'].params['setter_param']._set_button.click()
    assert count[0] == 3
    assert puzzle['test']._setter_param_value == 3
    assert puzzle['test'].params['setter_param'].value == 3
    assert puzzle['test'].params['setter_param'].get_value() == 3
    assert puzzle['test'].params['setter_param'].input.text() == '3'

def test_setter_return_param(qtbot, qapp):
    puzzle = pzp.Puzzle(qapp, "Test params")
    puzzle.add_piece("test", TParamPiece(puzzle), 0, 0)
    puzzle.show()

    count = [0]
    def count_calls(count=count):
        count[0] += 1
    puzzle['test'].params['setter_return_param'].changed.connect(count_calls)

    assert count[0] == 0
    assert puzzle['test'].params['setter_return_param'].value is None
    assert puzzle['test'].params['setter_return_param'].get_value() is None
    assert puzzle['test'].params['setter_return_param'].input.text() == '0'
    assert count[0] == 0

    puzzle['test'].params['setter_return_param'].set_value()
    assert count[0] == 1
    assert puzzle['test'].params['setter_return_param'].value == 1
    assert puzzle['test'].params['setter_return_param'].get_value() == 1
    assert puzzle['test'].params['setter_return_param'].input.text() == '1'

    puzzle['test'].params['setter_return_param'].set_value(2)
    assert count[0] == 2
    assert puzzle['test'].params['setter_return_param'].value == 3
    assert puzzle['test'].params['setter_return_param'].get_value() == 3
    assert puzzle['test'].params['setter_return_param'].input.text() == '3'

    puzzle['test'].params['setter_return_param']._input_set_value(4)
    assert count[0] == 2
    assert puzzle['test'].params['setter_return_param'].input.text() == '4'
    puzzle['test'].params['setter_return_param']._set_button.click()
    assert count[0] == 3
    assert puzzle['test'].params['setter_return_param'].value == 5
    assert puzzle['test'].params['setter_return_param'].get_value() == 5
    assert puzzle['test'].params['setter_return_param'].input.text() == '5'

def test_getter_param(qtbot, qapp):
    puzzle = pzp.Puzzle(qapp, "Test params")
    puzzle.add_piece("test", TParamPiece(puzzle), 0, 0)
    puzzle.show()

    count = [0]
    def count_calls(count=count):
        count[0] += 1
    puzzle['test'].params['getter_param'].changed.connect(count_calls)

    assert count[0] == 0
    assert puzzle['test'].params['getter_param'].value is None
    assert puzzle['test'].params['getter_param'].input.text() == ''
    assert count[0] == 0

    puzzle['test'].params['getter_param'].get_value()
    assert count[0] == 1
    assert puzzle['test'].params['getter_param'].value == 1
    assert puzzle['test'].params['getter_param'].input.text() == '1'

    puzzle['test'].params['getter_param'].get_value()
    assert count[0] == 2
    assert puzzle['test'].params['getter_param'].value == 1
    assert puzzle['test'].params['getter_param'].input.text() == '1'

    # This should not in general emit the signal - there's no setter, so any changes
    # to the input field would trigger the signal by themselves. If we call set_value
    # with no arguments it will have no impact on the current value
    puzzle['test'].params['getter_param'].set_value()
    assert count[0] == 2
    assert puzzle['test'].params['getter_param'].value == 1
    assert puzzle['test'].params['getter_param'].input.text() == '1'

    # In contrast, changing the value of the input should in principle emit the signal
    puzzle['test'].params['getter_param']._input_set_value(2)
    assert count[0] == 3
    assert puzzle['test'].params['getter_param'].value == 2
    assert puzzle['test'].params['getter_param'].input.text() == '2'

    puzzle['test'].params['getter_param'].set_value(3)
    assert count[0] == 4
    assert puzzle['test'].params['getter_param'].value == 3
    assert puzzle['test'].params['getter_param'].input.text() == '3'

    puzzle['test'].params['getter_param'].get_value()
    assert count[0] == 5
    assert puzzle['test'].params['getter_param'].value == 1
    assert puzzle['test'].params['getter_param'].input.text() == '1'


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    puzzle = pzp.Puzzle(app, "Test params")
    puzzle.add_piece("test", TParamPiece(puzzle), 0, 0)
    from puzzlepiece.pieces import script
    puzzle.add_piece("script", script.Piece(puzzle), 0, 1)
    puzzle.show()
    app.exec()
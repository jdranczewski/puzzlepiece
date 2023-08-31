import puzzlepiece as pzp
from pyqtgraph.Qt import QtWidgets

class Piece(pzp.Piece):
    def define_params(self):
        pzp.param.text(self, "params", "")(None)

        @pzp.param.text(self, "value", "file")
        def set_param(self, value):
            param_name = self.params['params'].get_value()
            if len(param_name):
                params = pzp.parse.parse_params(param_name, self.puzzle)
                for param in params:
                    param.set_value(value)
            return value
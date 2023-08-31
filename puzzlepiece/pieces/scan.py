import puzzlepiece as pzp
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets
import numpy as np
import time

class Piece(pzp.Piece):
    def __init__(self, puzzle):
        super().__init__(puzzle)

    def define_params(self):
        pzp.param.text(self, "params", "laser:power")(None)
        pzp.param.text(self, "action", "run:lightfield:Acquire")(None)
        pzp.param.text(self, "break", "lightfield:saturated")(None)

        pzp.param.spinbox(self, "start", 8)(None)
        pzp.param.spinbox(self, "end", 60)(None)
        pzp.param.spinbox(self, "step", 2)(None)
        pzp.param.spinbox(self, "finish", 0)(None)

    def param_layout(self, wrap=1):
        return super().param_layout(wrap)

    def define_actions(self):
        @pzp.action.define(self, "Scan")
        def scan(self):
            values = np.arange(self.params['start'].get_value(), self.params['end'].get_value(), self.params['step'].get_value())
            params = pzp.parse.parse_params(self.params['params'].get_value(), self.puzzle)
            break_param = pzp.parse.parse_params(self.params['break'].get_value(), self.puzzle)[0] if len(self.params['break'].get_value()) else None
            command = self.params['action'].get_value()
            self.progress_bar.setMaximum(len(values))
            self.stop = False
        
            for i, value in enumerate(values):
                for param in params:
                    param.set_value(value)
                time.sleep(0.05)
                pzp.parse.run(command, self.puzzle)
                self.progress_bar.setValue(i+1)
                self.puzzle.process_events()
                if self.stop or (break_param is not None and break_param.get_value()):
                    break
            for param in params:
                param.set_value(self.params['finish'].get_value())
            # Maybe plot it?
    
    def custom_layout(self):
        layout = QtWidgets.QVBoxLayout()

        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setMaximum(1)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        return layout

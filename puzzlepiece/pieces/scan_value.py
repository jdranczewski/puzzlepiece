import puzzlepiece as pzp
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets
import numpy as np
import time

class Piece(pzp.Piece):
    def __init__(self, puzzle):
        super().__init__(puzzle, custom_horizontal=True)
        self.x = []
        self.y = []
        self.stop = False

    def define_params(self):
        pzp.param.text(self, "params", "")(None)
        pzp.param.text(self, "obtain", "")(None)

        pzp.param.spinbox(self, "start", 0.)(None)
        pzp.param.spinbox(self, "end", 11.)(None)
        pzp.param.spinbox(self, "step", 1.)(None)
        pzp.param.spinbox(self, "finish", 0.)(None)
        pzp.param.text(self, "filename", "")(None)

    def param_layout(self, wrap=1):
        return super().param_layout(wrap)

    def define_actions(self):
        @pzp.action.define(self, "Scan")
        def scan(self):
            values = np.arange(self.params['start'].get_value(), self.params['end'].get_value(), self.params['step'].get_value())
            params = pzp.parse.parse_params(self.params['params'].get_value(), self.puzzle)
            obtain = pzp.parse.parse_params(self.params['obtain'].get_value(), self.puzzle)[0]
            self.progress_bar.setMaximum(len(values))

            self.x = []
            self.y = []
            self.stop = False
            for i, value in enumerate(values):
                for param in params:
                    param.set_value(value)
                self.x.append(value)
                time.sleep(0.05)
                self.y.append(obtain.get_value())
                self.progress_bar.setValue(i+1)
                self.plot_line.setData(self.x, self.y)
                self.puzzle.process_events()

                if self.stop:
                    break
            for param in params:
                param.set_value(self.params['finish'].get_value())

        @pzp.action.define(self, "Save")
        def save(self):
            out = np.stack((self.x, self.y)).T
            filename = self.params['filename'].get_value()
            filename = pzp.parse.format(filename, self.puzzle)
            np.savetxt(filename, out, delimiter=',')

        @pzp.action.define(self, "Name")
        def choose_file(self):
            fname = str(QtWidgets.QFileDialog.getSaveFileName(self, "Save file...")[0])
            self.params['filename'].set_value(fname)

    
    def custom_layout(self):
        layout = QtWidgets.QVBoxLayout()

        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setMaximum(1)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.pw = pg.PlotWidget()
        layout.addWidget(self.pw)
        self.plot = self.pw.getPlotItem()
        self.plot_line = self.plot.plot([0], [0], symbol='o', symbolSize=3)

        return layout

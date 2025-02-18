import puzzlepiece as pzp
from pyqtgraph.Qt import QtWidgets
import pyqtgraph as pg
import time
import numpy as np


class Piece(pzp.Piece):
    def __init__(self, puzzle):
        super().__init__(puzzle, custom_horizontal=True)
        self.running = False
        self.times = []
        self.data = []

    def define_params(self):
        pzp.param.text(self, "param", "plotter:max")(None)
        pzp.param.spinbox(self, "max", 1000)(None)

        @pzp.param.spinbox(self, "sleep", 0.1)
        def set_sleep(value):
            self.timer.sleep = value

    def define_actions(self):
        @pzp.action.define(self, "Clear")
        def clear():
            self.times = []
            self.data = []

    def add_point(self, value):
        self.data.append(value)
        self.times.append(time.time())

        max_l = self["max"].get_value()
        self.times = self.times[-max_l:]
        self.data = self.data[-max_l:]

        if len(self.data) > 1:
            td = np.array(self.times) - self.times[0]
            if np.amax(td) > 60:
                td /= 60
            self.plot_line.setData(td, self.data)

    def get_value(self):
        # The task that happens in the side-thread should be simple and not touch the Widgets or
        # the main thread too much - it can take a while though, like a lengthy data acquisition
        param = pzp.parse.parse_params(self["param"].get_value(), self.puzzle)[0]
        return param.get_value()

    def custom_layout(self):
        layout = QtWidgets.QVBoxLayout()

        # The thread runs self.get_value repeatedly, which returns a value...
        self.timer = pzp.threads.PuzzleTimer(
            "Live", self.puzzle, self.get_value, self["sleep"].get_value()
        )
        # ... this value is then passed to self.add_point through a Signal
        self.timer.returned.connect(self.add_point)

        layout.addWidget(self.timer)
        self["sleep"].set_value()  # Set the sleep value to the default one

        self.pw = pg.PlotWidget()
        layout.addWidget(self.pw)
        self.plot = self.pw.getPlotItem()
        self.plot_line = self.plot.plot(symbol="o", symbolSize=3)

        return layout

    def call_stop(self):
        self.timer.stop()

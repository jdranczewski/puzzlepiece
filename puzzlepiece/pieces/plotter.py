import puzzlepiece as pzp
from pyqtgraph.Qt import QtCore, QtWidgets
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
        pzp.param.spinbox(self, "max", 100)(None)

        @pzp.param.spinbox(self, "sleep", 0.1)
        def set_sleep(self, value):
            self.timer.sleep = value

    def define_actions(self):
        @pzp.action.define(self, "Clear")
        def clear(self):
            self.times = []
            self.data = []
    
    def add_point(self, value):
        self.data.append(value)
        self.times.append(time.time())

        max_l = self.params['max'].get_value()
        self.times = self.times[-max_l:]
        self.data = self.data[-max_l:]

        if len(self.data) > 1:
            td = np.array(self.times)-self.times[0]
            if np.amax(td) > 60:
                td /= 60
            self.plot_line.setData(td, self.data)

    def get_value(self):
        # We would generally prefer the threaded function to touch Widgets and GUI stuff as
        # little as possible! If it tries to modify something, and then the user presses
        # a button in the meantime, that's usually  b a d.

        # So instead we get the value in the thread (this is the time intensive part)
        # and pass it back to the main thread through a Signal. The plotting then
        # happens in the main thread and all is likely well.

        param = pzp.parse.parse_params(self.params['param'].get_value(), self.puzzle)[0]
        self.new_value_available.emit(param.get_value())

    new_value_available = QtCore.Signal(float)
    def custom_layout(self):
        layout = QtWidgets.QVBoxLayout()

        # The thread runs self.get_value repeatedly, which then runs self.add_point in the main thread
        # through a Signal
        self.timer = pzp.threads.PuzzleTimer('Live', self.puzzle, self.get_value, self.params['sleep'].get_value())
        self.new_value_available.connect(self.add_point)

        layout.addWidget(self.timer)
        self.params['sleep'].set_value() # Set the sleep value to the default one

        self.pw = pg.PlotWidget()
        layout.addWidget(self.pw)
        self.plot = self.pw.getPlotItem()
        self.plot_line = self.plot.plot([0], [0], symbol='o', symbolSize=3)

        return layout
    
    def call_stop(self):
        self.timer.stop()
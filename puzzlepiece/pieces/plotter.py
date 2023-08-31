import puzzlepiece as pzp
from pyqtgraph.Qt import QtCore, QtWidgets
import pyqtgraph as pg
import time
import numpy as np

class Worker(QtCore.QObject):
    finished = QtCore.Signal()
    update = QtCore.Signal(float)

    def __init__(self, param, sleep):
        self.param = param
        self.sleep = sleep
        self.running = True
        super().__init__()

    def run(self):
        while self.running:
            value = float(self.param.get_value())
            self.update.emit(value)
            time.sleep(self.sleep.get_value())
        self.finished.emit()


class Piece(pzp.Piece):
    def __init__(self, puzzle):
        super().__init__(puzzle, custom_horizontal=True)
        self.running = False
        self.times = []
        self.data = []

    def define_params(self):
        pzp.param.text(self, "param", "plotter:max")(None)
        pzp.param.spinbox(self, "max", 100)(None)
        pzp.param.spinbox(self, "sleep", 0.1)(None)

    def define_actions(self):
        @pzp.action.define(self, "Start")
        def start(self):
            if not self.running:
                sleep = self.params['sleep']
                # if hasattr(self, '_thread') and not self._thread.isFinished():
                #     stop()
                
                param = pzp.parse.parse_params(self.params['param'].get_value(), self.puzzle)[0]

                self._thread = QtCore.QThread()
                self.worker = Worker(param, sleep)
                self.worker.moveToThread(self._thread)

                self._thread.started.connect(self.worker.run)
                self.worker.finished.connect(self._thread.quit)
                self.worker.finished.connect(self.worker.deleteLater)
                self._thread.finished.connect(self._thread.deleteLater)
                self.worker.update.connect(self.add_point)

                self._thread.start()
                self.running = True

        @pzp.action.define(self, "Stop")
        def stop(self):
            if self.running:
                self.worker.running = False
                self.running = False
            # self._thread.wait()

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

    def custom_layout(self):
        layout = QtWidgets.QVBoxLayout()

        self.pw = pg.PlotWidget()
        layout.addWidget(self.pw)
        self.plot = self.pw.getPlotItem()
        self.plot_line = self.plot.plot([0], [0], symbol='o', symbolSize=3)

        return layout
    
    def call_stop(self):
        self.actions['Stop']()
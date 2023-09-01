import puzzlepiece as pzp
from pyqtgraph.Qt import QtWidgets
import random

class Piece(pzp.Piece):
    def __init__(self, puzzle):
        super().__init__(puzzle)

    def define_params(self):
        # This defines a parameter that doesn't need a setter
        pzp.param.spinbox(self, "min", 0)(None)

        pzp.param.spinbox(self, "max", 10)(None)

        @pzp.param.spinbox(self, "seed", 0)
        def seed(self, value):
            random.seed(value)
            return value
        
    def define_readouts(self):
        @pzp.param.readout(self, "Random number")
        def random_number(self):
            return random.randint(self.params['min'].get_value(),
                                  self.params['max'].get_value())
     

    def define_actions(self):
        @pzp.action.define(self, "Dialog")
        def print_something(self):
            pzp.parse.run('prompt:In a range between {random_number:min} and {random_number:max}, your number is {random_number:Random number}',
                          self.puzzle)
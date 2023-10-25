import puzzlepiece as pzp
import random

class Piece(pzp.Piece):
    # We define a Piece object to contain the random number generator

    # We give it 'params' within this function (these will appear as inputs/value displays)
    def define_params(self):
        # Some params don't need setters, they're just variables that impact other things.
        # In that case we pass None to the defining decorator.
        pzp.param.spinbox(self, "min", 0)(None)
        pzp.param.spinbox(self, "max", 10)(None)

        # Some params have a 'setter' function, which sets a value, like a laser's power.
        # In that case we make the function (which takes a value) and decorate it with
        # a param-defining decorator
        @pzp.param.spinbox(self, "seed", 0)
        def seed(self, value):
            random.seed(value)
        
        # Some params have a 'getter' function, which returns a value, like a powermeter's reading
        # In that case we make the function (which returns a value) and decorate it with
        # a readout-param-defining decorator
        @pzp.param.readout(self, "number")
        def random_number(self):
            return random.randint(self.params['min'].get_value(),
                                  self.params['max'].get_value())
     
    # We give it 'actions' within this function (these will appear as buttons)
    def define_actions(self):
        # Sometimes an action is needed, like homing a moving stage
        # In that case we make the function (which performs the action) and decorate it with
        # an action-defining decorator
        @pzp.action.define(self, "Dialog")
        def print_something(self):
            pzp.parse.run('prompt:In a range between {random:min} and {random:max}, your number is {random:number}',
                          self.puzzle)
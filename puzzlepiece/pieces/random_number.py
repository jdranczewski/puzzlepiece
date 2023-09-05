import puzzlepiece as pzp
import random

class Piece(pzp.Piece):
    def define_params(self):
        # Some params don't need setters, they're just variables that impact other things
        pzp.param.spinbox(self, "min", 0)(None)
        pzp.param.spinbox(self, "max", 10)(None)

        # Some params have a 'setter' function, which sets a value, like a laser's power
        @pzp.param.spinbox(self, "seed", 0)
        def seed(self, value):
            random.seed(value)
        
        # Some params have a 'getter' function, which returns a value, like a powermeter's reading
        @pzp.param.readout(self, "number")
        def random_number(self):
            return random.randint(self.params['min'].get_value(),
                                  self.params['max'].get_value())
     

    def define_actions(self):
        # Sometimes an action is needed, like homing a moving stage
        @pzp.action.define(self, "Dialog")
        def print_something(self):
            pzp.parse.run('prompt:In a range between {random:min} and {random:max}, your number is {random:number}',
                          self.puzzle)
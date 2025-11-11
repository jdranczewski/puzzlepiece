import puzzlepiece as pzp
import numpy as np


class Piece(pzp.Piece):
    """
    Scan a param value and perform an action for each (run a script for example).
    """

    param_wrap = 1

    def __init__(self, puzzle):
        super().__init__(puzzle)

    def define_params(self):
        pzp.param.text(self, "params", "")(None)
        pzp.param.text(self, "action", "")(None)
        pzp.param.text(self, "break", "")(None)

        pzp.param.spinbox(self, "start", 0.0)(None)
        pzp.param.spinbox(self, "end", 25.1)(None)
        pzp.param.spinbox(self, "step", 1.0)(None)
        pzp.param.spinbox(self, "finish", 0.0)(None)

        pzp.param.progress(self, "progress")(None)

    def define_actions(self):
        @pzp.action.define(self, "Scan")
        def scan(self):
            # Create the list of values to scan
            values = np.arange(
                self["start"].get_value(),
                self["end"].get_value(),
                self["step"].get_value(),
            )
            # List of params to set
            params = pzp.parse.parse_params(self["params"].get_value(), self.puzzle)
            # A break param will stop the loop if it's True
            break_param = (
                pzp.parse.parse_params(self["break"].get_value(), self.puzzle)[0]
                if len(self["break"].get_value())
                else None
            )
            # The command to run each iteration
            command = self["action"].get_value()

            self.stop = False
            for i, value in enumerate(self["progress"].iter(values)):
                for param in params:
                    param.set_value(value)
                pzp.parse.run(command, self.puzzle)
                self.puzzle.process_events()
                if self.stop or (break_param is not None and break_param.get_value()):
                    break
            for param in params:
                param.set_value(self["finish"].get_value())


if __name__ == "__main__":
    # If running this file directly, make a Puzzle, add our Piece, and display it
    app = pzp.QApp()
    puzzle = pzp.Puzzle()
    puzzle.add_piece(
        "scan",
        Piece,
        0,
        0,
        param_defaults={
            "params": "scan:finish",
            "end": "5.1",
            "action": "prompt:Hello, {scan:finish}",
        },
    )
    puzzle.show()
    app.exec()

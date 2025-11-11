import puzzlepiece as pzp


class Piece(pzp.Piece):
    """
    This Piece lets you set other params with its textbox.
    Can be useful to get a wider textbox input.
    """

    def define_params(self):
        pzp.param.text(self, "params", "")(None)

        @pzp.param.text(self, "value", "file")
        def set_param(value):
            param_name = self["params"].get_value()
            if len(param_name):
                # Get the params specified as "piece_name:param_name, piece_name:param_name"
                params = pzp.parse.parse_params(param_name, self.puzzle)
                # Iterate over them and set their values to the one given by
                # the user to this setter
                for param in params:
                    param.set_value(value)
            return value


if __name__ == "__main__":
    # If running this file directly, make a Puzzle, add our Piece, and display it
    app = pzp.QApp()
    puzzle = pzp.Puzzle()
    puzzle.add_piece("setter", Piece, 0, 0)
    puzzle.show()
    app.exec()

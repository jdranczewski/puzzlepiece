# Import the automation framework
import puzzlepiece as pzp
# Import the random number generator Piece
from puzzlepiece.pieces import random_number
from pyqtgraph.Qt import QtWidgets

# Create a Qt app to contain the whole thing
app = QtWidgets.QApplication([])

# Create a Puzzle
puzzle = pzp.Puzzle(app, "Basic example", debug=True)

# Cerate a Piece and add it to the Puzzle
piece = random_number.Piece(puzzle)
puzzle.add_piece("random", piece, 0, 0)

# Show the Puzzle window
puzzle.show()

# Execute the application
# (this enters the Qt loop and will only exit once the window is closed)
app.exec()

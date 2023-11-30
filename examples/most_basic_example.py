# Import the automation framework
import puzzlepiece as pzp
# Import the random number generator Piece
from puzzlepiece.pieces import random_number, plotter

# Create a Qt app to contain the whole thing
app = pzp.QApp([])

# Create a Puzzle
puzzle = pzp.Puzzle(app, "Basic example", debug=True)

# Add Pieces to the Puzzle
puzzle.add_piece("random", random_number.Piece, 0, 0)
puzzle.add_piece("plotter", plotter.Piece, 0, 1)

# Show the Puzzle window
puzzle.show()

# Execute the application
# (this enters the Qt loop and will only exit once the window is closed)
app.exec()

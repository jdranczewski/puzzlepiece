import puzzlepiece as pzp
from puzzlepiece.pieces import random_number, plotter, scan_value, script
from pyqtgraph.Qt import QtWidgets

def main():
    # Define the containing app
    app = QtWidgets.QApplication([])

    # Create a Puzzle
    window = pzp.Puzzle(app, "Basic example", debug=True)

    # Add Pieces
    window.add_piece("random", random_number.Piece(window), 0, 0)
    folder = window.add_folder(0, 1)
    folder.add_piece("plotter", plotter.Piece(window))
    folder.add_piece("scan_value", scan_value.Piece(window))
    folder.add_piece("script", script.Piece(window))

    # Run a setup script
    window.run("""
set:plotter:param:random:number
set:scan_value:params:random:max
set:scan_value:obtain:random:number
set:scan_value:end:100
set:scan_value:finish:10
""")

    # Show the app
    window.show()
    app.exec()

if __name__ == "__main__":
    main()
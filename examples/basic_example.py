import puzzlepiece as pzp
from puzzlepiece.pieces import random_number, plotter, scan_value, script

def main():
    # Define the containing app
    app = pzp.QApp([])

    # Create a Puzzle
    puzzle = pzp.Puzzle(app, "Basic example", debug=True)

    # Add Pieces
    puzzle.add_piece("random", random_number.Piece, 0, 0)
    folder = puzzle.add_folder(0, 1)
    folder.add_piece("plotter", plotter.Piece)
    folder.add_piece("scan_value", scan_value.Piece)
    folder.add_piece("script", script.Piece)

    # Run a setup script
    puzzle.run("""
set:plotter:param:random:number
set:scan_value:params:random:max
set:scan_value:obtain:random:number
set:scan_value:end:100
set:scan_value:finish:10
""")

    # Show the app
    puzzle.show()
    app.exec()

if __name__ == "__main__":
    main()
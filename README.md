# Puzzlepiece
**Puzzlepiece is a GUI-forward Python framework for automating experimental setups.** It focuses on abstracting communication with a piece of hardware into **standard inputs, outputs, and actions**. It then automatically **generates GUI components** for them, minimising the need for boilerplate code. Puzzlepiece allows the user to bring diverse controls into a single, consolidated application, and automate their interaction or experiment using a unified API, either by making custom Pieces, or through a built-in script language,
or with Interactive Python.

Check out the [`examples`](https://github.com/jdranczewski/puzzlepiece/tree/release/examples) folder for how to make an application (a Puzzle), and [`puzzlepiece/pieces/random_number.py`](https://github.com/jdranczewski/puzzlepiece/blob/release/puzzlepiece/pieces/random_number.py) for a simple example Piece. A Piece is a module that does a particular job (talks to a laser, scans a value, ...), and multiple of these brought together make up a Puzzle.

You can install puzzlepiece using pip:
```
pip install puzzlepiece
```

See the documentation at https://puzzlepiece.readthedocs.io/ for examples of how to get started.

Created by Jakub Dranczewski as part of PhD work supported by the EU ITN EID project CORAL (GA no. 859841).

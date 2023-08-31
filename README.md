# Puzzlepiece
**Puzzlepiece is a GUI-forward Python framework for automating experimental setups.** It focuses on abstracting communication with a piece of hardware into **standard inputs, outputs, and actions**. It then automatically **generates GUI components** for them, minimising the need for boilerplate code. Puzzlepiece allows the user to bring diverse controls into a single, consolidated application, and automate their interaction or experiment using a unified API, either through a built-in script language, or Interactive Python.

Check out the [`examples`](examples/) folder for how to make an application (a Puzzle), and [`puzzlepiece/pieces/random_number.py`](puzzlepiece/pieces/random_number.py) for a simple example Piece.

More documentation coming soon! Rudimentary docs can currently be compiled from the `docs` folder, will build to readthedocs asap. Also PyPI coming soon.

Currently the main requirement is `pyqtgraph`, and the code accesses whichever Python Qt bindings are installed _through_ `pyqtgraph`. Eventually the code is likely to be migrated to `QtPy`.

Created by Jakub Dranczewski as part of PhD work supported by the EU ITN EID project CORAL (GA no. 859841).

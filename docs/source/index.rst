.. puzzlepiece documentation master file, created by
   sphinx-quickstart on Tue Apr 25 11:52:22 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to the puzzlepiece documentation!
=========================================

**Puzzlepiece is a GUI-forward Python framework for automating experimental setups.** It focuses on abstracting communication
with a piece of hardware into **standard inputs, outputs, and actions**. It then automatically **generates GUI components** for them,
minimising the need for boilerplate code. Puzzlepiece allows the user to bring diverse controls into a single, consolidated application,
and automate their interaction or experiment using a unified API, either through a built-in script language, or Interactive Python.

You can install puzzlepiece using pip::

   pip install puzzlepiece

Some examples are located on GitHub: `how to construct an app <https://github.com/jdranczewski/puzzlepiece/tree/main/examples>`_
or `how to code a Piece <https://github.com/jdranczewski/puzzlepiece/blob/main/puzzlepiece/pieces/random_number.py>`_
(a single GUI module, representing an experimental device or task). The full source code is available at https://github.com/jdranczewski/puzzlepiece .

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   modules


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

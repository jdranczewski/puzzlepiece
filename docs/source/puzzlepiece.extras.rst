puzzlepiece.extras module
=========================

The extras module contains additional features that are useful, but not part of the
core puzzlepiece functionality. Currently these are ``ipython_shims`` (a small collection
of Notebook magics) and the ``datagrid`` - a Widget that can be added to your Pieces,
with multiple Piece-like Rows that use params for data storage
and manipulation.

The extras modules have to be imported explicitly::

   # This will import the datagrid module:
   from puzzlepiece.extras import datagrid
   # The following will not work:
   import puzzlepiece.extras as extras
   extras.datagrid

.. toctree::
   :maxdepth: 2

   puzzlepiece.extras.ipython_shims
   puzzlepiece.extras.datagrid

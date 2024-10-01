puzzlepiece.extras.ipython_shims module
=======================================

Import this module to get access to useful puzzlepiece-related Magics::

   from puzzlepiece.extras import ipython_shims

%%pzp_script
------------

Magic for running the cell as puzzlepiece script::

   %%pzp_script
   set:piece_name:param_name:25
   prompt:Param changed

Assumes the :class:`~puzzlepiece.puzzle.Puzzle` is in the global namespace
as ``puzzle``. A different name can be provided as an argument to the magic: 
``%%pzp_script puzzle_variable``.

See :func:`puzzlepiece.parse.run` for the full scripting syntax.

%%safe_run
------------

Magic for running the cell with a safety function in case of a crash::

   # Cell 1
   def close_shutter():
      puzzle["shutter"]["open"].set_value(0)

   # Cell 2
   %%safe_run close_shutter
   raise Exception

Running cell 2 will raise an exception, but the magic catches the exception,
closes the shutter, and then the original exception is re-raised. Another
useful usecase is sending a Slack message when a crash occurs.

This is similar in spirit to :func:`puzzlepiece.puzzle.Puzzle.custom_excepthook`,
but works in Notebooks in constrast to that.
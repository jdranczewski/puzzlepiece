Questions & Answers
===================

Here are some questions you may have about the details of how to use puzzlepiece.
If the topics below don't answer your question, consider submitting an issue at
https://github.com/jdranczewski/puzzlepiece/issues and I will try to reply!

Can I use puzzlepiece as a generic GUI framework?
+++++++++++++++++++++++++++++++++++++++++++++++++
Absolutely! It was created with experiment automation in mind, but the param/action
abstractions are widely applicable, and I've been using puzzlepiece to rapidly
create GUI tools for all sorts of things.

Why puzzlepiece?
++++++++++++++++
A number of other experiment automation frameworks exists of course. puzzlepiece was
born from a desire for a solution that makes the GUI a core priority, while still
providing a unified, convenient API for accessing hardware through code.

I think the balance I've landed on is pretty good, and it does technically allow
you to use puzzlepiece as the GUI frontend to other automation frameworks.

Here are some features that I count as the core ideas of puzzlepiece:

* Pre-made widgets allow for rapid GUI prototyping, while giving you a unified API
  "for free".
* Effortless modularity - you can divide your problem into many Pieces, and they can
  easily communicate with each other through the Puzzle. If parts of your problem
  change, add new Pieces or sub-class the existing ones!
* Quick and easy to set up with Jupyter Notebooks, which is incredibly powerful both
  for development and use - align your experiment using the GUI, but define measurements
  in code for example.
* Useful beyond the lab. I've been using puzzlepiece whenever I need to create a GUI
  tool. I find it's the quickest way to throw together Qt apps, or modules that can
  all talk to each other.
* Not very opinionated - the core abstraction of puzzlepiece (Pieces with params and
  actions) is meant to be flexible - you design your app and how it should work, we
  provide and standardise the parts that would be tedious to write manually.
* Good for beginners once set up. Many experiments require people who would prefer not
  to have to touch Python to operate them. You can create neat GUIs for them! And for
  the next steps, the ``get_value``/``set_value`` paradigm is an intuitive way to
  interact with hardware and makes for easier coding.

How does puzzlepiece talk to experimental hardware?
+++++++++++++++++++++++++++++++++++++++++++++++++++
Puzzlepiece itself doesn't! The goal of this library is to provide you with a
universal abstraction layer that makes building a GUI and automating its operation
easier, standardised, and modular.
This is achieved through the concepts of params and actions giving you premade
GUI components that are simple to create, and together build a universal API that
makes talking to your setup consistent.

**For hardware integration Pieces, you can check out** https://pzp-hardware.readthedocs.io,
**which has a growing library of ready-made integrations!**

For hardware not included in ``pzp-hardware``,
the hardware communication is something you need to implement yourself by
creating setters and getters for the various params. For example, ThorLabs provides
a Python API for their ThorCam cameras. You need to identify the parameters you'd
like to expose through puzzlepiece (checkbox for connection, spinbox for integration time,
array param for the camera image, ...) and create getters and setters for these params yourself.

Once that is done for the various bits of equipment you have, you can access your whole
setup through the same, modular interface! So there's some upfront time investment, but that's
generally true for creating any GUI/hardware interface, and after that in my experience
using your setup is much more smooth.

Should I use threads?
+++++++++++++++++++++
You can! But think carefully about where and how exactly these should be used. Most things
in puzzlepiece are single-threaded *on purpose*, so that we can guarantee an execution order
for the function calls you make. Set the moving stage, then adjust the projected image, and then
take a picture with the camera - no race conditions, just sequential execution. This means
the GUI will freeze during some actions, but this can be considered a feature - something
is happening, and so we will wait for it to finish before doing anything else or told
explicitly to refresh. This way you have a high degree of control over how things happen.

If you *do* want to update the GUI during a main thread process, call
:func:`puzzlepiece.puzzle.Puzzle.process_events` - this will return control to the GUI loop
for a bit, so plots can be drawn, button presses and keybord shortcuts processed. This can
be good, as it allows for live-ish updates, and stopping the process using the stop button,
but introduces a little bit of unpredictability - what if the user changes something?

For things that are not critical to run sequentially and which benefit from not freezing
the GUI, have a look at :mod:`puzzlepiece.threads` - for example,
:class:`puzzlepiece.threads.PuzzleTimer` is a Widget that lets you run an action repeatedly
in a background thread (like get an image from a camera for a live preview), and
:class:`puzzlepiece.threads.Worker` is a nice abstration for putting more generic tasks in
threads.

The :func:`puzzlepiece.param.BaseParam.get_value` and :func:`puzzlepiece.param.BaseParam.set_value`
methods are thread-safe by default, so can be used to safely update the GUI (progress bar for
example) from a Worker thread. Have a look at :class:`puzzlepiece.threads.Worker`
for a more detailed discussion of this.

You can also control-click on the buttons in the GUI (or press control+enter) to set/get values
in a thread, though do that at your own risk - if you press get twice for example during a camera
exposure, the manufacturer's API may get confused. This is best used for independent things - say
you want to keep the camera running while you set the position of a moving stage.

I want to do <X> to the param input
+++++++++++++++++++++++++++++++++++
You may want to change something about the way a param's input behaves, for example add more decimal
places to a :class:`~puzzlepiece.param.ParamFloat`, or add some options to a
:class:`~puzzlepiece.param.ParamDropdown`.

I don't implement all of these options, because it would quickly become a bit unwieldy to support
every use case, and Qt already has APIs for most things like this. Every ``param`` exposes an
``input`` attribute, which is a reference to the specific Qt Widget used for the input.

For example, you may check that :class:`~puzzlepiece.param.ParamFloat` uses a ``QDoubleSpinBox``
as its input box, either by reading the source code or inspecting ``puzzle["piece:param"].input``
in an interactive shell. You can then go to the brilliant
`Qt Docs <https://doc.qt.io/qt-6/qdoublespinbox.html#decimals-prop>`_
and find out that you can use ``QDoubleSpinBox.setDecimals(int prec)`` to set the number of decimal
places.

This can then be used either within the Piece or in your app to adjust existing Pieces::

  # in ``define_params``
  self["param"].input.setDecimals(5)
  # in your app
  puzzle["piece:param"].input.setDecimals(5)
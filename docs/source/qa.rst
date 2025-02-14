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

How does puzzlepiece talk to experimental hardware?
+++++++++++++++++++++++++++++++++++++++++++++++++++
Puzzlepiece itself doesn't! The goal of this library is to provide you with a
universal abstraction layer that makes building a GUI and automating its operation
easier, standardised, and modular.
This is achieved through the concepts of params and actions giving you premade
GUI components that are simple to create, and together build a universal API that
makes talking to your setup consistent.

The hardware communication is something you need to implement yourself by
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
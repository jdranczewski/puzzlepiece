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
Set up Python in the lab
========================

There are `many ways <https://xkcd.com/1987/>`__ to set up Python. The
following is an opinionated **guide to what I believe to be a reliable and
best-practice way to set Python up in a lab environment** with many users.
It assumes that these users will be on a spectrum of programming ability
or willingness: some will want to just run the GUI, some will prefer a
combination of GUI and Jupyter, and some will want to write their own
integrations.

The goal here is to set up a semi-global Python environment that will
enable easy access for everyone, while not getting in the way of others
who may want to set things up differently!

The guide will use Windows, as many lab equipment APIs default to that,
but you can adapt these principles to Linux or MacOS.

Installing Python
+++++++++++++++++
Personally, I prefer working with pure Python instead of Anaconda,
because I find Python's environment management principles more
straightforward than Anaconda's, and prefer to avoid mixing ``pip``
and ``conda`` when installing packages. Many of the principles here
can still be applied if you decide to use Anaconda, but this guide
from now on assumes a direct Python installation.

* **Download a recent version of Python** from
  https://www.python.org/downloads/ -- I usually err on the side of
  caution and install the second newest version, to avoid compatibility
  issues with packages that may not have been updated.
* **Run the installer, keeping the default options.** You *may* choose to add
  Python to the PATH:

  * PATH is the variable Windows uses to figure out where terminal
    commands live. If you add Python to the PATH, launch a terminal,
    type ``python`` and press enter, the version you have just installed
    will launch.
  * This can be good on a personal computer, but can be a problem on
    shared lab PCs, with potentially multiple versions of Python
    installed.
  * On a shared account, like in the lab, I would recommend **not adding
    Python to PATH**, and using virtual environments instead.

* Make a note of the **installation path** that Python is installed under.
  This will usually be similar to::

    C:\Users\<username>\AppData\Local\Programs\Python\Python313

  To see the AppData directory, you may have to enable "Show hidden
  items" in Windows Explorer.

* **Congrats, you now have Python!** If you haven't added Python to PATH
  in the installer, you can type this into the terminal to get the
  interactive prompt::

    <installation path>\python.exe

  For example::

    C:\Users\<username>\AppData\Local\Programs\Python\Python311\python.exe

  This is cumbersome though. Let us set up a **virtual environment** to
  make using Python easier.

Setting up a Python virtual environment
+++++++++++++++++++++++++++++++++++++++
**A virtual environment is like a “child” installation of Python** -- it
allows you to install packages in your own little container, without
touching the global installation. You can have multiple independent
environments, which lets multiple people work in their own environments
with their own packages, without having Python installed many times, or
getting in each other's ways.

*If* you are the only person using a Windows computer, and want to have
a basic, single installation of Python, you don't have to set up virtual
environments. But on shared systems, or systems other than Windows, it's
better to work with virtual environments.

**We will be working in** ``C:/automation`` -- I believe it's good to have
a central folder where your environment, APIs, libraries, and all
automation related things live. This is not required though -- you *can*
place the environment elsewhere. Just make sure it's reasonably easy
to find. **Create this folder now.**

* Go to your ``C:/automation`` folder in Windows Explorer, shift+right
  click and select "Open in Terminal" (Windows 11) or "Open PowerShell
  here" (Windows 10).

* The terminal working directory is displayed to the left of the input
  prompt. If it's wrong, you can change it with the ``cd`` command::

    cd "C:/path/to/working/folder"

* Using the Python installation path, create a virtual environment with
  a name of your choice (I usually go for ``venv``)::

    <installation path>/python.exe -m venv name_of_your_venv

  There should now be a folder in your automation directory with the
  name of your environment!
* To use your new environment, you have to **activate it**. When a
  virtual environment is activated, all calls to ``python`` or ``pip``
  in that terminal will refer to the specific environment and not the
  global Python installation.
* If your terminal window is still in the automation folder (check the
  path before the ``>`` and your cursor), you can say::

    name_of_your_venv/Scripts/Activate.ps1

  (we're assuming PowerShell is being used). If your terminal window is
  in any other working directory, you have to provide the full path to
  the environment::

    C:/automation/name_of_your_venv/Scripts/Activate.ps1

  A ``(name_of_your_venv)`` indicator should appear to the left of the
  command prompt in your terminal!

  * Note that you can press tab while typing the paths above to get
    autocomplete suggestions, making selecting the path easier -- pressing
    tab multiple times cycles through the suggestions.

Make the environment easy to access
+++++++++++++++++++++++++++++++++++
It should be easy for users of the lab PC to activate and use the main
experimental environment. If advanced users want to use their own
environments, that is of course fine, but someone who doesn't want to
deal with Python should be able to easily use an environment that
"just works".

PowerShell activation shortcut
------------------------------
It should be easy to activate the environment from any terminal. The
following steps will create a PowerShell "alias", so that **typing**
``venv`` **and pressing enter in any PowerShell window will activate
the environment.**

* Create a PowerShell profile text file in the following location::

    <Documents folder>/WindowsPowerShell/Microsoft.PowerShell_profile.ps1

* Make the contents of the file the following (matching your environment's
  location)::

    New-Alias venv C:\automation\venv\Scripts\Activate.ps1

* Enable script execution by running this in a PowerShell window::

    Set-ExecutionPolicy RemoteSigned

* The shortcut should work in any new PowerShell window! You may have to
  re-open any PowerShell windows that are currently open. Just type::

    venv

  and press enter to activate the environment.

Select environment in VSCode
----------------------------
`Visual Studio Code <https://code.visualstudio.com/>`__ is a flexible code
editor from Microsoft that is commonly used for Python (and other)
development. If you want to develop set up automations yourself, you
should probably use it, or a comparable Integrated Development Environment
(IDE) like `PyCharm <https://www.jetbrains.com/pycharm/>`__.

* Install VSCode from https://code.visualstudio.com/ and open the folder
  you want to work in from the file menu.
* Install the Python extension for VSCode from the extension pane on the
  left.
* With a Python file open, choose your environment in the bottom right
  corner by clicking the Python version number.
* If your environment doesn't appear in the popup automatically, you can
  add ``C:/automation`` to the "Python: Venv Folders" list in VSCode
  settings, or click "Enter interpreter path -> Find", and select the
  ``python.exe`` executable from the ``Scripts`` folder of your virtual
  environment.
* Executing Python files will now use your environment! Note that you can
  also run Jupyter Notebooks in VSCode!
* You can save your current Workspace by going “File -> Save workspace
  as...” - this will create a file you can double-click to reopen the
  Workspace later. VSCode will usually start with the last-opened
  workspace by default too.

Run Python files with your environment
--------------------------------------
You can of course run Python files using your new virtual environment
from VS Code or from the terminal::

  venv
  python automation.py

You may want to let your users run GUIs more easily though, and a good
way to do that is to **set the environment as the default way to open
Python files.** If you would rather not apply this to *all* Python files,
you can also make up a custom text file extension (like ``.pypzp``) and
set the default application for that.

* In Windows Explorer, select "View -> Show -> File name extensions"
  to make it clear what kind of files you're working with, and make it
  easy to change the extension to whatever you want.
* Right-click a ``.py`` (or ``.pypzp``, or any other extension you want
  to open with the virtual environment's Python) file. Select "Open
  with -> Choose another app".
* Scroll all the way down to "Choose an app on your PC" in the dialog
  and click that.
* Browse to your virtual environment folder in the file selection dialog,
  go to ``Scripts`` and select ``python.exe``. You can also choose
  ``pythonw.exe`` if you want to hide the terminal, but usually it's
  best to keep it for debugging purposes.
* Click "Always" in the "Choose another app" popup.

Your app should launch using the environment, and double-clicking files
with the same extension should also run them using the same environment.

Install Python packages
+++++++++++++++++++++++
In contrast to Anaconda, pure Python does not come with packages like numpy
pre-installed. You have to get them using the ``pip`` package manager.
Whenever you encounter a package that you need and that isn't installed,
you can simply run (**we will always assume you have the virtual environment
activated here**)::

  pip install name_of_the_package

To speed up package installation, I recommend installing ``uv``
(https://docs.astral.sh/uv/), which can act as a drop-in replacement for ``pip``.
If you choose not to use it, simply remove ``uv`` from any ``pip`` commands shown
here. To install ``uv`` in our environment, we use ``pip``::

  pip install uv

Now we can install a couple of basic scientific packages::

  uv pip install numpy scipy matplotlib jupyterlab jupytext tqdm puzzlepiece PyQt6

Note that I use ``PyQt6`` here, but feel free to install ``PySide6`` if you
prefer working under the L-GPL, rather than the GPL license.

To update packages, use the ``--upgrade`` option::

  uv pip install --upgrade puzzlepiece

Adding folders to the environment
+++++++++++++++++++++++++++++++++
You may want to make Python files in a folder available for importing. This
could be a directory of useful scripts or puzzlepiece Pieces for example.

If the folder is a Python package
---------------------------------
With some simple steps you can make a folder a Python package that can be installed,
and many GitHub repositories may already be Python packages. If you would like to
make a folder installable as a package, you can create the ``pyproject.toml`` file
with ``uv``::

  uv init --bare .

Then create a folder named after your package in that directory (say ``test_package``)
and put your files in there (so you could then write ``from test_package import file``).

You can install the folder into your environment using ``pip``::

  uv pip install -e .

The ``-e`` option makes the package "editable", meaning that any changes you make to the
files in this folder will be respected when you import the package.

You can follow similar steps to install and edit packages from GitHub. I recommend doing this
with `pzp-hardware <https://pzp-hardware.readthedocs.io>`__, so you can add your own hardware
integrations in the same spot, track your changes with git , and then
`open pull requests <https://github.com/jdranczewski/pzp-hardware/pulls>`__ to have your integration
merged into the main package! The steps are similar to the above::

  git clone https://github.com/jdranczewski/pzp-hardware.git
  cd pzp-hardware
  uv pip install -e .

You may have to `install git <https://git-scm.com/>`__ first, and learn version control fundamentals
at https://github.com/git-guides. There is a good git GUI built into VS Code too!

If the folder is not a Python package
-------------------------------------
In some cases, you may want to make Python search a folder even if it's not a package for the sake
of simplicity (you may have seen people talk about "adding directories to the PYTHONPATH", which
is an environment variable).

As an example, let's say we want to let the user import anything that's in ``C:/automation/libraries``.

* Go to ``C:\automation\venv\Lib\site-packages``, or the equivalent for your environment location.
* Create a text file there and name it ``libraries.pth`` -- the name doesn't matter, just make it
  informative. The file extension must be ``.pth``.
* Open the file in Notepad or another text editor and make the contents the path to the folder you
  want to be able to import from, like ``C:/automation/libraries``.
* You may have to re-activate the environment.

You can now import from this folder! If there's a Python file at ``C:/automation/libraries/test.py``,
you can now ``import test``.

Note that I would advise against using this to add manufacturer APIs to your Python search path.
Instead, you can use :func:`puzzlepiece.extras.hardware_tools.add_path_directory` and
:func:`puzzlepiece.extras.hardware_tools.add_dll_directory` to add these at runtime in a way that is
much easier to reproduce between installations and environments, especially if you use
:func:`puzzlepiece.extras.hardware_tools.config` to prompt for the directory at runtime, and store
it alongside the Piece::

  # Default directory
  dll_directory = r"C:\Program Files\Thorlabs\Scientific Imaging\Scientific Camera Support\Scientific Camera Interfaces\SDK\Native Toolkit\dlls\Native_64_lib"
  # Load directory from config file or prompt the user if config not present
  dll_directory = pht.config(
      "thorcam_dll_directory",
      default=dll_directory,
      validator=pht.validator_path_exists,
  )
  # Add the directory to path
  pht.add_dll_directory(dll_directory)

Using Jupyter Notebooks/Lab
+++++++++++++++++++++++++++
We've installed Jupyter Lab with ``pip`` above, so launching it is easy now. Go to the folder you
want to work in in Windows Explorer, shift+right click and select "Open in Terminal" (Windows 11)
or "Open PowerShell here" (Windows 10). Then activate the environment and run Lab::

  venv
  jupyter lab

A browser window should open, running Jupyter Lab in your environment! **I usually use Jupyter Lab
and puzzlepiece when working in the lab** - construct a Puzzle in a Notebook, and then I can interact
with it both from the Notebook and in the GUI! The Notebook can double as a lab book too, chronicling
your notes in Markdown cells, alongside the code you've run. You have to use the ``%gui qt`` "magic"
to enable this::

  %gui qt
  import puzzlepiece as pzp

  puzzle = pzp.Puzzle()
  puzzle.show()

Opening Jupyter Lab as an app
-----------------------------
Jupyter Lab opens as a browser tab by default, which can be annoying if you have many tabs open.
We can use Google Chrome to open Lab as a separate "application", with its own window and taskbar
icon.

* Open a terminal and run::

    venv
    jupyter lab --generate-config

* A new file will appear on your computer: ``C:\Users\<your username>\.jupyter\jupyter_lab_config.py``.
  Edit this file and add the following line anywhere below ``c = get_config()``::

    c.LabApp.browser = '"C:\Program Files\Google\Chrome\Application\chrome.exe" --app=%s'

When you launch Jupyter Lab it should now open as a separate window!

Saving Jupyter Notebooks as Python files
----------------------------------------
With the ``jupytext`` package installed, you can open and edit Python files as if they were Jupyter
Notebooks. I find this quite nice for version control, easy searching and browsing the Notebooks in
any text editor, but note that **this doesn't save cell output, only the code and Markdown notes**.

* You can right-click on .py files in Jupyter Lab to open them as Notebooks.
* You can create new Python file "Notebooks" from the "Jupytext" section in the Jupyter Lab launcher.

Adding multiple virtual environments to Jupyter as kernels
----------------------------------------------------------
You only need to do this if you have multiple different virtual environments that you'd like to use
from the same Jupyter Lab installation. Follow this tutorial:
https://janakiev.com/blog/jupyter-virtual-envs/, but in short, with your environment activated::

  python -m ipykernel install --user --name=name_for_the_kernel

Tips and tricks
+++++++++++++++
* VS Code's git integration is pretty good already, but I recommend installing the "Git Graph" extension
  for a clearer overview of a repository's history and some additional actions.
* If you are using a private GitHub repository and want to have access to it on the lab computer, you
  should use **access tokens** rather than log into your personal account.

  * To create a token go to "Settings -> Developer Settings -> Personal Access Tokens -> Fine-grained
    tokens" on GitHub (https://github.com/settings/personal-access-tokens). Under “Repository access”
    select the repositories you would like the computer to access. Under “Repository permissions” give
    read and write access to Contents.
  * Configure git on the computer to sign the commits with a name unique to it, so you can trace
    where the commits come from::

      git config --global user.name "Lab PC"
      git config --global user.email "lab_pc@example.com"
  * You can now push and pull to the private repositories specified.

* You can open Jupyter Notebooks in VS Code using the Jupyter extension, and there are also some
  extensions that implement ``jupytext`` for using ``.py`` files as Notebooks. You can combine this
  with ``.code-workspace`` files to create an easy-to-launch lab environment with the right Python
  environment already selected.
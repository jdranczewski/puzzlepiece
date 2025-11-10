import ctypes as c
import configparser
import importlib
import inspect
import os
from qtpy import QtWidgets, QtGui
import subprocess
import sys
import webbrowser

import typing


# region CONFIG
def debug_prompt(force_terminal=False):
    """
    Display a prompt asking the user whether to launch the Puzzle in debug mode. If a QApplication
    exists, this will be a GUI prompt, otherwise ``Launch Puzzle in debug mode? (Y/n)`` is shown
    in the terminal. Returns False if the user types anything starting with "n" (n/no/No/N etc.),
    otherwise returns True. The GUI prompt can also be cancelled, which raises an Exception
    to halt the launch.

    This is useful in ``__main__`` declaration in Piece files, so that the same file can
    be run directly and used for testing both debug and non-debug operation, but changes
    to the debug flag don't get checked into version control::

        if __name__ == "__main__":
            app = pzp.QApp()
            puzzle = pzp.Puzzle(name="Template", debug=pht.debug_prompt())
            puzzle.add_piece("template", Piece, row=0, column=0)
            puzzle.show()
            app.exec()

    :param force_terminal: Skip the QApplication check and always prompt in the terminal, not the GUI.
    :rtype: bool
    """
    app = QtWidgets.QApplication.instance()
    if not force_terminal and app:
        # If there's already a QApplication, ask the question as a GUI prompt
        mb = QtWidgets.QMessageBox()
        mb.setWindowTitle("puzzlepiece")
        mb.setText("Launch Puzzle in debug mode?")
        mb.setStandardButtons(
            mb.StandardButton.Yes | mb.StandardButton.No | mb.StandardButton.Cancel
        )
        mb.setDefaultButton(mb.StandardButton.Yes)
        dirname = os.path.dirname(__file__)
        mb.setWindowIcon(QtGui.QIcon(os.path.join(dirname, "../icon.png")))
        response = mb.exec()
        if response == mb.StandardButton.Cancel:
            raise Exception("Puzzle launch cancelled from debug_prompt")
        return response == mb.StandardButton.Yes
    check = input("Launch Puzzle in debug mode? (Y/n) ")
    return not (len(check) and check.lower()[0] == "n")


def _get_caller_details(level=1):
    """
    Get the path and filename of this function's caller N levels up.
    """
    filename = inspect.stack()[level].filename
    return os.path.dirname(filename), os.path.basename(filename)


_section = "puzzlepiece"


def config(
    key,
    *,
    default: typing.Any = None,
    description: str = None,
    validator: typing.Callable = None,
):
    """
    Obtain a config value (specific to the calling file) for a given key. If a saved value is
    not present, prompt the user for one with the given description. A validator function
    can be given, which should raise an exception if the user input value is not valid
    (the validator is not used to test already stored values).

    The config files use the INI format and are placed alongside the calling Python file.
    For example, if ``config`` is called in ``camera.py``, it will create ``camera.config``
    next to ``camera.py``.

    The method enables storing local configuration files for installation-specific things
    like DLL directories. For example::

        from puzzlepiece.extras import hardware_tools as pht
        dll_directory = pht.config(
            "thorcam_dll_directory",
            default="C:/DLLs",
            validator=pht.validator_path_exists
        )

    :param key: The config key name to retrieve/save
    :param default: A default value for the key, the user can accept it by pressing enter
    :param description: A description that will be shown along with the input prompt
    :param validator: A function that checks if the user input is valid (should raise an
        exception if not)
    :return: The stored/saved value
    """
    # Establish path to config file and load it
    folder, fname = _get_caller_details(level=2)
    # Replace the extension with "config"
    cname = fname.split(".")
    if len(cname) > 1:
        cname[-1] = "config"
    else:
        cname.append("config")
    cname = ".".join(cname)
    parser = configparser.ConfigParser()
    parser.read(os.path.join(folder, cname))

    # If key is present in the config, simply return it
    if _section in parser and key in parser[_section]:
        return parser[_section][key]

    # otherwise, ask the user for a value:
    question = f"----------\n'{fname}' requires a value for '{key}'"
    if description:
        question += f" - {description}"
    if question[-1] != ".":
        question += "."
    question += "\n\nPlease provide a value, "
    if default:
        question += f"or press enter to accept the default value ('{default}'), "
    question += "or press ctrl+c to cancel: "
    value = input(question)
    # Check if user wants to keep default value
    if not len(value) and default:
        value = default
    # Validate the input
    if validator:
        validator(value)

    # Write the given value to the file
    if _section not in parser:
        parser[_section] = {}
    parser[_section][key] = value
    try:
        with open(os.path.join(folder, cname), "w") as f:
            parser.write(f)
    except FileNotFoundError:
        raise Exception(
            f"could not create the config file at {os.path.join(folder, cname)}"
        )
    return value


def validator_path_exists(name: str) -> None:
    """
    Raise a ``FileNotFoundError`` if the provided path (directory or file) does not exist.
    Can be used as a validator for :func:`puzzlepiece.extras.hardware_tools.config`.

    :param name: Path to a directory or file
    """
    if not os.path.exists(name):
        raise FileNotFoundError(f"'{name}' does not exist")


# endregion


# region Requirements
def requirements(packages_spec: typing.Union[dict, typing.List[str]]) -> None:
    """
    Indicate that some Python packages are required to proceed. Can be used to implement per-file
    requirements for larger automation suites - the user may not have to install all the packages,
    but some are required for running specific files. Calls to this method are also parsed to
    indicate Piece requirements in https://pzp-hardware.readthedocs.io

    When called, this function will stop script execution and inform the user that a package is required.
    The next steps depend on the specification provided in ``packages_spec``. If it's a simple list of
    package names, ``requirements`` will raise a ``ModuleNotFoundError`` if any of them are not installed.
    If ``packages_spec`` is a dictionary with installation instructions, the user will be asked whether they
    want to automatically install the package with pip (which will use the current Python executable to
    install into the right virtual environment), or online installation instructions will be opened.

    For example, in a :class:`~puzzlepiece.piece.Piece`'s :func:`~puzzlepiece.piece.Piece.setup` method::

        def setup(self):
            pht.requirements({
                "thorlabs_tsi_sdk": {
                    # This will just open installation instructions in a browser and raise ModuleNotFoundError
                    "url": "https://pzp-hardware.readthedocs.io/en/latest/auto/pzp_hardware.thorlabs.camera.html#installation"
                },
                "PIL": { # the name of the package, as in "import PIL"
                    "pip": "pillow", # the PyPI name of the package, as in "pip install pillow"
                    # If pip installation fails or is not chosen by the user, open installation instructions
                    "url": "https://pillow.readthedocs.io/en/stable/installation/basic-installation.html",
                }
            })

            # This will indicate requirements but not help the user install them:
            pht.requirements(["thorlabs_tsi_sdk", "PIL"])

            # Once we ensure the requirements are installed, we can import them:
            import thorlabs_tsi_sdk

    :param packages_spec: The specification for the required packages
    """
    for package_name in packages_spec:
        if importlib.util.find_spec(package_name):
            continue
        # if not package:
        try:
            package = packages_spec[package_name]
            if "pip" in package:
                check = input(
                    f"----------\n'{package_name}' not installed, would you like to automatically install it from pip?\n"
                    f"You can also run 'pip install {package['pip']}' yourself.\n(y/N): "
                )
                if len(check) and check.lower()[0] == "y":
                    try:
                        subprocess.check_call(
                            [sys.executable, "-m", "pip", "install", package["pip"]]
                        )
                        continue
                    except subprocess.CalledProcessError:
                        print(f"Failed to automatically install '{package_name}'.")
                        print(
                            f"Please run 'pip install {package['pip']}' and try again."
                        )
            if "url" in package:
                webbrowser.open(package["url"])
                raise ModuleNotFoundError(
                    f"'{package_name}' not installed, install instructions opened in default browser"
                )
        except TypeError:
            # The argument is not a dictionary
            pass
        raise ModuleNotFoundError(package_name)


# endregion


# region DLL
def add_path_directory(directory: str) -> None:
    """
    Add the directory provided to the PATH. This will add both to the system path
    and the Python search path for the current Python session.

    :param directory: The directory to add to the PATH. Can be relative.
    """
    directory = os.path.abspath(directory)
    os.environ["PATH"] = directory + os.pathsep + os.environ["PATH"]
    sys.path.append(directory)


def add_dll_directory(directory: str) -> None:
    """
    Add the directory provided to the PATH as in
    :func:`~puzzlepiece.extras.hardware_tools.add_path_directory`, but also to
    the allowed DLL directory list (using ``os.add_dll_directory``). This is needed
    since Python 3.8 for your DLLs to be found and used.

    :param directory: The directory to add to the PATH. Can be relative.
    """
    add_path_directory(directory)
    os.add_dll_directory(directory)


def load_dll(path: str, fallback: dict = None) -> "c.WinDLL":
    """
    Load a DLL from a path. Also calls :func:`~puzzlepiece.extras.hardware_tools.add_dll_directory`
    for you. Returns a ctypes ``WinDLL`` object.

    Installation instructions can be provided for the user in the form of the ``fallback`` dictionary.
    These are shown if the DLL load fails in any way, along with the exception.
    A message can be printed in the console, and/or installation instructions opened in the default
    browser.

    Example usage::

        from puzzlepiece.extras import hardware_tools as pht
        pht.load_dll(
            dll_path,
            fallback = {
                "message": "This Piece requires the ThorLabs APT DLLs.",
                "url": "https://example.org",
            }
        )

    :param path: Path to the DLL to load
    :param fallback: A dictionary of instructions for the user to install the DLL. Currently supports
        "message" and "url" as keys.
    """
    try:
        add_dll_directory(os.path.dirname(path))
        return c.windll.LoadLibrary(path)
    except Exception as e:
        print(f"Failed to load dll ('{path}')")
        if "message" in fallback:
            print(fallback["message"])
        if "url" in fallback:
            webbrowser.open(fallback["url"])
            print("Installation instructions opened in default browser.")
        raise e


def dll_methods(path: str) -> typing.List[str]:
    """
    Use ``pefile`` to return a list of function names for a DLL given as a path.
    Can be used to inspect the methods exposed by a manufacturer's DLL, useful
    during initial exploration when developing a hardware Piece. Does not parse
    method arguments or return types, the manufacturer's manual needs to be consulted
    for these.

    ``pefile`` is an optional dependency, it can be installed with ``pip install pefile``,
    or at runtime, as it is required with :func:`~puzzlepiece.extras.hardware_tools.requirements`.

    :param str: Path to the DLL.
    :return: A list of method names exposed by the DLL.
    """
    requirements({"pefile": {"pip": "pefile"}})
    import pefile

    pe = pefile.PE(path)
    return [exp.name.decode() for exp in pe.DIRECTORY_ENTRY_EXPORT.symbols]


def load_dll_with_methods(path: str) -> typing.Tuple["c.WinDLL", typing.List[str]]:
    """
    Use :func:`~puzzlepiece.extras.hardware_tools.load_dll` to load a DLL from a path,
    and :func:`~puzzlepiece.extras.hardware_tools.dll_methods` to get the methods it exposes.
    Both are returned.

    Additionally, the returned ``WinDLL`` will have the methods saved in its ``__dir__``,
    meaning that they are available for autocompletion in IPython. This is particularly useful
    in early development, making inspection of available methods easier.

    ``pefile`` is an optional dependency, it can be installed with ``pip install pefile``,
    or at runtime, as it is required with :func:`~puzzlepiece.extras.hardware_tools.requirements`.

    :param str: Path to the DLL.
    """
    lib = load_dll(path)
    methods = dll_methods(path)
    # Iterate through the methods and get them from the library
    # This registers them in the library's __dir__ for future use
    for name in methods:
        getattr(lib, name)
    return lib, methods


# endregion

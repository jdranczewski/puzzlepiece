import ctypes as c
import configparser
import importlib
import inspect
import os
import subprocess
import sys
import webbrowser

import typing


# region CONFIG
def debug_prompt():
    check = input("Launch in debug mode? (Y/n) ")
    return not (len(check) and check.lower()[0] == "n")

def _get_caller_details(level=1):
    filename = inspect.stack()[level].filename
    return os.path.dirname(filename), os.path.basename(filename)


_section = "puzzlepiece"


def config(key, *, default=None, description=None, validator=None):
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


def validator_path_exists(name):
    if not os.path.exists(name):
        raise FileNotFoundError(f"'{name}' does not exist")


# endregion


# region DLL
def add_path_directory(directory: str) -> None:
    os.environ["PATH"] = directory + os.pathsep + os.environ["PATH"]
    sys.path.append(directory)


def add_dll_directory(directory: str) -> None:
    add_path_directory(directory)
    os.add_dll_directory(directory)


def load_dll(path: str, fallback:dict = None) -> "c.WinDLL":
    try:
        add_dll_directory(os.path.dirname(path))
        return c.windll.LoadLibrary(path)
    except Exception as e:
        print(f"Failed to load dll ('{path}')")
        if "message" in fallback:
             print(fallback["message"])
        if "url" in fallback:
            webbrowser.open(fallback["url"])
            print(
                f"Installation instructions opened in default browser."
            )
        raise e


def dll_methods(path: str) -> typing.List[str]:
    requirements({"pefile": {"pip": "pefile"}})
    import pefile

    pe = pefile.PE(path)
    return [exp.name.decode() for exp in pe.DIRECTORY_ENTRY_EXPORT.symbols]


def load_dll_with_methods(path: str) -> typing.Tuple["c.WinDLL", typing.List[str]]:
    lib = load_dll(path)
    methods = dll_methods(path)
    # Iterate through the methods and get them from the library
    # This registers them in the libary's __dir__ for future use
    for name in methods:
        getattr(lib, name)
    return lib, methods


# endregion


# region Requirements
def requirements(packages_spec: typing.Union[dict, typing.List[str]]) -> None:
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

import re
import time
from pyqtgraph.Qt import QtWidgets

def parse_params(text, puzzle):
    """
    Parse a string of the following format to construct references to :class:`~puzzlepiece.param.BaseParam` objects:
    ``[Piece name]:[param name], [Piece name]:[param name], ...``

    :param text: The string to parse.
    :param puzzle: The app's :class:`~puzzlepiece.puzzle.Puzzle`.
    :rtype: list(puzzlepiece.param.BaseParam, )
    """
    args = text.split(", ")
    result = []
    for arg in args:
        piece, name = arg.split(":")
        if name in puzzle.pieces[piece].params:
            result.append(puzzle.pieces[piece].params[name])
        else:
            raise SyntaxError(f"Parameter parse error for {arg}")
    return result

def run(text, puzzle):
    """
    Execute a set of puzzlepiece script commands.
    
    Commands can be separated by new lines, or a semicolon (``;``) + space.

    If a command needs to *include* a semicolon followed by a space,
    it can be inserted as ``\;`` (backslash character + semicolon + space).
    
    Comments can be added by starting the line with ``#``.

    The available commands are:
        - ``set:[Piece name]:[param name]:[value]``
        - ``run:[Piece name]:[action name]``
        - ``get:[Piece name]:[param name]``
        - ``sleep:[duration in s]``
        - ``prompt:[text]``
        - ``print:[text]``

    :param text: The string to parse.
    :param puzzle: The app's :class:`~puzzlepiece.puzzle.Puzzle`.
    """
    text = text.replace('\\;', '<!--semicolon-->')
    text = text.replace('; ', '\n')
    instructions = text.split('\n')
    for instruction in instructions:
        if len(instruction) == 0 or instruction[0] == '#':
            continue
        task, *params = instruction.split(':')
        if task == 'set':
            piece, param, *value = params
            value = ":".join(value)
            value = value.replace('<!--semicolon-->', ';')
            puzzle.pieces[piece].params[param].set_value(value)
        elif task == 'run':
            piece, *action = params
            action = ":".join(action)
            puzzle.pieces[piece].actions[action]()
        elif task == 'get':
            piece, *param = params
            param = ":".join(param)
            puzzle.pieces[piece].params[param].get_value()
        elif task == 'sleep':
            duration = params[0]
            time.sleep(float(duration))
        elif task == 'prompt':
            text = ':'.join(params)
            text = format(text, puzzle)
            box = QtWidgets.QMessageBox()
            box.setText(text)
            box.exec()
        elif task == 'print':
            text = ':'.join(params)
            text = format(text, puzzle)
            print(text)
        else:
            raise SyntaxError("Unknown task in {}".format(instruction))
        puzzle.process_events()

def format(text, puzzle):
    """
    Insert values of :class:`~puzzlepiece.param.BaseParam` objects
    into a string.

    To insert a value, use the following format:
    ``The value is: {[Piece name]:[param name]}``

    If a param has a getter, it will be called.

    One can also apply additional formatting:
    ``The formatted value is {[Piece name]:[param/readout name];[format]}``
    where `format` follows the 'new' standard as described at https://pyformat.info/.
    For example:
    ``The laser power is {laser:power;:.1f}``

    :param text: The string to parse.
    :param puzzle: The app's :class:`~puzzlepiece.puzzle.Puzzle`.
    :rtype: str
    """
    for match in re.findall(r"{[a-zA-Z0-9:; _\-\.]+}", text):
        m = str(match)
        elements = m[1:-1].split(";")
        param = parse_params(elements[0], puzzle)[0]
        if len(elements) == 1:
            if param._format is not None:
                result = param._format.format(param.get_value())
            else:
                result = str(param.get_value())
        elif len(elements) == 2:
            result = ('{'+elements[1]+'}').format(param.get_value())
        text = text.replace(m, result)
    return text
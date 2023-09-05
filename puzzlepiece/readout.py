from . import param

def define(piece, name, format="{}", visible=True):
    return param.readout(piece, name, visible, format)
import puzzlepiece as pzp
from pyqtgraph.Qt import QtWidgets

class Piece(pzp.Piece):
    def __init__(self, puzzle):
        super().__init__(puzzle)
        self.stop = False

    def define_params(self):
        pzp.param.text(self, "iterator", "")(None)
        pzp.param.text(self, "pre", "")(None)
        pzp.param.text(self, "post", "")(None)
        pzp.param.spinbox(self, "counter", 0, visible=False)(None)

    def define_actions(self):
        @pzp.action.define(self, "Save")
        def save(self):
            fname = str(QtWidgets.QFileDialog.getSaveFileName(self, "Save file...")[0])
            with open(fname, 'w') as f:
                f.write("#pre " + self.params['pre'].get_value() + '\n')
                f.write("#post " + self.params['post'].get_value() + '\n')
                f.write(self.text.toPlainText())

        @pzp.action.define(self, "Open")
        def _open(self):
            fname = str(QtWidgets.QFileDialog.getOpenFileName(self, "Open file...")[0])
            with open(fname, 'r') as f:
                text = ""
                for line in f.readlines():
                    if '#pre ' in line:
                        self.params['pre'].set_value(line[5:-1])
                    elif '#post ' in line:
                        self.params['post'].set_value(line[6:-1])
                    else:
                        text += line
                self.text.setPlainText(text)
                
        @pzp.action.define(self, "Run")
        def run(self):
            self.stop = False
            iter_name = self.params['iterator'].get_value()

            try:
                pzp.parse.run(self.params['pre'].get_value(), self.puzzle)

                if len(iter_name):
                    iterator = self.puzzle.pieces[iter_name].iterator()
                    for step in iterator:
                        pzp.parse.run(self.text.toPlainText(), self.puzzle)
                        if self.stop:
                            self.stop = False
                            return
                else:
                    pzp.parse.run(self.text.toPlainText(), self.puzzle)
            finally:
                pzp.parse.run(self.params['post'].get_value(), self.puzzle)
    
    def custom_layout(self):
        layout = QtWidgets.QVBoxLayout()

        self.text = QtWidgets.QPlainTextEdit()
        self.text.setPlainText("")
        layout.addWidget(self.text)

        return layout

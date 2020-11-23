# coding:utf-8

__author__ = "timmyliang"
__email__ = "820472580@qq.com"
__date__ = "2020-03-22 22:55:38"

"""

"""

import os
import sys

from functools import wraps, partial

DIR = os.path.dirname(__file__)
MODULE = os.path.join(DIR, "..")
if MODULE not in sys.path:
    sys.path.append(MODULE)

from QBinder import Binder


from Qt import QtWidgets
from Qt import QtCore
from Qt import QtGui

class WidgetTest(QtWidgets.QWidget):

    state = Binder()
    state.text = "empty"
    state.num = 1
    state.val = 2.0
    state.start = 1
    state.end = 2
    
    def __init__(self):
        super(WidgetTest, self).__init__()
        self.initialize()

    def initialize(self):
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.edit = QtWidgets.QLineEdit()
        self.label = QtWidgets.QLabel()
        self.button = QtWidgets.QPushButton("change Text")
        layout.addWidget(self.edit)
        layout.addWidget(self.label)
        layout.addWidget(self.button)

        self.button.clicked.connect(self.change_text)
        self.edit.setText(lambda: self.state.text)
        self.edit.setSelection(lambda: (self.state.start,self.state.end))
        self.label.setText(lambda: "message is %s" % self.state.text)
        
        self.spin = QtWidgets.QSpinBox(self)
        self.label = QtWidgets.QLabel()
        layout.addWidget(self.spin)
        layout.addWidget(self.label)
        self.spin.setValue(lambda: self.state.num)
        self.label.setText(lambda: "num is %s" % self.state.num)
        print(self.label.text())
        self.spin = QtWidgets.QDoubleSpinBox(self)
        self.label = QtWidgets.QLabel()
        layout.addWidget(self.spin)
        layout.addWidget(self.label)
        self.spin.setValue(lambda: self.state.val)
        self.label.setText(lambda: "val is %s" % self.state.val)
        
    def change_text(self):
        # self.state.start =0
        self.state.end += 1
        # self.edit.setSelection(1,4)
        # self.state.text = "asd"

if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    widget = WidgetTest()
    widget.show()

    app.exec_()


# import sys
# MODULE = r"G:\repo\QBinder\test"
# sys.path.insert(0,MODULE) if MODULE not in sys.path else None

# import inputTest
# # reload(inputTest)
# widget = inputTest.WidgetTest()
# widget.show()
import sys

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication

from VideoPreview.videoPreview_main import VideoPreview
# coding=utf-8

from demo.VideoPreview.deviceTree import DeviceTree


def __main__():
    app = QtWidgets.QApplication(sys.argv)
    app.setObjectName("InspSys")
    win = VideoPreview()
    win.show()
    win.raise_()
    sys.exit(app.exec_())

if __name__ == '__main__':
    __main__()
    app = QApplication(sys.argv)
    #tree = DeviceTree()
    #tree.show()
    sys.exit(app.exec_())


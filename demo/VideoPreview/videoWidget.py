from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QImage, QFont
from PyQt5.QtCore import Qt


class VideoWidget(QtWidgets.QWidget):
    """
     播放视频窗口
    """
    selectionChanged = QtCore.pyqtSignal(int)  # 添加一个信号
    enlargeWindow = QtCore.pyqtSignal(int)
    def __init__(self, parent=None):
        super(VideoWidget, self).__init__(parent)
        self.setStyleSheet("QWidget {background-color: white;}")
        self.widget = QtWidgets.QLabel(self)
        self.index = -1
        self.selected = False
        self.setContentsMargins(0,0,0,0)
        
        # 创建布局
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(2, 2, 2, 2)
        self.layout.setSpacing(0)
        
        # 添加到布局
        self.layout.addWidget(self.widget)
        
        self.setLayout(self.layout)
        
    def mouseDoubleClickEvent(self,QMouseEvent=None):
        # 发射双击信号，传递当前窗口的索引
        if QMouseEvent.button() == Qt.LeftButton:
            self.enlargeWindow.emit(self.index)
        print("double click")
        
    def select(self):
        self.selected = True
        self.setStyleSheet("QWidget { background-color: lightgreen; }")
        
    def selectCancle(self):
        self.selected = False
        self.setStyleSheet("QWidget { background-color: white; }")
        
    def mousePressEvent(self, event):
        if not self.selected:
            self.selectionChanged.emit(self.index)  # 发射信号
            self.select()
        else:
            self.selectionChanged.emit(-1)  # 发射信号
            self.selectCancle()
            
    def set_info_text(self, text):
        """设置窗口信息文本 - 现在不再使用"""
        pass
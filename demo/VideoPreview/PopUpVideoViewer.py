from PyQt5 import QtWidgets, QtCore


class PopUpVideoViewer(QtWidgets.QWidget):
    windowClosed = QtCore.pyqtSignal()  # 窗口关闭信号

    def __init__(self, index, channel_data, preview_handle=None, device_controller=None, parent=None):
        super().__init__(parent)
        self.index = index
        self.channel_data = channel_data or {}
        self.preview_handle = preview_handle
        self.device_controller = device_controller

        # 如果作为嵌入组件，不要设置 WA_DeleteOnClose 为 False，由 videoView 控制
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)

        self._setup_window()
        self._setup_ui()



    def _setup_window(self):
        """配置窗口基础属性（大小、标题等）"""
        # 窗口标题（适配通道数据）
        device_name = self.channel_data.get('device_name', '未知设备')
        channel_num = self.channel_data.get('channel_num', 1)
        self.setWindowTitle(f"大窗口预览 - {device_name} (通道{channel_num})")

        # 适配大小：设置合理的默认尺寸，同时支持窗口缩放
        self.resize(1280, 1020)  # 16:9 适配视频预览的常见比例
        self.setMinimumSize(800, 600)  # 设置最小尺寸，避免窗口缩太小

    # 在 PopUpVideoViewer 的 _setup_ui 中添加一个关闭/还原按钮
    # 修改 PopUpVideoViewer.py
    # 修改 PopUpVideoViewer.py 的 _setup_ui
    def _setup_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 关键：创建一个 QLabel 或 QWidget 作为视频承载器
        self.big_video_widget = QtWidgets.QLabel(self)
        self.big_video_widget.setStyleSheet("background-color: black;")
        main_layout.addWidget(self.big_video_widget)

    def closeEvent(self, event):
        # 关闭时必须通知 videoView 恢复
        self.windowClosed.emit()
        event.accept()

    def keyPressEvent(self, event):
        """ESC键关闭窗口"""
        if event.key() == QtCore.Qt.Key_Escape:
            self.close()
        super().keyPressEvent(event)  # 保留父类事件处理


    # 可选：添加窗口居中显示（提升用户体验）
    def showEvent(self, event):
        """窗口显示时居中"""
        self.move(QtWidgets.QDesktopWidget().availableGeometry().center() - self.rect().center())
        super().showEvent(event)
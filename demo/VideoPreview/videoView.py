from asyncio import sleep

from PyQt5.QtGui import QMouseEvent
from PyQt5 import QtWidgets,QtCore

from demo.VideoPreview.videoWidget import VideoWidget


class VideoView(QtWidgets.QWidget):
    """
    视频窗口容器
    """
    windowSelected = QtCore.pyqtSignal(int)  # 添加窗口选中信号
    def __init__(self, parent=None):
        super(VideoView, self).__init__(parent)
        # 视频
        self.video_widgets = []
        self.current_selected_index = -1  # 修正变量名
        # 正确初始化布局
        self.main_layout = QtWidgets.QVBoxLayout(self)  # 关键修复
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.main_layout)
        
        # 创建网格布局
        self.grid_layout = QtWidgets.QGridLayout()
        self.grid_layout.setSpacing(2)
        self.main_layout.addLayout(self.grid_layout)

        self.setup_windows(4)  # 默认4窗口布局

    def setup_windows(self, num_windows):
        """初始化视频窗口"""
        # 清除现有窗口
        for i in reversed(range(self.grid_layout.count())):
            item = self.grid_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()
        self.video_widgets.clear()

        # 创建视频窗口
        n = int(num_windows ** 0.5)
        for i in range(num_windows):
            row = i // n
            col = i % n

            widget = VideoWidget(self)
            widget.index = i
            widget.setMinimumSize(160, 120)

            # 连接点击信号
            widget.selectionChanged.connect(self.on_window_selected)

            self.grid_layout.addWidget(widget, row, col)
            self.video_widgets.append(widget)
        
        # 重置选择状态
        self.current_selected_index = -1

    def on_window_selected(self, index):
        """处理窗口选中事件"""
        print(f"窗口选择: {index}")
        
        # 清除之前的选择
        if self.current_selected_index != -1 and self.current_selected_index < len(self.video_widgets):
            prev_widget = self.video_widgets[self.current_selected_index]
            prev_widget.selectCancle()

        # 设置新选择
        self.current_selected_index = index
        if index != -1:
            widget = self.video_widgets[index]
            widget.select()

        # 发射信号
        self.windowSelected.emit(index)

    def _start_preview(self, window_index, channel_data):
        """在指定窗口启动预览"""
        print(f"\n>>>>>> 在窗口 {window_index} 启动预览 <<<<<<")
        print(f"设备: {channel_data['device_name']}")
        print(f"通道: {channel_data['channel_num']}")

        # 获取目标窗口
        if 0 <= window_index < len(self.video_widgets):
            widget = self.video_widgets[window_index]
            
            # 存储通道数据到窗口组件
            widget.setProperty('channel_data', channel_data)
            
            print("视频预览数据准备完成")
        else:
            print("错误：无效的窗口索引！")

    def clear_preview(self, window_index):
        """清理指定窗口的预览"""
        if 0 <= window_index < len(self.video_widgets):
            widget = self.video_widgets[window_index]
            user_id = widget.property('user_id')
            preview_handle = widget.property('preview_handle')

            if preview_handle:
                # 停止预览
                pass
            if user_id:
                # 登出设备
                pass

            widget.setProperty('user_id', None)
            widget.setProperty('preview_handle', None)
            widget.setProperty('channel_data', None)

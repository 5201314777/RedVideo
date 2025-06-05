import functools
import sys

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import QWidget, QVBoxLayout

from demo.HikSDK.HCNetSDK import netsdkdllpath
from demo.HikSDK.PlayCtrl import playM4dllpath
from demo.VideoPreview.VideoOperationBar import VideoOperationBar
from demo.VideoPreview.deviceTree import DeviceTree
from demo.VideoPreview.videoView import VideoView
from demo.VideoPreview.logger import Logger

from demo.VideoPreview.videoWidget import VideoWidget
from demo.VideoPreview.machineOperationBar import OperationBar
from demo.VideoPreview.DeviceController import DeviceController

import ctypes


class VideoPreview(QtWidgets.QMainWindow):
    """
    主窗口类，用于显示视频预览和设备树。
    """

    def __init__(self):
        super(VideoPreview, self).__init__()
        self.pending_channel_data = None  # 暂存设备树传来的通道数据
        self.selected_window_index = -1  # 当前选中的视频窗口索引
        self.initialize_UI()


    def initialize_UI(self):
        self.resize(1500, 1000)
        # 加载SDK库
        self.Objdll = ctypes.cdll.LoadLibrary(netsdkdllpath)
        self.Playctrldll = ctypes.cdll.LoadLibrary(playM4dllpath)
        self.Objdll.NET_DVR_Init()

        #初始化设备控制器
        self.device_controller = DeviceController(self.Objdll, self.Playctrldll)

        # 创建设备树
        self.device_tree = DeviceTree(controller=self.device_controller)

        # 创建视频视图
        self.video_view = VideoView()
        self.VideooperationBar = VideoOperationBar(self.Objdll, self.Playctrldll, self.video_view)
        # 连接信号
        self.device_tree.channelClicked.connect(self.handle_channel_click)
        self.video_view.windowSelected.connect(self.handle_window_selected)

        # 创建日志记录器
        self.logger = Logger()
        self.OperationBar = OperationBar()
        
        # 设置云台控制面板的设备控制器
        self.OperationBar.set_device_controller(self.device_controller)

        # 创建主布局和容器
        self.main_layout = QtWidgets.QHBoxLayout()
        self.main_layout.addWidget(self._create_device_tree_container())
        self.main_layout.addWidget(self._create_center_container())
        self.main_layout.addWidget(self._create_operation_container())
        # 设置中心部件
        central_widget = QtWidgets.QWidget()
        central_widget.setLayout(self.main_layout)
        self.setCentralWidget(central_widget)

    def _create_device_tree_container(self):
        """
        创建并配置设备树的容器。
        """
        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)
        container.setFixedWidth(250)
        layout.addWidget(self.device_tree)
        return container

    def _create_center_container(self):
        """
        创建并配置中心容器，包含视频视图和日志记录器。
        """
        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.video_view)
        layout.addWidget(self.VideooperationBar)

        layout.addWidget(self.logger)
        self.logger.setFixedHeight(150)
        return container

    def _create_operation_container(self):
        container = QtWidgets.QWidget()

        layout = QtWidgets.QVBoxLayout(container)
        container.setFixedWidth(280)
        container.setStyleSheet("QWidget { background-color: white; }")
        layout.addWidget(self.OperationBar)
        return container

    def handle_channel_click(self, channel_data):
        """处理设备通道点击信号"""
        print("\n***** 主窗口收到设备通道信号 *****")
        print("通道数据:", channel_data)

        # 验证数据完整性
        required_fields = ['ip', 'port', 'username', 'password', 'channel_num']
        if not all(field in channel_data for field in required_fields):
            print("错误：收到不完整的数据！")
            return

        # 暂存通道数据
        self.pending_channel_data = channel_data
        print("通道数据已暂存")
        
        # 更新云台控制面板的设备信息
        if 'user_id' in channel_data and channel_data['user_id'] != -1:
            self.OperationBar.set_current_device(channel_data['user_id'], channel_data['channel_num'])
        
        # 如果有选中的窗口，将通道数据存储到窗口
        if self.selected_window_index != -1:
            self.store_channel_data()

    def handle_window_selected(self, window_index):
        """处理视频窗口选中信号"""
        print(f"\n***** 主窗口收到窗口选中信号: {window_index} *****")
        self.selected_window_index = window_index

        # 如果有暂存的通道数据，将其存储到新选中的窗口
        if self.pending_channel_data is not None:
            self.store_channel_data()

    def store_channel_data(self):
        """将通道数据存储到选中的窗口"""
        if self.selected_window_index == -1 or self.pending_channel_data is None:
            return
            
        # 获取选中的窗口
        selected_window = self.video_view.video_widgets[self.selected_window_index]
        
        # 存储通道数据到窗口
        selected_window.setProperty('channel_data', self.pending_channel_data)
        print(f"通道数据已存储到窗口 {self.selected_window_index}")
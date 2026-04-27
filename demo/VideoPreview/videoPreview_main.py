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
        
        # 连接视频窗口信息更新信号
        for widget in self.video_view.video_widgets:
            widget.info_updated.connect(self.handle_window_info_updated)
        
        # 初始化热成像温度管理器
        from demo.VideoPreview.thermal_temperature_manager import ThermalTemperatureManager, ThermalTemperatureDisplay
        self.thermal_manager = ThermalTemperatureManager(self.device_controller)
        self.thermal_display = ThermalTemperatureDisplay(self.thermal_manager)
        
        # 为每个视频窗口设置热成像温度显示
        for i, widget in enumerate(self.video_view.video_widgets):
            self.thermal_display.set_video_widget(i, widget)
        
        # 添加窗口关联菜单
        self._add_window_association_menu()

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
    
    def handle_window_info_updated(self, window_index, info_dict):
        """处理窗口信息更新"""
        print(f"窗口 {window_index} 信息已更新:")
        print(f"  温度阈值: {info_dict.get('temp_threshold')}°C")
        print(f"  区域标识: {info_dict.get('area_identifier')}")
        if info_dict.get('device_info'):
            device_name = info_dict['device_info'].get('name', '未知设备')
            device_ip = info_dict['device_info'].get('ip', '未知IP')
            print(f"  设备: {device_name} ({device_ip})")
    
    def _add_window_association_menu(self):
        """添加窗口关联菜单"""
        # 获取菜单栏
        menubar = self.menuBar()
        
        # 创建窗口菜单
        window_menu = menubar.addMenu("窗口")
        
        # 创建关联子菜单
        association_menu = window_menu.addMenu("窗口关联")
        
        # 为每个窗口创建关联选项
        for i in range(len(self.video_view.video_widgets)):
            for j in range(i + 1, len(self.video_view.video_widgets)):
                action = association_menu.addAction(f"关联窗口 {i+1} 和窗口 {j+1}")
                action.triggered.connect(lambda checked, idx1=i, idx2=j: self.associate_windows(idx1, idx2))
    
    def associate_windows(self, window_index1, window_index2):
        """关联两个窗口"""
        self.video_view.associate_windows(window_index1, window_index2)

    def store_channel_data(self):
        """将通道数据存储到选中的窗口"""
        if self.selected_window_index == -1 or self.pending_channel_data is None:
            return
            
        # 获取选中的窗口
        selected_window = self.video_view.video_widgets[self.selected_window_index]
        
        # 存储通道数据到窗口
        selected_window.setProperty('channel_data', self.pending_channel_data)
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        print("主窗口关闭")
        
        # 清理热成像温度管理器资源
        if hasattr(self, 'thermal_manager'):
            self.thermal_manager.cleanup()
        if hasattr(self, 'thermal_display'):
            self.thermal_display.cleanup()
            
        event.accept()
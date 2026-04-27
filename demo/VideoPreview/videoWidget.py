from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtGui import QImage, QFont
from PyQt5.QtCore import Qt
import json
import os


class VideoWidget(QtWidgets.QWidget):
    """
     播放视频窗口
    """
    selectionChanged = QtCore.pyqtSignal(int)  # 添加一个信号
    enlargeWindow = QtCore.pyqtSignal(int)
    info_updated = QtCore.pyqtSignal(int, dict)  # 信息更新信号
    
    def __init__(self, parent=None):
        super(VideoWidget, self).__init__(parent)
        self.setStyleSheet("QWidget {background-color: white;}")
        self.widget = QtWidgets.QLabel(self)
        self.index = -1
        self.selected = False
        self.setContentsMargins(0,0,0,0)
        
        # 窗口信息
        self.device_info = None  # 设备信息
        self.temp_threshold = 37.3  # 默认温度阈值
        self.area_identifier = ""  # 区域标识
        self.overtemp = False  # 是否超温
        self.associated_window_index = -1  # 关联的窗口索引（用于正常图像和红外图像的关联）
        self.current_temperature = None  # 当前温度
        
        # 创建布局
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(2, 2, 2, 2)
        self.layout.setSpacing(0)
        
        # 创建信息栏
        self.info_bar = QtWidgets.QWidget(self)
        self.info_bar.setStyleSheet("QWidget {background-color: #f0f0f0; border-bottom: 1px solid #ddd;}")
        self.info_bar.setFixedHeight(80)
        
        # 信息栏布局
        self.info_layout = QtWidgets.QVBoxLayout(self.info_bar)
        self.info_layout.setContentsMargins(4, 4, 4, 4)
        self.info_layout.setSpacing(2)
        
        # 第一行：设备信息和温度阈值
        self.top_row = QtWidgets.QHBoxLayout()
        
        # 设备信息标签
        self.device_label = QtWidgets.QLabel("未连接设备")
        self.device_label.setStyleSheet("font-size: 10px; font-weight: bold;")
        self.top_row.addWidget(self.device_label)
        
        # 温度阈值显示
        self.temp_layout = QtWidgets.QHBoxLayout()
        self.temp_label = QtWidgets.QLabel("温度阈值:")
        self.temp_label.setStyleSheet("font-size: 10px;")
        
        self.temp_input = QtWidgets.QLineEdit(str(self.temp_threshold))
        self.temp_input.setStyleSheet("font-size: 10px; width: 60px;")
        self.temp_input.setValidator(QtGui.QDoubleValidator(0, 100, 1))
        
        self.celsius_label = QtWidgets.QLabel("°C")
        self.celsius_label.setStyleSheet("font-size: 10px;")
        
        self.temp_layout.addWidget(self.temp_label)
        self.temp_layout.addWidget(self.temp_input)
        self.temp_layout.addWidget(self.celsius_label)
        
        self.top_row.addLayout(self.temp_layout)
        self.top_row.addStretch()
        
        # 第二行：区域标识
        self.area_layout = QtWidgets.QHBoxLayout()
        self.area_label = QtWidgets.QLabel("区域标识:")
        self.area_label.setStyleSheet("font-size: 10px;")
        
        self.area_input = QtWidgets.QLineEdit(self.area_identifier)
        self.area_input.setStyleSheet("font-size: 10px;")
        
        self.area_layout.addWidget(self.area_label)
        self.area_layout.addWidget(self.area_input)
        self.area_layout.addStretch()
        
        # 第三行：超温提示和应用按钮
        self.bottom_row = QtWidgets.QHBoxLayout()
        
        # 超温提示
        self.overtemp_label = QtWidgets.QLabel("高温")
        self.overtemp_label.setStyleSheet("font-size: 10px; color: gray;")
        
        # 应用按钮
        self.apply_btn = QtWidgets.QPushButton("应用")
        self.apply_btn.setStyleSheet("font-size: 10px; padding: 2px;")
        self.apply_btn.setFixedSize(40, 20)
        self.apply_btn.clicked.connect(self.on_apply)
        
        self.bottom_row.addWidget(self.overtemp_label)
        self.bottom_row.addStretch()
        self.bottom_row.addWidget(self.apply_btn)
        
        # 将所有行添加到信息栏布局
        self.info_layout.addLayout(self.top_row)
        self.info_layout.addLayout(self.area_layout)
        self.info_layout.addLayout(self.bottom_row)
        
        # 添加信息栏和视频窗口到主布局
        self.layout.addWidget(self.info_bar)
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
    
    def on_apply(self):
        """应用按钮点击事件"""
        # 获取输入的温度阈值
        try:
            temp_value = float(self.temp_input.text())
            self.temp_threshold = temp_value
        except ValueError:
            pass
        
        # 获取输入的区域标识
        self.area_identifier = self.area_input.text()
        
        # 保存信息
        self.save_info()
        
        # 检查是否超温
        self.check_overtemp()
        
        # 发送信息更新信号
        info_dict = {
            'temp_threshold': self.temp_threshold,
            'area_identifier': self.area_identifier,
            'device_info': self.device_info
        }
        self.info_updated.emit(self.index, info_dict)
        
        # 更新关联的窗口
        self.update_associated_window()
        
        print(f"窗口 {self.index} 应用信息: 温度阈值={self.temp_threshold}, 区域标识={self.area_identifier}")
    
    def set_device_info(self, device_info):
        """设置设备信息"""
        self.device_info = device_info
        if device_info:
            device_name = device_info.get('name', '未知设备')
            device_ip = device_info.get('ip', '未知IP')
            self.device_label.setText(f"{device_name} ({device_ip})")
            # 加载该设备的保存信息
            self.load_info()
        else:
            self.device_label.setText("未连接设备")
    
    def set_overtemp(self, overtemp):
        """设置超温状态"""
        self.overtemp = overtemp
        if overtemp:
            self.overtemp_label.setStyleSheet("font-size: 10px; color: red; font-weight: bold;")
        else:
            self.overtemp_label.setStyleSheet("font-size: 10px; color: gray;")
    
    def update_temperature(self, temperature):
        """更新当前温度"""
        self.current_temperature = temperature
        # 检查是否超温
        self.check_overtemp()
    
    def check_overtemp(self):
        """检查是否超温"""
        if self.current_temperature is not None:
            is_overtemp = self.current_temperature > self.temp_threshold
            self.set_overtemp(is_overtemp)
            print(f"窗口 {self.index} 温度检查: 当前温度={self.current_temperature}")
    
    def get_info(self):
        """获取窗口信息"""
        return {
            'temp_threshold': self.temp_threshold,
            'area_identifier': self.area_identifier,
            'device_info': self.device_info,
            'overtemp': self.overtemp
        }
    
    def save_info(self):
        """保存窗口信息到文件"""
        if not self.device_info:
            return
        
        try:
            # 确保配置目录存在
            config_dir = os.path.join(os.path.dirname(__file__), 'config')
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
            
            # 生成配置文件名
            device_ip = self.device_info.get('ip', 'unknown')
            config_file = os.path.join(config_dir, f'device_{device_ip}_window_{self.index}.json')
            
            # 保存信息
            info = {
                'temp_threshold': self.temp_threshold,
                'area_identifier': self.area_identifier
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(info, f, ensure_ascii=False, indent=2)
                
            print(f"窗口 {self.index} 信息已保存到: {config_file}")
        except Exception as e:
            print(f"保存窗口信息失败: {str(e)}")
    
    def load_info(self):
        """从文件加载窗口信息"""
        if not self.device_info:
            return
        
        try:
            # 生成配置文件名
            device_ip = self.device_info.get('ip', 'unknown')
            config_file = os.path.join(os.path.dirname(__file__), 'config', f'device_{device_ip}_window_{self.index}.json')
            
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    info = json.load(f)
                    
                    # 更新温度阈值
                    if 'temp_threshold' in info:
                        self.temp_threshold = info['temp_threshold']
                        self.temp_input.setText(str(self.temp_threshold))
                    
                    # 更新区域标识
                    if 'area_identifier' in info:
                        self.area_identifier = info['area_identifier']
                        self.area_input.setText(self.area_identifier)
                    
                    print(f"窗口 {self.index} 信息已从 {config_file} 加载")
        except Exception as e:
            print(f"加载窗口信息失败: {str(e)}")
    
    def update_associated_window(self):
        """更新关联的窗口"""
        if self.associated_window_index == -1:
            return
        
        try:
            # 获取父级VideoView
            parent_widget = self.parent()
            if hasattr(parent_widget, 'video_widgets'):
                video_widgets = parent_widget.video_widgets
                if 0 <= self.associated_window_index < len(video_widgets):
                    associated_widget = video_widgets[self.associated_window_index]
                    
                    # 更新关联窗口的设置
                    associated_widget.temp_threshold = self.temp_threshold
                    associated_widget.area_identifier = self.area_identifier
                    
                    # 更新UI
                    associated_widget.temp_input.setText(str(self.temp_threshold))
                    associated_widget.area_input.setText(self.area_identifier)
                    
                    # 保存关联窗口的信息
                    associated_widget.save_info()
                    
                    # 发送信息更新信号
                    info_dict = {
                        'temp_threshold': self.temp_threshold,
                        'area_identifier': self.area_identifier,
                        'device_info': associated_widget.device_info
                    }
                    associated_widget.info_updated.emit(associated_widget.index, info_dict)
                    
                    print(f"关联窗口 {self.associated_window_index} 已更新: 温度阈值={self.temp_threshold}, 区域标识={self.area_identifier}")
        except Exception as e:
            print(f"更新关联窗口失败: {str(e)}")
    
    def set_associated_window(self, window_index):
        """设置关联的窗口索引"""
        self.associated_window_index = window_index
        print(f"窗口 {self.index} 关联到窗口 {window_index}")
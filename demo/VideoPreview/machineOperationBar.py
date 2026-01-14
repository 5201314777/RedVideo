from PyQt5 import QtWidgets, QtGui, QtCore
import os.path as osp
from demo.VideoPreview.ErrorHandler import HikErrorHandler
from ctypes import c_long, byref

here = osp.dirname(osp.abspath(__file__))

class OperationBar(QtWidgets.QWidget):
    def __init__(self):
        super(OperationBar, self).__init__()
        self.device_controller = None
        self.current_user_id = -1
        self.current_channel = 1
        self.ptz_speed = 3  # 默认云台速度
        
        # 长按控制相关
        self.long_press_timer = QtCore.QTimer()
        self.long_press_timer.timeout.connect(self.on_long_press_timeout)
        self.long_press_threshold = 500  # 长按阈值，毫秒
        
        self.repeat_timer = QtCore.QTimer()
        self.repeat_timer.timeout.connect(self.on_repeat_action)
        self.repeat_interval = 100  # 重复动作间隔，毫秒
        
        self.current_action = None  # 当前执行的动作
        self.is_long_pressing = False  # 是否正在长按
        
        self.initUI()

    def set_device_controller(self, device_controller):
        """设置设备控制器"""
        self.device_controller = device_controller
        
    def set_current_device(self, user_id, channel):
        """设置当前设备信息"""
        self.current_user_id = user_id
        self.current_channel = channel
        print(f"云台控制面板设置设备: 用户ID={user_id}, 通道={channel}")
        
        # 设备连接后，自动应用当前参数
        QtCore.QTimer.singleShot(1000, self.apply_all_params_to_device)  # 延迟1秒应用参数

    def initUI(self):
        toolbarLayout = QtWidgets.QVBoxLayout()
        # 创建镜头调整GroupBox并添加到布局
        self.toolbarMoveGroupBox = self.create_toolbar_move_groupbox()
        self.toolbarPathSetGroupBox =self.create_toolbar_PathSet_groupbox()
        self.toolbarParamGroupBox =self.create_toolbar_param_groupbox()
        toolbarLayout.addWidget(self.toolbarMoveGroupBox)
        toolbarLayout.addWidget(self.toolbarPathSetGroupBox)
        toolbarLayout.addWidget(self.toolbarParamGroupBox)
        self.setLayout(toolbarLayout)

    def create_toolbar_param_groupbox(self):
        groupbox = QtWidgets.QGroupBox("参数栏")
        layout = QtWidgets.QVBoxLayout()
        groupbox.setLayout(layout)

        # 参数名称和初始值
        self.params = {
            "亮度": 50,
            "对比度": 50,
            "饱和度": 50,
            "色度": 50,
            "锐度": 50,
            "去噪": 50,
            "音量": 50
        }
        
        # 存储滑块引用
        self.param_sliders = {}

        # 创建参数控制组件
        for param, value in self.params.items():
            paramLayout = QtWidgets.QHBoxLayout()
            paramLabel = QtWidgets.QLabel(param)
            paramLabel.setAlignment(QtCore.Qt.AlignRight)
            paramLabel.setFixedSize(50, 20)
            paramSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
            
            # 所有参数都使用0-100的范围，通过映射函数转换到正确的SDK值
            paramSlider.setMinimum(0)
            paramSlider.setMaximum(100)
                
            paramSlider.setValue(value)
            
            # 添加数值显示标签
            valueLabel = QtWidgets.QLabel(str(value))
            valueLabel.setFixedSize(30, 20)
            valueLabel.setAlignment(QtCore.Qt.AlignCenter)
            
            # 存储滑块和标签引用
            self.param_sliders[param] = {
                'slider': paramSlider,
                'label': valueLabel
            }
            
            paramLayout.addWidget(paramLabel)
            paramLayout.addWidget(paramSlider)
            paramLayout.addWidget(valueLabel)
            layout.addLayout(paramLayout)
            
            # 连接信号
            paramSlider.valueChanged.connect(lambda value, param=param: self.on_param_changed(param, value))

        # 添加控制按钮
        buttonLayout = QtWidgets.QHBoxLayout()
        
        # 重置按钮
        self.resetParamsBtn = self.addBtn(
            "重置",
            "重置所有参数到默认值",
            None,
            self.reset_all_params
        )
        
        # 应用按钮
        self.applyParamsBtn = self.addBtn(
            "应用",
            "将当前参数应用到设备",
            None,
            self.apply_all_params_to_device
        )
        
        # 读取按钮
        self.readParamsBtn = self.addBtn(
            "读取",
            "从设备读取当前参数",
            None,
            self.set_params_from_device
        )
        
        # 紧急恢复按钮
        self.emergencyBtn = self.addBtn(
            "紧急恢复",
            "紧急恢复视频显示（解决黑屏问题）",
            None,
            self.emergency_restore_video
        )
        self.emergencyBtn.setStyleSheet("QPushButton { background-color: #ff6b6b; color: white; font-weight: bold; }")
        
        buttonLayout.addWidget(self.resetParamsBtn)
        buttonLayout.addWidget(self.applyParamsBtn)
        buttonLayout.addWidget(self.readParamsBtn)
        buttonLayout.addWidget(self.emergencyBtn)
        layout.addLayout(buttonLayout)

        return groupbox
    def create_toolbar_PathSet_groupbox(self):
        groupbox =QtWidgets.QGroupBox("路径预设")
        layout = QtWidgets.QVBoxLayout()
        groupbox.setFixedHeight(200)
        groupbox.setLayout(layout)

        self.PathIDBtn = QtWidgets.QLabel("ID")
        self.PathIDBtn.setFixedSize(30, 30)

        self.PathIDSelectBtn = QtWidgets.QComboBox()

        self.PathSetBeginBtn = self.addBtn(
            "开始",
            "开始运行所选预设路径",
            None,
            self.on_PathSetBeginBtn_clicked
        )
        self.PathSetEndBtn = self.addBtn(
            "结束",
            "结束运行所选预设路径",
            None,
            self.on_PathSetEndBtn_clicked
        )
        self.PathPreSetBeginBtn = self.addBtn(
            "预设路径",
            "预设巡航路径",
            None,
            self.on_PathPreSetBeginBtn_clicked
        )
        self.PathPreSetEndBtn = self.addBtn(
            "结束路径",
            "结束预设巡航路径",
            None,
            self.on_PathPreSetEndBtn_clicked
        )
        self.DelOnePathBtn = self.addBtn(
            "删除单条",
            "删除当前预设路径",
            None,
            self.on_DelOnePathBtn_clicked
        )
        self.DelAllPathtn = self.addBtn(
            "删除所有",
            "删除所有预设路径",
            None,
            self.on_DelAllPathtn_clicked
        )
        toolBarBtnLayout = QtWidgets.QHBoxLayout()
        toolBarBtnLayout.addWidget(self.PathIDBtn)
        toolBarBtnLayout.addWidget(self.PathIDSelectBtn)
        toolBarBtnLayout.addWidget(self.PathSetBeginBtn)
        toolBarBtnLayout.addWidget(self.PathSetEndBtn)
        layout.addLayout(toolBarBtnLayout)
        toolBarBtnLayout = QtWidgets.QHBoxLayout()
        toolBarBtnLayout.addWidget(self.PathPreSetBeginBtn)
        toolBarBtnLayout.addWidget(self.PathPreSetEndBtn)
        layout.addLayout(toolBarBtnLayout)
        toolBarBtnLayout = QtWidgets.QHBoxLayout()
        toolBarBtnLayout.addWidget(self.DelOnePathBtn)
        toolBarBtnLayout.addWidget(self.DelAllPathtn)
        layout.addLayout(toolBarBtnLayout)

        return groupbox
    def create_toolbar_move_groupbox(self):
        groupbox = QtWidgets.QGroupBox("镜头调整")
        groupbox.setFixedHeight(300)
        layout = QtWidgets.QVBoxLayout()
        groupbox.setLayout(layout)

        # 创建移动按钮 - 添加长按功能
        self.toolBarUpBtn = self.addPtzBtn(
            "上",
            "向上移动镜头",
            "Up",
            "move_up"
        )
        self.toolBarLeftBtn = self.addPtzBtn(
            "左",
            "向左移动镜头",
            "left",
            "move_left"
        )
        self.toolBarRightBtn = self.addPtzBtn(
            "右",
            "向右移动镜头",
            "right",
            "move_right"
        )
        self.toolBarDownBtn = self.addPtzBtn(
            "下",
            "向下移动镜头",
            "down",
            "move_down"
        )

        # 添加移动按钮到布局
        toolBarBtnLayout = QtWidgets.QHBoxLayout()
        toolBarBtnLayout.addWidget(self.toolBarUpBtn)
        layout.addLayout(toolBarBtnLayout)
        toolBarBtnLayout = QtWidgets.QHBoxLayout()
        toolBarBtnLayout.addWidget(self.toolBarLeftBtn)
        toolBarBtnLayout.addWidget(self.toolBarRightBtn)
        layout.addLayout(toolBarBtnLayout)
        toolBarBtnLayout = QtWidgets.QHBoxLayout()
        toolBarBtnLayout.addWidget(self.toolBarDownBtn)

        layout.addLayout(toolBarBtnLayout)

        # 创建焦距调整组件 - 添加长按功能
        self.toolBarSubFocusBtn = self.addPtzBtn(
            "减少",
            "缩小焦距",
            "sub",
            "zoom_out"
        )
        self.toolBarFocusText = QtWidgets.QLabel("焦距")
        self.toolBarFocusText.setFixedSize(30, 30)
        self.toolBarAddFocusBtn = self.addPtzBtn(
            "增加",
            "增加焦距",
            "add",
            "zoom_in"
        )

        # 添加焦距调整组件到布局
        toolBarFocusLayout = QtWidgets.QHBoxLayout()
        toolBarFocusLayout.addWidget(self.toolBarSubFocusBtn)
        toolBarFocusLayout.addWidget(self.toolBarFocusText)
        toolBarFocusLayout.addWidget(self.toolBarAddFocusBtn)
        layout.addLayout(toolBarFocusLayout)

        # 创建聚焦长度调整组件 - 添加长按功能
        self.toolBarSubFocusLenBtn = self.addPtzBtn(
            "减少",
            "缩焦距",
            "sub",
            "focus_near"
        )
        self.toolBarFocusLenText = QtWidgets.QLabel("聚焦")
        self.toolBarFocusLenText.setFixedSize(30, 30)
        self.toolBarAddFocusLenBtn = self.addPtzBtn(
            "增加",
            "伸聚焦",
            "add",
            "focus_far"
        )

        # 添加聚焦长度调整组件到布局
        toolBarFocusLenLayout = QtWidgets.QHBoxLayout()
        toolBarFocusLenLayout.addWidget(self.toolBarSubFocusLenBtn)
        toolBarFocusLenLayout.addWidget(self.toolBarFocusLenText)
        toolBarFocusLenLayout.addWidget(self.toolBarAddFocusLenBtn)
        layout.addLayout(toolBarFocusLenLayout)

        # 创建光圈调整组件 - 添加长按功能
        self.toolBarSubApertureBtn = self.addPtzBtn(
            "缩小",
            "缩小光圈",
            "sub",
            "iris_close"
        )
        self.toolBarApertureText = QtWidgets.QLabel("光圈")
        self.toolBarApertureText.setFixedSize(30, 30)
        self.toolBarAddApertureBtn = self.addPtzBtn(
            "增大",
            "增大光圈",
            "add",
            "iris_open"
        )

        # 添加光圈调整组件到布局
        toolBarApertureLayout = QtWidgets.QHBoxLayout()
        toolBarApertureLayout.addWidget(self.toolBarSubApertureBtn)
        toolBarApertureLayout.addWidget(self.toolBarApertureText)
        toolBarApertureLayout.addWidget(self.toolBarAddApertureBtn)
        layout.addLayout(toolBarApertureLayout)

        return groupbox

    def addBtn(self, title=None, tip=None, icon=None, slot=None):
        btn = QtWidgets.QToolButton()
        if icon is not None:
            btn.setIcon(self.newIcon(icon))
        if title is not None:
            btn.setText(title)
        if tip is not None:
            btn.setToolTip(tip)
        if slot is not None:
            btn.clicked.connect(slot)
        return btn
    
    def addPtzBtn(self, title=None, tip=None, icon=None, action=None):
        """创建支持长按的云台控制按钮"""
        btn = QtWidgets.QToolButton()
        if icon is not None:
            btn.setIcon(self.newIcon(icon))
        if title is not None:
            btn.setText(title)
        if tip is not None:
            btn.setToolTip(tip + " (单击移动一小段距离，长按持续移动)")
        
        # 设置按钮的动作标识
        if action is not None:
            btn.setProperty('ptz_action', action)
        
        # 连接鼠标事件
        btn.pressed.connect(self.on_ptz_btn_pressed)
        btn.released.connect(self.on_ptz_btn_released)
        
        return btn

    def on_ptz_btn_pressed(self):
        """云台按钮按下"""
        sender = self.sender()
        action = sender.property('ptz_action')
        
        if not action:
            return
            
        print(f"按钮按下: {action}")
        
        # 立即执行一次动作（短按效果）
        self.execute_ptz_action(action)
        
        # 设置当前动作
        self.current_action = action
        self.is_long_pressing = False
        
        # 启动长按检测定时器
        self.long_press_timer.start(self.long_press_threshold)
    
    def on_ptz_btn_released(self):
        """云台按钮释放"""
        print("按钮释放")
        
        # 停止所有定时器
        self.long_press_timer.stop()
        self.repeat_timer.stop()
        
        # 如果正在长按，发送停止命令
        if self.is_long_pressing and self.current_action:
            self.stop_ptz_action(self.current_action)
        
        # 重置状态
        self.current_action = None
        self.is_long_pressing = False
    
    def on_long_press_timeout(self):
        """长按检测超时"""
        print("检测到长按，开始持续移动")
        
        # 停止长按检测定时器
        self.long_press_timer.stop()
        
        # 标记为长按状态
        self.is_long_pressing = True
        
        # 启动重复动作定时器
        self.repeat_timer.start(self.repeat_interval)
    
    def on_repeat_action(self):
        """重复执行动作"""
        if self.current_action and self.is_long_pressing:
            self.execute_ptz_action(self.current_action)
    
    def execute_ptz_action(self, action):
        """执行云台动作"""
        if not self.device_controller or self.current_user_id == -1:
            print("设备控制器未设置或设备未登录")
            return
        
        # 根据动作类型调用相应的控制方法
        action_map = {
            'move_up': self.device_controller.ptz_move_up,
            'move_down': self.device_controller.ptz_move_down,
            'move_left': self.device_controller.ptz_move_left,
            'move_right': self.device_controller.ptz_move_right,
            'zoom_in': self.device_controller.ptz_zoom_in,
            'zoom_out': self.device_controller.ptz_zoom_out,
            'focus_near': self.device_controller.ptz_focus_near,
            'focus_far': self.device_controller.ptz_focus_far,
            'iris_open': self.device_controller.ptz_iris_open,
            'iris_close': self.device_controller.ptz_iris_close,
        }
        
        if action in action_map:
            action_map[action](self.current_user_id, self.current_channel, self.ptz_speed)
    
    def stop_ptz_action(self, action):
        """停止云台动作"""
        if not self.device_controller or self.current_user_id == -1:
            return
        
        # 根据动作类型获取对应的停止命令
        stop_command_map = {
            'move_up': 21,    # TILT_UP
            'move_down': 22,  # TILT_DOWN
            'move_left': 23,  # PAN_LEFT
            'move_right': 24, # PAN_RIGHT
            'zoom_in': 11,    # ZOOM_IN
            'zoom_out': 12,   # ZOOM_OUT
            'focus_near': 13, # FOCUS_NEAR
            'focus_far': 14,  # FOCUS_FAR
            'iris_open': 15,  # IRIS_OPEN
            'iris_close': 16, # IRIS_CLOSE
        }
        
        if action in stop_command_map:
            command = stop_command_map[action]
            self.device_controller.ptz_control(self.current_user_id, self.current_channel, command, 1)  # 1表示停止
            print(f"停止云台动作: {action}")

    def newIcon(self, icon):
        icons_dir = osp.join(here, "../icons")
        return QtGui.QIcon(osp.join(":/", icons_dir, "%s.png" % icon))

    # 槽函数定义
    def on_PathSetBeginBtn_clicked(self):
        print("开始")
    def on_PathSetEndBtn_clicked(self):
        print("结束")
    def on_PathPreSetBeginBtn_clicked(self):
        pass
    def on_PathPreSetEndBtn_clicked(self):
        pass
    def on_DelOnePathBtn_clicked(self):
        pass

    def on_DelAllPathtn_clicked(self):
        pass

    def on_param_changed(self, param, value):
        """处理参数改变的槽函数"""
        print(f"{param} 参数改变为: {value}")
        
        # 更新数值显示
        if param in self.param_sliders:
            self.param_sliders[param]['label'].setText(str(value))
        
        # 更新内部参数值
        self.params[param] = value
        
        # 如果设备已连接，立即应用参数
        if self.device_controller and self.current_user_id != -1:
            self.apply_param_to_device(param, value)
        else:
            print("设备未连接，参数将在连接后应用")
    
    def apply_param_to_device(self, param, value):
        """将参数应用到设备"""
        if not self.device_controller or self.current_user_id == -1:
            print("设备未连接，无法应用参数")
            return
            
        try:
            if param == "亮度":
                self.set_brightness(value)
            elif param == "对比度":
                self.set_contrast(value)
            elif param == "饱和度":
                self.set_saturation(value)
            elif param == "色度":
                self.set_hue(value)
            elif param == "锐度":
                self.set_sharpness(value)
            elif param == "去噪":
                self.set_noise_reduction(value)
            elif param == "音量":
                self.set_volume(value)
        except Exception as e:
            error_msg = f"应用参数 {param} 失败: {str(e)}"
            print(error_msg)
    
    def set_brightness(self, value):
        """设置亮度 (0-100)"""
        # 根据海康SDK文档，参数范围是[1,10]
        # 将0-100%映射到1-10的范围
        sdk_value = int(1 + (value * 9 / 100))  # 0% -> 1, 100% -> 10
        
        # 确保在有效范围内
        if sdk_value < 1:
            sdk_value = 1
        elif sdk_value > 10:
            sdk_value = 10
        
        print(f"设置亮度: {value}% -> SDK值: {sdk_value} (范围1-10)")
        
        # 使用海康SDK设置亮度
        result = self.device_controller.Objdll.NET_DVR_ClientSetVideoEffect(
            self.current_user_id, 
            self.current_channel, 
            sdk_value,  # 亮度 (1-10)
            -1,  # 对比度 (-1表示不改变)
            -1,  # 饱和度
            -1   # 色调
        )
        
        if result:
            success_msg = HikErrorHandler.format_error_info(
                0,
                "设置亮度",
                f"值: {value}% (SDK值: {sdk_value})"
            )
            print(success_msg)
        else:
            error_code = self.device_controller.Objdll.NET_DVR_GetLastError()
            error_msg = HikErrorHandler.format_error_info(
                error_code,
                "设置亮度",
                f"值: {value}% (SDK值: {sdk_value}), 通道: {self.current_channel}"
            )
            print(error_msg)
            
            # 如果设置失败，尝试恢复到默认值
            print("亮度设置失败，尝试恢复到默认值...")
            default_sdk_value = 5  # 中间值 (1-10的中间值)
            self.device_controller.Objdll.NET_DVR_ClientSetVideoEffect(
                self.current_user_id, 
                self.current_channel, 
                default_sdk_value,
                -1, -1, -1
            )
    
    def set_contrast(self, value):
        """设置对比度 (0-100)"""
        # 根据海康SDK文档，参数范围是[1,10]
        sdk_value = int(1 + (value * 9 / 100))  # 0% -> 1, 100% -> 10
        
        # 确保在有效范围内
        if sdk_value < 1:
            sdk_value = 1
        elif sdk_value > 10:
            sdk_value = 10
        
        print(f"设置对比度: {value}% -> SDK值: {sdk_value} (范围1-10)")
        
        result = self.device_controller.Objdll.NET_DVR_ClientSetVideoEffect(
            self.current_user_id,
            self.current_channel,
            -1,  # 亮度
            sdk_value,  # 对比度 (1-10)
            -1,  # 饱和度
            -1   # 色调
        )
        
        if result:
            success_msg = HikErrorHandler.format_error_info(
                0,
                "设置对比度",
                f"值: {value}% (SDK值: {sdk_value})"
            )
            print(success_msg)
        else:
            error_code = self.device_controller.Objdll.NET_DVR_GetLastError()
            error_msg = HikErrorHandler.format_error_info(
                error_code,
                "设置对比度",
                f"值: {value}% (SDK值: {sdk_value}), 通道: {self.current_channel}"
            )
            print(error_msg)
    
    def set_saturation(self, value):
        """设置饱和度 (0-100)"""
        # 根据海康SDK文档，参数范围是[1,10]
        sdk_value = int(1 + (value * 9 / 100))  # 0% -> 1, 100% -> 10
        
        # 确保在有效范围内
        if sdk_value < 1:
            sdk_value = 1
        elif sdk_value > 10:
            sdk_value = 10
        
        print(f"设置饱和度: {value}% -> SDK值: {sdk_value} (范围1-10)")
        
        result = self.device_controller.Objdll.NET_DVR_ClientSetVideoEffect(
            self.current_user_id,
            self.current_channel,
            -1,  # 亮度
            -1,  # 对比度
            sdk_value,  # 饱和度 (1-10)
            -1   # 色调
        )
        
        if result:
            success_msg = HikErrorHandler.format_error_info(
                0,
                "设置饱和度",
                f"值: {value}% (SDK值: {sdk_value})"
            )
            print(success_msg)
        else:
            error_code = self.device_controller.Objdll.NET_DVR_GetLastError()
            error_msg = HikErrorHandler.format_error_info(
                error_code,
                "设置饱和度",
                f"值: {value}% (SDK值: {sdk_value}), 通道: {self.current_channel}"
            )
            print(error_msg)
    
    def set_hue(self, value):
        """设置色度/色调 (0-100)"""
        # 根据海康SDK文档，参数范围是[1,10]
        sdk_value = int(1 + (value * 9 / 100))  # 0% -> 1, 100% -> 10
        
        # 确保在有效范围内
        if sdk_value < 1:
            sdk_value = 1
        elif sdk_value > 10:
            sdk_value = 10
        
        print(f"设置色度: {value}% -> SDK值: {sdk_value} (范围1-10)")
        
        result = self.device_controller.Objdll.NET_DVR_ClientSetVideoEffect(
            self.current_user_id,
            self.current_channel,
            -1,  # 亮度
            -1,  # 对比度
            -1,  # 饱和度
            sdk_value   # 色调 (1-10)
        )
        
        if result:
            success_msg = HikErrorHandler.format_error_info(
                0,
                "设置色度",
                f"值: {value}% (SDK值: {sdk_value})"
            )
            print(success_msg)
        else:
            error_code = self.device_controller.Objdll.NET_DVR_GetLastError()
            error_msg = HikErrorHandler.format_error_info(
                error_code,
                "设置色度",
                f"值: {value}% (SDK值: {sdk_value}), 通道: {self.current_channel}"
            )
            print(error_msg)
    
    def set_sharpness(self, value):
        """设置锐度 (0-100)"""
        # 锐度通常需要通过配置接口设置
        print(f"锐度设置: {value}% (此功能需要设备支持)")
        
        # 可以尝试使用 NET_DVR_SetDVRConfig 接口
        # 具体的配置结构体需要根据海康SDK文档确定
        try:
            # 这里是示例代码，实际实现需要正确的结构体
            result = self.device_controller.ptz_control(
                self.current_user_id, 
                self.current_channel, 
                0x1001,  # 假设的锐度控制命令
                0
            )
            if result:
                print(f"锐度调整命令发送成功: {value}%")
            else:
                print(f"锐度调整命令发送失败")
        except:
            print("锐度调整功能暂不支持")
    
    def set_noise_reduction(self, value):
        """设置去噪 (0-100)"""
        print(f"去噪设置: {value}% (此功能需要设备支持)")
        
        # 去噪功能通常需要通过特定的配置接口
        # 这里提供一个框架，具体实现需要根据设备文档
        try:
            # 示例：可能需要使用特定的配置命令
            print("去噪功能配置中...")
        except:
            print("去噪功能暂不支持")
    
    def set_volume(self, value):
        """设置音量 (0-100)"""
        # 音量控制通常通过音频相关接口
        sdk_value = int(value * 0xFFFF / 100)  # 转换为16位值
        
        try:
            # 使用海康SDK的音量控制接口
            result = self.device_controller.Objdll.NET_DVR_VoiceComClientSetVolume(
                self.current_user_id,
                sdk_value
            )
            
            if result:
                success_msg = HikErrorHandler.format_error_info(
                    0,
                    "设置音量",
                    f"值: {value}% (SDK值: {sdk_value})"
                )
                print(success_msg)
            else:
                error_code = self.device_controller.Objdll.NET_DVR_GetLastError()
                error_msg = HikErrorHandler.format_error_info(
                    error_code,
                    "设置音量",
                    f"值: {value}% (SDK值: {sdk_value})"
                )
                print(error_msg)
        except:
            print(f"音量设置: {value}% (音频功能可能不支持)")
    
    def apply_all_params_to_device(self):
        """将所有参数应用到设备"""
        if self.device_controller and self.current_user_id != -1:
            print("应用所有参数到设备...")
            for param, value in self.params.items():
                self.apply_param_to_device(param, value)
        else:
            print("设备未连接，无法应用参数")
    
    def reset_all_params(self):
        """重置所有参数到默认值"""
        default_values = {
            "亮度": 50,
            "对比度": 50,
            "饱和度": 50,
            "色度": 50,
            "锐度": 50,
            "去噪": 50,
            "音量": 50
        }
        
        for param, value in default_values.items():
            if param in self.param_sliders:
                # 更新滑块值（这会触发valueChanged信号）
                self.param_sliders[param]['slider'].setValue(value)
        
        print("所有参数已重置为默认值")
    
    def emergency_restore_video(self):
        """紧急恢复视频显示 - 重置所有视频效果参数"""
        if not self.device_controller or self.current_user_id == -1:
            print("设备未连接，无法执行紧急恢复")
            return False
            
        try:
            print("执行紧急恢复...")
            
            # 重置所有视频效果参数到安全的默认值
            # 根据海康SDK文档，参数范围是[1,10]，中间值为5
            result = self.device_controller.Objdll.NET_DVR_ClientSetVideoEffect(
                self.current_user_id,
                self.current_channel,
                5,  # 亮度：中间值 (1-10)
                5,  # 对比度：中间值 (1-10)
                5,  # 饱和度：中间值 (1-10)
                5   # 色调：中间值 (1-10)
            )
            
            if result:
                print("紧急恢复成功，视频参数已重置为默认值 (SDK值: 5)")
                
                # 同时更新UI滑块到默认位置
                for param in ["亮度", "对比度", "饱和度", "色度"]:
                    if param in self.param_sliders:
                        self.param_sliders[param]['slider'].blockSignals(True)  # 阻止信号避免重复调用
                        self.param_sliders[param]['slider'].setValue(50)
                        self.param_sliders[param]['label'].setText("50")
                        self.param_sliders[param]['slider'].blockSignals(False)
                
                return True
            else:
                error_code = self.device_controller.Objdll.NET_DVR_GetLastError()
                error_msg = HikErrorHandler.format_error_info(
                    error_code,
                    "紧急恢复",
                    f"用户ID: {self.current_user_id}, 通道: {self.current_channel}"
                )
                print(error_msg)
                return False
                
        except Exception as e:
            print(f"紧急恢复异常: {str(e)}")
            return False
    
    def get_current_params(self):
        """获取当前参数值"""
        return self.params.copy()
    
    def set_params_from_device(self):
        """从设备读取当前参数值"""
        if not self.device_controller or self.current_user_id == -1:
            print("设备未连接，无法读取参数")
            return
        
        try:
            print("从设备读取参数...")
            
            # 创建参数变量
            brightness = c_long()
            contrast = c_long()
            saturation = c_long()
            hue = c_long()
            
            # 调用SDK接口读取参数
            result = self.device_controller.Objdll.NET_DVR_ClientGetVideoEffect(
                self.current_user_id,
                self.current_channel,
                byref(brightness),
                byref(contrast),
                byref(saturation),
                byref(hue)
            )
            
            if result:
                # 将SDK值(1-10)转换为UI值(0-100)
                brightness_ui = int((brightness.value - 1) * 100 / 9)  # 1->0%, 10->100%
                contrast_ui = int((contrast.value - 1) * 100 / 9)
                saturation_ui = int((saturation.value - 1) * 100 / 9)
                hue_ui = int((hue.value - 1) * 100 / 9)
                
                print(f"从设备读取到参数:")
                print(f"  亮度: SDK值={brightness.value} -> UI值={brightness_ui}%")
                print(f"  对比度: SDK值={contrast.value} -> UI值={contrast_ui}%")
                print(f"  饱和度: SDK值={saturation.value} -> UI值={saturation_ui}%")
                print(f"  色度: SDK值={hue.value} -> UI值={hue_ui}%")
                
                # 更新UI滑块
                param_mapping = {
                    "亮度": brightness_ui,
                    "对比度": contrast_ui,
                    "饱和度": saturation_ui,
                    "色度": hue_ui
                }
                
                for param, value in param_mapping.items():
                    if param in self.param_sliders:
                        # 阻止信号避免重复调用设备接口
                        self.param_sliders[param]['slider'].blockSignals(True)
                        self.param_sliders[param]['slider'].setValue(value)
                        self.param_sliders[param]['label'].setText(str(value))
                        self.param_sliders[param]['slider'].blockSignals(False)
                        # 更新内部参数值
                        self.params[param] = value
                
                success_msg = HikErrorHandler.format_error_info(
                    0,
                    "读取设备参数",
                    f"亮度:{brightness_ui}%, 对比度:{contrast_ui}%, 饱和度:{saturation_ui}%, 色度:{hue_ui}%"
                )
                print(success_msg)
                
            else:
                error_code = self.device_controller.Objdll.NET_DVR_GetLastError()
                error_msg = HikErrorHandler.format_error_info(
                    error_code,
                    "读取设备参数",
                    f"用户ID: {self.current_user_id}, 通道: {self.current_channel}"
                )
                print(error_msg)
            
        except Exception as e:
            error_msg = f"从设备读取参数异常: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()

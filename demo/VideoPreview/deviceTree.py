import sys
from ctypes import*

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QMenu, QAction, QMessageBox, QInputDialog
from PyQt5.QtCore import Qt, QPoint
from PyQt5 import QtCore
from demo.HikSDK.HCNetSDK import NET_DVR_CHANNEL_CFG, NET_DVR_GET_CHANNEL_CFG,NET_DVR_IPDEVINFO_V31,NET_DVR_IPPARACFG_V40
from demo.VideoPreview.ConfigManager import ConfigManager
from demo.VideoPreview.DeviceDialog import DeviceDialog


class DeviceTree(QTreeWidget):
    # 新增信号
    channelClicked = QtCore.pyqtSignal(dict)  # 传递设备数据的信号

    def __init__(self, parent=None,controller=None):
        super(DeviceTree, self).__init__(parent)
        self.controller = controller  # 保存控制器实例
        self.setHeaderLabels(['设备列表'])
        self.setContextMenuPolicy(Qt.CustomContextMenu)  # 右击事件
        self.customContextMenuRequested.connect(self.on_context_menu)
        self.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.rootDevices = []
        self.devicesInfo = []
        self.deviceNum = 0  # 接入设备数
        self.config_manager = ConfigManager()
        self.load_saved_devices()
        self.expandAll()  # 展开所有节点
        self.itemClicked.connect(self.on_item_clicked)  # 确保连接点击信号

    def add_device(self, device_name, parent=None, device_info=None, save_to_file=True):
        # UI部分：创建根节点
        if parent is None:
            root_item = QTreeWidgetItem([f'{device_name}'])
            self.addTopLevelItem(root_item)
            self.rootDevices.append(root_item)
            parent = root_item  # 设置parent为新创建的根节点
            self.deviceNum += 1
            self.expandItem(root_item)

        # 获取通道数
        channelNum = self.get_channel_count(device_info) if device_info else 4

        # UI部分：添加通道子节点
        for i in range(channelNum):
            channel_item = QTreeWidgetItem([f'{device_name}-通道 {i + 1}'])
            parent.addChild(channel_item)

        # 数据处理与持久化
        if device_info:
            device_info['channelNum'] = channelNum  # 更新通道信息

            # 1. 更新内存中的列表 (避免重复添加)
            # 检查列表中是否已存在该设备（通过名字判断）
            exists = False
            for index, d in enumerate(self.devicesInfo):
                if d.get('name') == device_info['name']:
                    self.devicesInfo[index] = device_info  # 如果存在则更新
                    exists = True
                    break

            if not exists:
                self.devicesInfo.append(device_info)  # 不存在则追加

            print(f"设备处理完成: {device_info['name']}")

            # 2. 仅在手动添加时记录日志（加载时通常不需要重复记录添加日志）
            if save_to_file:
                self._log_event(True, "添加设备",
                                f"{device_info['name']} ({device_info['address']}:{device_info['port']})",
                                f"通道数: {channelNum}")

            # 3. 关键修复：保存到文件
            if save_to_file:
                if self.config_manager.save_devices(self.devicesInfo):
                    print("配置已保存到文件")
                else:
                    print("配置保存失败")
    def get_channel_count(self, device_info):
        DEFAULT_CHANNELS = 1
        print("\n====== 开始获取通道信息 ======")

        if not device_info:
            print("警告：设备信息为空，返回默认通道数:", DEFAULT_CHANNELS)
            self._log_event(False, "获取通道信息", "无", "设备信息为空")
            return DEFAULT_CHANNELS

        try:
            # 1. 登录设备
            print(f"尝试登录设备: {device_info['address']}:{device_info['port']}")
            user_id, device_info_v40 = self.controller.login_device(
                device_info['address'],
                device_info['port'],
                device_info['username'],
                device_info['password']
            )

            if user_id == -1:
                error_code = self.controller.Objdll.NET_DVR_GetLastError()
                print(f"登录失败，错误码: {error_code}")
                self._log_event(False, "获取通道信息", f"{device_info['name']} ({device_info['address']}:{device_info['port']})", f"登录失败，错误码: {error_code}")
                return DEFAULT_CHANNELS
            print("设备登录成功")

            # 2. 获取基础通道信息
            analog_channels = device_info_v40.struDeviceV30.byChanNum
            ip_chan_num = device_info_v40.struDeviceV30.byIPChanNum
            high_chan_num = device_info_v40.struDeviceV30.byHighDChanNum
            total_ip_channels = ip_chan_num + high_chan_num * 256

            print(f"基础通道信息 -> 模拟通道: {analog_channels}, IP通道: {ip_chan_num}, 高位数IP通道: {high_chan_num}")
            print(f"计算总IP通道数: {ip_chan_num} + {high_chan_num}*256 = {total_ip_channels}")

            # 3. 获取详细配置（仅当有IP通道时）
            if total_ip_channels > 0:
                print("\n设备支持IP通道，开始获取详细配置...")
                ip_para_cfg = NET_DVR_IPPARACFG_V40()
                ip_para_cfg.dwSize = sizeof(NET_DVR_IPPARACFG_V40)
                bytes_returned = c_uint32(0)

                success = self.controller.Objdll.NET_DVR_GetDVRConfig(
                    user_id,
                    0x2711,  # NET_DVR_GET_IPPARACFG_V40
                    0,
                    byref(ip_para_cfg),
                    sizeof(NET_DVR_IPPARACFG_V40),
                    byref(bytes_returned)
                )

                if success:
                    print("成功获取IP通道配置")
                    print(f"配置中的模拟通道数: {ip_para_cfg.dwAChanNum}")
                    print(f"配置中的数字通道数: {ip_para_cfg.dwDChanNum}")
                    total_channels = ip_para_cfg.dwAChanNum + ip_para_cfg.dwDChanNum
                    print(f"合计总通道数: {total_channels}")
                else:
                    error_code = self.controller.Objdll.NET_DVR_GetLastError()
                    print(f"获取IP配置失败，错误码: {error_code}")
                    print("回退使用基础模拟通道数:", analog_channels)
                    total_channels = analog_channels
            else:
                print("\n设备不支持IP通道，仅使用模拟通道")
                total_channels = analog_channels
                print(f"模拟通道数: {total_channels}")

            # 4. 登出设备
            self.controller.Objdll.NET_DVR_Logout(user_id)
            print("====== 通道检测完成 ======\n")
            
            # 记录日志
            self._log_event(True, "获取通道信息", f"{device_info['name']} ({device_info['address']}:{device_info['port']})", f"检测到 {total_channels} 个通道")
            
            return max(1, total_channels)

        except Exception as e:
            print(f"\n!!! 发生异常: {str(e)}")
            self._log_event(False, "获取通道信息", f"{device_info['name']} ({device_info['address']}:{device_info['port']})", f"异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return DEFAULT_CHANNELS

    def on_item_clicked(self, item, column):
        """点击设备通道时触发"""
        if item.parent() is not None:  # 只处理通道项
            print("\n===== 设备树点击事件开始 =====")
            try:
                channel_name = item.text(0)
                device_name = item.parent().text(0)
                print(f"点击了设备: {device_name}, 通道: {channel_name}")

                device_info = next((d for d in self.devicesInfo if d['name'] == device_name), None)

                if device_info:
                    # 先登录设备获取user_id
                    print(f"为云台控制登录设备: {device_info['address']}:{device_info['port']}")
                    user_id, device_info_v40 = self.controller.login_device(
                        device_info['address'],
                        device_info['port'],
                        device_info['username'],
                        device_info['password']
                    )
                    
                    if user_id == -1:
                        error_code = self.controller.Objdll.NET_DVR_GetLastError()
                        print(f"设备登录失败，错误码: {error_code}")
                        self._log_event(False, "选择通道", f"{device_name} - {channel_name}", f"设备登录失败，错误码: {error_code}")
                        return
                    
                    print(f"设备登录成功，用户ID: {user_id}")
                    
                    # 准备要发送的数据
                    channel_data = {
                        'type': 'hikvision',
                        'device_name': device_name,
                        'channel_name': channel_name,
                        'channel_num': int(channel_name.split()[-1]),
                        'ip': device_info['address'],
                        'port': device_info['port'],
                        'username': device_info['username'],
                        'password': device_info['password'],
                        'user_id': user_id,  # 添加用户ID用于云台控制
                        'timestamp': QtCore.QDateTime.currentDateTime().toString()
                    }
                    print("准备发射信号，数据内容:", channel_data)

                    # 发射信号
                    self.channelClicked.emit(channel_data)
                    print("信号发射成功！")
                    
                    # 记录日志
                    self._log_event(True, "选择通道", f"{device_name} - {channel_name}", "无")
                else:
                    print("警告：未找到设备信息！")
                    self._log_event(False, "选择通道", f"{device_name} - {channel_name}", "未找到设备信息")

            except Exception as e:
                print(f"点击处理发生异常: {str(e)}")
                self._log_event(False, "选择通道", f"{device_name if 'device_name' in locals() else '未知'} - {channel_name if 'channel_name' in locals() else '未知'}", f"异常: {str(e)}")
                import traceback
                traceback.print_exc()
            print("===== 设备树点击事件结束 =====\n")

    def on_context_menu(self, position):
        item = self.itemAt(position)
        menu = QMenu()

        if item is None:
            add_device_action = QAction("添加设备", self)
            add_device_action.triggered.connect(self.on_add_device)
            menu.addAction(add_device_action)
        else:
            if item.parent() is None:
                # 查看信息
                view_info_action = QAction("查看信息", self)
                view_info_action.triggered.connect(lambda: self.on_show_device(item))
                menu.addAction(view_info_action)

                delete_action = QAction("删除设备", self)
                delete_action.triggered.connect(lambda: self.on_delete_device(item))
                menu.addAction(delete_action)

        menu.exec_(self.viewport().mapToGlobal(QPoint(position)))
    def on_item_double_clicked(self,item,col):
        if item.parent() is not None:
            print(item.text(0))

    #TODO 将设备信息持久化保存# DeviceTree.py
    def on_add_device(self):
        # 创建并显示添加设备的对话框
        dialog = DeviceDialog(self)

        # 因为Dialog内部已经限制了必须填写完整才能点击Accept，
        # 所以这里不需要再弹窗提示"信息不全"
        if dialog.exec_() == QtWidgets.QDialog.Accepted:

            device_info = dialog.get_device_info()
            if not device_info: return

            device_name = device_info['name']
            device_str = f"{device_info['address']}:{device_info['port']}"

            # --- 开始合法性验证 ---
            if self.controller:
                # 调用控制器测试连接
                is_valid, msg = self.controller.device_connection_test(
                    device_info['address'],
                    device_info['port'],
                    device_info['username'],
                    device_info['password']
                )

                if is_valid:
                    # 验证成功，执行添加逻辑
                    # add_device 内部会自动记录"添加成功"的日志
                    self.add_device(device_name, device_info=device_info)
                else:
                    # 验证失败：不弹窗，直接写日志
                    print(f"设备验证失败: {msg}")
                    self._log_event(False, "添加设备", f"{device_name} ({device_str})", f"验证失败: {msg}")
            else:
                # 控制器未初始化
                self._log_event(False, "添加设备", device_name, "系统错误: 控制器未初始化")

    def on_delete_device(self, item):
        # 确认删除
        device_name = item.text(0)
        reply = QMessageBox.question(self, '删除设备',
                                     f"你确定要删除设备 '{device_name}' 吗?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            # 从树中删除项（不需要检查父节点，因为已经确保了item不是根节点）
            index = self.indexOfTopLevelItem(item)
            if index != -1:
                self.takeTopLevelItem(index)
                
                # 从设备信息列表中删除
                device_info = next((d for d in self.devicesInfo if d['name'] == device_name), None)
                if device_info:
                    self.devicesInfo.remove(device_info)
                    self.config_manager.save_devices(self.devicesInfo)
                    self._log_event(True, "删除设备", device_name, "配置已更新")
                # 记录日志
                self._log_event(True, "删除设备", device_name, "无")
            else:
                self._log_event(False, "删除设备", device_name, "未找到设备项")

    def on_show_device(self, item):
        device_name = item.text(0)
        print(device_name)
        info = next((d for d in self.devicesInfo if d['name'] == device_name), None)
        if info:
            dialog = DeviceDialog(self)
            dialog.show_device_info(info)
            dialog.exec_()
            
            # 记录日志
            self._log_event(True, "查看设备信息", device_name, "无")
        else:
            QMessageBox.warning(self, "未找到", "未找到该设备信息。")
            self._log_event(False, "查看设备信息", device_name, "未找到设备信息")
            
    def _log_event(self, success, operation, device_info, error_info):
        """记录事件到日志"""
        # 获取主窗口
        main_window = self.window()
        if hasattr(main_window, 'logger'):
            main_window.logger.add_log(success, operation, device_info, error_info)

    def load_saved_devices(self):
        """从本地文件加载设备并显示在树中"""
        saved_devices = self.config_manager.load_devices()
        for dev_info in saved_devices:
            # 这里调用 add_device 时设置 save_to_file=False，防止循环保存
            # 注意：我们需要稍微修改 add_device 方法来支持这个参数
            self.add_device(dev_info['name'], device_info=dev_info, save_to_file=False)

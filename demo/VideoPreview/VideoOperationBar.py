import functools
import sys
import os
from ctypes import c_long, c_bool, POINTER, c_char, c_ulong
import time
from datetime import datetime
from ctypes import create_string_buffer

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QFileDialog, QMessageBox
from PyQt5 import QtWidgets
from _ctypes import byref

from demo.VideoPreview.VideoThread import VideoThread
from demo.VideoPreview.videoWidget import VideoWidget
from demo.utils.tool_bar import *
from demo.utils.QtTool import *
from demo.VideoPreview.DeviceController import *
from demo.VideoPreview.ErrorHandler import HikErrorHandler

class VideoOperationBar(QtWidgets.QToolBar):
    def __init__(self,Objdll,Playctrl,video_view):
        super(VideoOperationBar, self).__init__()
        self.setStyleSheet("QToolBar { background-color: white; }")
        self.setOrientation(Qt.Horizontal)
        self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.device_controller = DeviceController(Objdll, Playctrl)
        self.video_view = video_view
        self.video_threads = {}  # 使用字典而不是列表，以窗口索引为键
        self.recording_windows = {}  # 记录正在录像的窗口
        
        # 创建录像和抓图的存储目录
        self.record_dir = r"D:\Test\Videos"  # 根据开发文档指定的路径
        self.capture_dir = r"D:\Test\Images"  # 根据开发文档指定的路径
        self._ensure_directories()
        
        action = functools.partial(newAction, self)
        # 创建一个QWidgetAction来包含窗口数选择的组合框
        selectWidNum = QtWidgets.QWidgetAction(self)
        widNumWidget = QWidget()  # 创建一个QWidget作为action的默认小部件
        selectWidNum.setDefaultWidget(widNumWidget)

        # 创建一个水平布局管理器
        widNumLayout = QtWidgets.QHBoxLayout(widNumWidget)

        # 创建标签并设置对齐方式
        selectWidNumLabel = QtWidgets.QLabel("窗口数:")
        selectWidNumLabel.setAlignment(Qt.AlignCenter)
        widNumLayout.addWidget(selectWidNumLabel)

        # 创建组合框并添加选项
        self.selectWidNumComboBox = QtWidgets.QComboBox()
        self.widNums = ['1', '4', '9', '16', '25', '36', '49', '64', '81']
        self.selectWidNumComboBox.addItems(self.widNums)
        self.selectWidNumComboBox.setCurrentIndex(1)  # 默认选择4窗口
        self.selectWidNumComboBox.currentIndexChanged.connect(self.updateVideoLayout)
        widNumLayout.addWidget(self.selectWidNumComboBox)

        startVideo = action(
            "播放",
            self.startVideo,
        )
        record = action(
            "录像",
            self.record
        )
        grabbing = action(
            "抓图",
            self.grabbing
        )
        inforce = action(
            "强制帧",
            self.inforce
        )
        self.actions = struct(
            startVideo=startVideo,
            record=record,
            grabbing=grabbing,
            inforce=inforce,
            selectWidNum=selectWidNum,
            videoOperationBar=(
                startVideo,
                record,
                grabbing,
                None,
                inforce,
                selectWidNum
            ),
        )
        addActions(self, self.actions.videoOperationBar)
        
    def _ensure_directories(self):
        """确保录像和抓图目录存在"""
        os.makedirs(self.record_dir, exist_ok=True)
        os.makedirs(self.capture_dir, exist_ok=True)
        
    def startVideo(self):
        """处理播放按钮点击事件"""
        # 检查是否有选中的窗口
        if self.video_view.current_selected_index == -1:
            print("请先选择一个视频窗口")
            self._log_event(False, "播放视频", "无", "未选择视频窗口")
            return
            
        # 获取选中的窗口索引
        window_index = self.video_view.current_selected_index
        
        # 获取选中的窗口
        selected_window = self.video_view.video_widgets[window_index]
        
        # 检查窗口是否有关联的通道数据
        channel_data = selected_window.property('channel_data')
        if not channel_data:
            print("请先选择一个设备通道")
            self._log_event(False, "播放视频", "无", "未选择设备通道")
            return
            
        device_info = f"{channel_data['device_name']} - 通道{channel_data['channel_num']}"
        print(f"开始播放视频 - 窗口索引: {window_index}, 设备: {channel_data['device_name']}, 通道: {channel_data['channel_num']}")
        
        # 如果该窗口已有线程，先停止它
        if window_index in self.video_threads and self.video_threads[window_index].isRunning():
            print(f"停止窗口 {window_index} 的现有线程")
            self.video_threads[window_index].terminate()
            self.video_threads[window_index].wait()
            del self.video_threads[window_index]
        
        # 创建视频线程并开始播放
        try:
            # 检查是否已经有用户ID
            user_id = selected_window.property('user_id')
            
            # 如果没有用户ID，先登录设备
            if user_id is None or user_id == -1:
                user_id, _ = self.device_controller.login_device(
                    channel_data['ip'],
                    channel_data['port'],
                    channel_data['username'],
                    channel_data['password']
                )
                
                if user_id == -1:
                    print("设备登录失败")
                    self._log_event(False, "播放视频", device_info, "设备登录失败")
                    return
                    
                # 存储用户ID到窗口组件
                selected_window.setProperty('user_id', user_id)
                print(f"设备登录成功，用户ID: {user_id}")
            else:
                print(f"使用现有用户ID: {user_id}")
            
            # 创建视频线程
            t = VideoThread(self.device_controller, selected_window)
            # 保存线程到字典
            self.video_threads[window_index] = t
            
            print(f"视频线程创建成功，窗口索引: {window_index}")
            self._log_event(True, "播放视频", device_info, "无")
        except Exception as e:
            print(f"视频播放失败: {str(e)}")
            self._log_event(False, "播放视频", device_info, str(e))
            import traceback
            traceback.print_exc()

    def record(self):
        """处理录像按钮点击事件"""
        # 检查是否有选中的窗口
        if self.video_view.current_selected_index == -1:
            print("请先选择一个视频窗口")
            self._log_event(False, "录像", "无", "未选择视频窗口")
            return
            
        # 获取选中的窗口索引
        window_index = self.video_view.current_selected_index
        
        # 获取选中的窗口
        selected_window = self.video_view.video_widgets[window_index]
        
        # 检查窗口是否有关联的通道数据
        channel_data = selected_window.property('channel_data')
        if not channel_data:
            print("请先选择一个设备通道")
            self._log_event(False, "录像", "无", "未选择设备通道")
            return
            
        # 检查窗口是否正在播放视频
        preview_handle = selected_window.property('preview_handle')
        if preview_handle is None or preview_handle == -1:
            print("请先开始播放视频")
            self._log_event(False, "录像", "无", "未开始播放视频")
            return
            
        device_info = f"{channel_data['device_name']} - 通道{channel_data['channel_num']}"
            
        # 如果窗口已经在录像，则停止录像
        if window_index in self.recording_windows:
            try:
                # 停止录像
                recording_info = self.recording_windows[window_index]
                self.device_controller.stop_record(preview_handle)
                
                # 记录录像结束
                duration = time.time() - recording_info['start_time']
                file_path = recording_info['file_path']
                print(f"停止录像 - 窗口索引: {window_index}, 文件: {file_path}, 时长: {duration:.2f}秒")
                self._log_event(True, f"停止录像 (时长: {duration:.2f}秒)", device_info, f"文件: {file_path}")
                
                # 从录像窗口列表中移除
                del self.recording_windows[window_index]
            except Exception as e:
                print(f"停止录像失败: {str(e)}")
                self._log_event(False, "停止录像", device_info, str(e))
                import traceback
                traceback.print_exc()
        else:
            try:
                # 创建录像文件名
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                device_name = channel_data['device_name'].replace(" ", "_")
                channel_num = channel_data['channel_num']
                file_name = f"{device_name}_CH{channel_num}_{timestamp}.mp4"
                file_path = os.path.join(self.record_dir, file_name)
                
                # 开始录像
                result = self.device_controller.start_record(preview_handle, file_path)
                if not result:
                    self._log_event(False, "开始录像", device_info, "录像启动失败")
                    return
                    
                # 记录录像信息
                self.recording_windows[window_index] = {
                    'start_time': time.time(),
                    'file_path': file_path
                }
                
                print(f"开始录像 - 窗口索引: {window_index}, 文件: {file_path}")
                self._log_event(True, "开始录像", device_info, f"文件: {file_path}")
            except Exception as e:
                print(f"开始录像失败: {str(e)}")
                self._log_event(False, "开始录像", device_info, str(e))
                import traceback
                traceback.print_exc()

    def grabbing(self):
        """处理抓图按钮点击事件"""
        # 检查是否有选中的窗口
        if self.video_view.current_selected_index == -1:
            error_msg = "请先选择一个视频窗口"
            print(error_msg)
            self._log_event(False, "抓图", "无", "未选择视频窗口")
            return
            
        # 获取选中的窗口索引
        window_index = self.video_view.current_selected_index
        
        # 获取选中的窗口
        selected_window = self.video_view.video_widgets[window_index]
        
        # 检查窗口是否有关联的通道数据
        channel_data = selected_window.property('channel_data')
        if not channel_data:
            error_msg = "请先选择一个设备通道"
            print(error_msg)
            self._log_event(False, "抓图", "无", "未选择设备通道")
            return
            
        # 检查窗口是否正在播放视频
        preview_handle = selected_window.property('preview_handle')
        if preview_handle is None or preview_handle == -1:
            error_msg = "请先开始播放视频"
            print(error_msg)
            self._log_event(False, "抓图", "无", "未开始播放视频")
            return
            
        device_info = f"{channel_data['device_name']} - 通道{channel_data['channel_num']}"
            
        try:
            # 创建抓图文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            device_name = channel_data['device_name'].replace(" ", "_")
            channel_num = channel_data['channel_num']
            file_name = f"{device_name}_CH{channel_num}_{timestamp}.jpg"
            file_path = os.path.join(self.capture_dir, file_name)
            
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 获取对应的视频线程
            video_thread = self.video_threads.get(window_index)
            
            # 尝试多种抓图方法
            capture_success = False
            error_messages = []
            
            # 1. 首先尝试使用视频线程的抓图方法
            if video_thread and hasattr(video_thread, 'capture_picture'):
                print(f"方法1: 尝试使用视频线程抓图")
                try:
                    result = video_thread.capture_picture(file_path)
                    if result:
                        success_msg = HikErrorHandler.format_error_info(
                            0,
                            "视频线程抓图",
                            f"文件: {file_path}"
                        )
                        print(success_msg)
                        capture_success = True
                    else:
                        error_messages.append("视频线程抓图失败")
                except Exception as e:
                    error_msg = f"视频线程抓图异常: {str(e)}"
                    print(error_msg)
                    error_messages.append(error_msg)
            
            # 2. 如果视频线程抓图失败，尝试使用设备控制器抓图
            if not capture_success:
                print(f"方法2: 尝试使用设备控制器抓图")
                try:
                    # 确保设备已登录
                    user_id = selected_window.property('user_id')
                    if user_id is not None and user_id != -1:
                        # 尝试抓图
                        result = self.device_controller.capture_picture(preview_handle, file_path)
                        if result:
                            success_msg = HikErrorHandler.format_error_info(
                                0,
                                "设备控制器抓图",
                                f"文件: {file_path}"
                            )
                            print(success_msg)
                            capture_success = True
                        else:
                            error_messages.append("设备控制器抓图失败")
                    else:
                        error_msg = "无效的用户ID，无法进行设备抓图"
                        print(error_msg)
                        error_messages.append(error_msg)
                except Exception as e:
                    error_msg = f"设备控制器抓图异常: {str(e)}"
                    print(error_msg)
                    error_messages.append(error_msg)
            
            # 3. 如果以上方法都失败，尝试使用备用方法
            if not capture_success:
                print(f"方法3: 尝试使用BMP抓图备用方法")
                try:
                    # 创建BMP文件路径
                    bmp_path = file_path.replace(".jpg", ".bmp")
                    bmp_path_bytes = bytes(bmp_path, "gbk")
                    
                    # 尝试使用BMP抓图
                    bmp_result = self.device_controller.Objdll.NET_DVR_CapturePictureBlock(preview_handle, bmp_path_bytes, 0)
                    
                    if bmp_result:
                        success_msg = HikErrorHandler.format_error_info(
                            0,
                            "BMP抓图",
                            f"文件: {bmp_path}"
                        )
                        print(success_msg)
                        
                        # 转换BMP到JPG
                        try:
                            from PIL import Image
                            img = Image.open(bmp_path)
                            img.save(file_path)
                            os.remove(bmp_path)  # 删除BMP文件
                            print(f"BMP转换为JPG成功: {file_path}")
                            capture_success = True
                        except ImportError:
                            print("PIL库不可用，保留BMP格式")
                            file_path = bmp_path  # 使用BMP路径
                            capture_success = True
                        except Exception as e:
                            print(f"BMP转换为JPG失败: {str(e)}")
                            file_path = bmp_path  # 使用BMP路径
                            capture_success = True
                    else:
                        error_code = self.device_controller.Objdll.NET_DVR_GetLastError()
                        error_msg = HikErrorHandler.format_error_info(
                            error_code,
                            "BMP抓图",
                            f"预览句柄: {preview_handle}, 文件: {bmp_path}"
                        )
                        print(error_msg)
                        error_messages.append(f"BMP抓图失败: {HikErrorHandler.get_error_message(error_code)}")
                except Exception as e:
                    error_msg = f"BMP抓图异常: {str(e)}"
                    print(error_msg)
                    error_messages.append(error_msg)
            
            # 根据抓图结果记录日志并通知用户
            if capture_success:
                self._log_event(True, "抓图", device_info, f"文件: {file_path}")
                
                # 显示抓图成功消息
                QMessageBox.information(self, "抓图成功", f"抓图已保存到:\n{file_path}")
            else:
                error_summary = "; ".join(error_messages)
                self._log_event(False, "抓图", device_info, f"所有抓图方法均失败: {error_summary}")
                QMessageBox.warning(self, "抓图失败", f"尝试了多种抓图方法但均失败。\n\n详细错误信息:\n{error_summary}")
        except Exception as e:
            error_msg = f"抓图过程异常: {str(e)}"
            print(error_msg)
            self._log_event(False, "抓图", device_info, error_msg)
            import traceback
            traceback.print_exc()

    def inforce(self):
        pass

    def updateVideoLayout(self, index=0):
        """更新视频窗口布局"""
        try:
            num_windows = int(self.widNums[index])
            print(f"切换窗口布局: {num_windows}个窗口")
            
            # 保存当前的视频线程信息和窗口数据
            saved_data = []
            for i, widget in enumerate(self.video_view.video_widgets):
                if i < num_windows:  # 只保存不超过新窗口数量的数据
                    channel_data = widget.property('channel_data')
                    preview_handle = widget.property('preview_handle')
                    user_id = widget.property('user_id')
                    if channel_data:  # 只保存有通道数据的窗口
                        saved_data.append({
                            'index': i,
                            'channel_data': channel_data,
                            'preview_handle': preview_handle,
                            'user_id': user_id
                        })
            
            # 停止所有线程和录像
            self.stopAllThreads()
            
            # 调用视频视图的setup_windows方法重新设置窗口
            self.video_view.setup_windows(num_windows)
            
            # 重新加载保存的视频流
            for data in saved_data:
                window_index = data['index']
                channel_data = data['channel_data']
                
                if window_index < num_windows:
                    # 获取对应的窗口
                    widget = self.video_view.video_widgets[window_index]
                    
                    # 存储通道数据到窗口
                    widget.setProperty('channel_data', channel_data)
                    
                    # 创建视频线程并开始播放
                    try:
                        # 登录设备
                        user_id, _ = self.device_controller.login_device(
                            channel_data['ip'],
                            channel_data['port'],
                            channel_data['username'],
                            channel_data['password']
                        )
                        
                        if user_id == -1:
                            print(f"窗口 {window_index} 设备登录失败")
                            continue
                            
                        # 存储用户ID到窗口组件
                        widget.setProperty('user_id', user_id)
                        
                        # 创建视频线程
                        t = VideoThread(self.device_controller, widget)
                        # 保存线程到字典
                        self.video_threads[window_index] = t
                        
                        print(f"窗口 {window_index} 视频自动重新加载成功")
                    except Exception as e:
                        print(f"窗口 {window_index} 视频重新加载失败: {str(e)}")
            
            print("窗口布局更新成功，自动重新加载了视频内容")
            self._log_event(True, f"更新窗口布局 ({num_windows}个窗口)", "无", "自动重新加载了视频内容")
        except Exception as e:
            print(f"更新窗口布局失败: {str(e)}")
            self._log_event(False, f"更新窗口布局", "无", str(e))
            import traceback
            traceback.print_exc()
            
    def stopAllThreads(self):
        """停止所有视频线程"""
        try:
            # 停止所有录像
            for window_index in list(self.recording_windows.keys()):
                if window_index in self.video_threads:
                    selected_window = self.video_view.video_widgets[window_index]
                    preview_handle = selected_window.property('preview_handle')
                    if preview_handle is not None and preview_handle != -1:
                        self.device_controller.stop_record(preview_handle)
                        
            self.recording_windows.clear()
            
            # 停止所有线程
            for index, thread in list(self.video_threads.items()):
                if thread.isRunning():
                    print(f"停止窗口 {index} 的线程")
                    thread.terminate()
                    thread.wait()
            self.video_threads.clear()
            print("所有视频线程已停止")
        except Exception as e:
            print(f"停止线程异常: {str(e)}")
            self._log_event(False, "停止所有线程", "无", str(e))
            import traceback
            traceback.print_exc()
            
    def _log_event(self, success, operation, device_info, error_info):
        """记录事件到日志"""
        # 获取主窗口
        main_window = self.window()
        if hasattr(main_window, 'logger'):
            main_window.logger.add_log(success, operation, device_info, error_info)
import cv2
import numpy as np
from PyQt5.QtCore import QThread

from demo.HikSDK.HCNetSDK import *
from PyQt5.QtCore import pyqtSignal
from demo.HikSDK.PlayCtrl import *
from demo.VideoPreview.ErrorHandler import HikErrorHandler
from demo.ai.person_detector import PersonDetector
from demo.utils.ImgTool import yv12_to_bgr
import ctypes
import os
T_YV12 = 3
class VideoThread(QThread):
    play_started = pyqtSignal(object)
    play_ready = pyqtSignal(bool)  # 信号：视频流准备就绪

    def __init__(self, device_controller, video_widget):
        super().__init__(parent=None)
        self.device_controller = device_controller
        self.video_widget = video_widget
        self.channel_num = 1  # 默认通道号
        self.play_port = c_long(-1)  # 每个线程使用独立的播放端口
        self.preview_handle = -1  # 预览句柄
        self.stream_ready = False  # 流是否准备就绪
        self.detector = PersonDetector()
        self.funcRealDataCallBack_V30 = REALDATACALLBACK(self.RealDataCallBack_V30)
        self.funcDecCallBack = DECCALLBACK(self.DecCallBack)
        self.play_started.connect(self.handle_play)
        
        # 停止之前的预览
        self.stop_previous_preview()
        
        # 启动线程
        self.start()
        
    def stop_previous_preview(self):
        """停止之前的预览"""
        try:
            # 获取之前的预览句柄
            preview_handle = self.video_widget.property('preview_handle')
            if preview_handle is not None and preview_handle != -1:
                print(f"停止之前的预览，句柄: {preview_handle}")
                self.device_controller.stop_preview(preview_handle)
                self.video_widget.setProperty('preview_handle', None)
                
            # 如果窗口已有播放端口，释放它
            play_port = self.video_widget.property('play_port')
            if play_port is not None and play_port != -1:
                print(f"关闭之前的播放端口: {play_port}")
                self.device_controller.playctrldll.PlayM4_Stop(play_port)
                self.device_controller.playctrldll.PlayM4_CloseStream(play_port)
                self.device_controller.playctrldll.PlayM4_FreePort(play_port)
                self.video_widget.setProperty('play_port', None)
        except Exception as e:
            print(f"停止之前预览异常: {str(e)}")
            import traceback
            traceback.print_exc()

    def run(self):
        try:
            print(f"视频线程启动 - 通道号: {self.channel_num}")
            
            # 获取新的播放端口
            if not self.device_controller.playctrldll.PlayM4_GetPort(byref(self.play_port)):
                error_msg = "获取播放库端口失败"
                print(error_msg)
                return
                
            print(f"获取到播放端口: {self.play_port.value}")
            # 将播放端口保存到窗口属性
            self.video_widget.setProperty('play_port', self.play_port.value)
                    
            # 获取用户ID和通道数据
            user_id = self.video_widget.property('user_id')
            channel_data = self.video_widget.property('channel_data')
            
            if user_id is None or user_id == -1:
                error_msg = "无效的用户ID"
                print(error_msg)
                return
                
            # 从通道数据获取通道号
            if channel_data and 'channel_num' in channel_data:
                self.channel_num = channel_data['channel_num']
                
            print(f"开始预览 - 用户ID: {user_id}, 通道号: {self.channel_num}")
            
            # 打开预览
            self.preview_handle = self.device_controller.open_preview(user_id, self.funcRealDataCallBack_V30, self.channel_num)
            if self.preview_handle == -1:
                error_code = self.device_controller.Objdll.NET_DVR_GetLastError()
                error_msg = HikErrorHandler.format_error_info(
                    error_code,
                    "视频线程预览",
                    f"用户ID: {user_id}, 通道号: {self.channel_num}"
                )
                print(error_msg)
                return
                
            # 保存预览句柄到窗口属性
            self.video_widget.setProperty('preview_handle', self.preview_handle)
            print(f"预览句柄: {self.preview_handle}")
            # 等待线程结束
            self.exec_()
            
        except Exception as e:
            error_msg = f"视频线程异常: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()

    def handle_play(self, view):
        """处理播放开始事件"""
        try:
            hwnd = int(view.winId())
            print(f"绑定窗口句柄: {hwnd}, 播放端口: {self.play_port.value}")
            
            if self.device_controller.playctrldll.PlayM4_Play(
                self.play_port,
                hwnd
            ):
                success_msg = HikErrorHandler.format_error_info(
                    0,
                    "播放库播放",
                    f"端口: {self.play_port.value}, 窗口句柄: {hwnd}"
                )
                print(success_msg)
                # 设置流已准备就绪
                self.stream_ready = True
                # 发射信号通知流已准备就绪
                self.play_ready.emit(True)
            else:
                error_code = self.device_controller.playctrldll.PlayM4_GetLastError(self.play_port)
                error_msg = HikErrorHandler.format_error_info(
                    error_code,
                    "播放库播放",
                    f"端口: {self.play_port.value}, 窗口句柄: {hwnd}"
                )
                print(error_msg)
                self.stream_ready = False
                self.play_ready.emit(False)
        except Exception as e:
            error_msg = f"播放处理异常: {str(e)}"
            print(error_msg)
            self.stream_ready = False
            self.play_ready.emit(False)
            import traceback
            traceback.print_exc()

    def capture_picture(self, file_path):
        """抓图功能"""
        if not self.stream_ready:
            print("视频流未准备就绪，无法抓图")
            return False
            
        if self.play_port.value == -1:
            print("无效的播放端口，无法抓图")
            return False
            
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 创建足够大的缓冲区 (5MB)
            buffer_size = 5 * 1024 * 1024
            buffer = ctypes.create_string_buffer(buffer_size)
            actual_size = ctypes.c_ulong()
            
            # 使用播放库抓图
            result = self.device_controller.playctrldll.PlayM4_GetJPEG(
                self.play_port,
                buffer,
                buffer_size,
                ctypes.byref(actual_size)
            )
            
            if result:
                # 将缓冲区数据写入文件
                with open(file_path, 'wb') as f:
                    f.write(buffer.raw[:actual_size.value])
                
                success_msg = HikErrorHandler.format_error_info(
                    0,
                    "线程抓图",
                    f"文件: {file_path}, 大小: {actual_size.value} 字节"
                )
                print(success_msg)
                return True
            else:
                error_code = self.device_controller.playctrldll.PlayM4_GetLastError(self.play_port)
                error_msg = HikErrorHandler.format_error_info(
                    error_code,
                    "线程抓图",
                    f"播放端口: {self.play_port.value}, 文件: {file_path}"
                )
                print(error_msg)
                return False
                
        except Exception as e:
            error_msg = f"线程抓图异常: {str(e)}"
            print(error_msg)
            return False

    def DecCallBack(self, nPort, pBuf, nSize, pFrameInfo, nUser, nReserved):
        try:
            print("DecCallBack called")

            frame_info = pFrameInfo.contents
            print("frame type:", frame_info.nType)

            if frame_info.nType != T_YV12:
                return

            frame = yv12_to_bgr(pBuf, frame_info)
            print("frame shape:", frame.shape)

            boxes = self.detector.detect(frame)
            print("person count:", len(boxes))

            self.boxes_signal.emit(boxes)

        except Exception as e:
            # 先别吞，调试阶段一定要看
            print("DecCallBack error:", e)

    def RealDataCallBack_V30(self, lPlayHandle, dwDataType, pBuffer, dwBufSize, pUser):
        """实时数据回调函数"""
        if dwDataType == NET_DVR_SYSHEAD:
            print(f"收到系统头数据，播放端口: {self.play_port.value}")

            if not self.device_controller.playctrldll.PlayM4_OpenStream(
                    self.play_port,
                    pBuffer,
                    dwBufSize,
                    1024 * 1024
            ):
                error_code = self.device_controller.playctrldll.PlayM4_GetLastError(
                    self.play_port)
                print(f"PlayM4_OpenStream 失败，错误码: {error_code}")
                return

            self.device_controller.playctrldll.PlayM4_SetDecCallBackEx(
                self.play_port,
                self.funcDecCallBack,
                None
            )

            # 播放（内部会触发 PlayM4_Play）
            self.play_started.emit(self.video_widget)
            print(f"窗口绑定成功，播放端口: {self.play_port.value}")



        elif dwDataType == NET_DVR_STREAMDATA:
            self.device_controller.playctrldll.PlayM4_InputData(
                self.play_port,
                pBuffer,
                dwBufSize
            )


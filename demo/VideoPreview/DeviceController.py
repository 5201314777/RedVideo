from demo.HikSDK.HCNetSDK import *
from demo.HikSDK.PlayCtrl import *
from demo.VideoPreview.ErrorHandler import HikErrorHandler
import ctypes
import os
import time


class DeviceController:
    def __init__(self, Objdll, Playctrl):
        self.Objdll = Objdll
        self.playctrldll = Playctrl
        print("SDK库加载成功")
        self.Objdll.NET_DVR_Init()
        print("SDK初始化成功")
        self.PlayCtrl_Port = c_long(-1)

    def login_device(self, ip, port, username, password):
        """登录设备"""
        print(f"正在登录设备: {ip}:{port}, 用户名: {username}")
        
        struLoginInfo = NET_DVR_USER_LOGIN_INFO()
        struLoginInfo.bUseAsynLogin = 0
        struLoginInfo.sDeviceAddress = bytes(ip, "ascii")
        struLoginInfo.wPort = port
        struLoginInfo.sUserName = bytes(username, "ascii")
        struLoginInfo.sPassword = bytes(password, "ascii")
        struLoginInfo.byLoginMode = 0

        struDeviceInfoV40 = NET_DVR_DEVICEINFO_V40()
        UserID = self.Objdll.NET_DVR_Login_V40(byref(struLoginInfo), byref(struDeviceInfoV40))
        
        if UserID == -1:
            error_code = self.Objdll.NET_DVR_GetLastError()
            error_msg = HikErrorHandler.format_error_info(
                error_code, 
                "设备登录", 
                f"设备地址: {ip}:{port}, 用户名: {username}"
            )
            print(error_msg)
        else:
            success_msg = HikErrorHandler.format_error_info(0, "设备登录", f"用户ID: {UserID}")
            print(success_msg)

        return UserID, struDeviceInfoV40

    def open_preview(self, UserID, callbackFun, channel_num=1):
        """打开预览"""
        print(f"正在开启预览 - 用户ID: {UserID}, 通道号: {channel_num}")
        
        preview_info = NET_DVR_PREVIEWINFO()
        preview_info.hPlayWnd = 0  # 不直接使用窗口句柄，通过回调处理
        preview_info.lChannel = channel_num  # 使用传入的通道号
        preview_info.dwStreamType = 0  # 主码流
        preview_info.dwLinkMode = 0  # TCP方式
        preview_info.bBlocked = 1  # 阻塞取流
        preview_info.dwDisplayBufNum = 15  # 播放缓冲区最大帧数
        
        lRealPlayHandle = self.Objdll.NET_DVR_RealPlay_V40(UserID, byref(preview_info), callbackFun, None)
        
        if lRealPlayHandle == -1:
            error_code = self.Objdll.NET_DVR_GetLastError()
            error_msg = HikErrorHandler.format_error_info(
                error_code,
                "开启预览",
                f"用户ID: {UserID}, 通道号: {channel_num}"
            )
            print(error_msg)
        else:
            success_msg = HikErrorHandler.format_error_info(
                0,
                "开启预览",
                f"预览句柄: {lRealPlayHandle}"
            )
            print(success_msg)
            
        return lRealPlayHandle

    def start_record(self, preview_handle, file_path):
        """开始录像"""
        if preview_handle == -1:
            print("录像失败: 无效的预览句柄")
            return False
            
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # 转换为字节
        file_path_bytes = bytes(file_path, "gbk")
        
        # 调用SDK开始录像
        result = self.Objdll.NET_DVR_SaveRealData(preview_handle, file_path_bytes)
        
        if result:
            success_msg = HikErrorHandler.format_error_info(0, "开始录像", f"文件: {file_path}")
            print(success_msg)
        else:
            error_code = self.Objdll.NET_DVR_GetLastError()
            error_msg = HikErrorHandler.format_error_info(
                error_code,
                "开始录像",
                f"预览句柄: {preview_handle}, 文件: {file_path}"
            )
            print(error_msg)
            
        return result == 1
        
    def stop_record(self, preview_handle):
        """停止录像"""
        if preview_handle == -1:
            print("停止录像失败: 无效的预览句柄")
            return False
            
        # 调用SDK停止录像
        result = self.Objdll.NET_DVR_StopSaveRealData(preview_handle)
        
        if result:
            success_msg = HikErrorHandler.format_error_info(0, "停止录像")
            print(success_msg)
        else:
            error_code = self.Objdll.NET_DVR_GetLastError()
            error_msg = HikErrorHandler.format_error_info(
                error_code,
                "停止录像",
                f"预览句柄: {preview_handle}"
            )
            print(error_msg)
            
        return result == 1
        
    def capture_picture(self, preview_handle, file_path):
        """抓图 - 根据海康SDK手册使用预览抓图方式"""
        if preview_handle == -1:
            print("抓图失败: 无效的预览句柄")
            return False
            
        # 确保目录存在
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
        except Exception as e:
            print(f"创建目录失败: {str(e)}")
            return False
        
        # 转换为字节
        file_path_bytes = bytes(file_path, "gbk")
        
        # 先暂停预览
        print(f"暂停预览，预览句柄: {preview_handle}")
        pause_result = self.Objdll.NET_DVR_RealPlayPause(preview_handle)
        if not pause_result:
            error_code = self.Objdll.NET_DVR_GetLastError()
            error_msg = HikErrorHandler.format_error_info(
                error_code,
                "暂停预览",
                f"预览句柄: {preview_handle}"
            )
            print(f"{error_msg}，继续尝试抓图")
        else:
            success_msg = HikErrorHandler.format_error_info(0, "暂停预览")
            print(success_msg)
        
        # 方法1: 使用阻塞抓图方式 NET_DVR_CapturePictureBlock (推荐)
        print(f"方法1: 尝试阻塞抓图，预览句柄: {preview_handle}")
        try:
            result = self.Objdll.NET_DVR_CapturePictureBlock(preview_handle, file_path_bytes, 0)
            
            if result:
                success_msg = HikErrorHandler.format_error_info(
                    0,
                    "阻塞抓图",
                    f"文件: {file_path}"
                )
                print(success_msg)
                return True
            else:
                error_code = self.Objdll.NET_DVR_GetLastError()
                error_msg = HikErrorHandler.format_error_info(
                    error_code,
                    "阻塞抓图",
                    f"预览句柄: {preview_handle}, 文件: {file_path}"
                )
                print(error_msg)
        except Exception as e:
            print(f"方法1: 阻塞抓图异常: {str(e)}")
        
        # 方法2: 使用非阻塞抓图方式 NET_DVR_CapturePicture
        print(f"方法2: 尝试非阻塞抓图，预览句柄: {preview_handle}")
        try:
            result = self.Objdll.NET_DVR_CapturePicture(preview_handle, file_path_bytes)
            
            if result:
                success_msg = HikErrorHandler.format_error_info(
                    0,
                    "非阻塞抓图",
                    f"文件: {file_path}"
                )
                print(success_msg)
                # 非阻塞方式需要等待一段时间让抓图完成
                print("等待1秒让非阻塞抓图完成...")
                time.sleep(1)
                return True
            else:
                error_code = self.Objdll.NET_DVR_GetLastError()
                error_msg = HikErrorHandler.format_error_info(
                    error_code,
                    "非阻塞抓图",
                    f"预览句柄: {preview_handle}, 文件: {file_path}"
                )
                print(error_msg)
        except Exception as e:
            print(f"方法2: 非阻塞抓图异常: {str(e)}")
        
        # 方法3: 尝试BMP格式抓图
        print(f"方法3: 尝试BMP格式抓图")
        try:
            bmp_path = file_path.replace(".jpg", ".bmp")
            bmp_path_bytes = bytes(bmp_path, "gbk")
            
            result = self.Objdll.NET_DVR_CapturePictureBlock(preview_handle, bmp_path_bytes, 0)
            
            if result:
                success_msg = HikErrorHandler.format_error_info(
                    0,
                    "BMP抓图",
                    f"文件: {bmp_path}"
                )
                print(success_msg)
                # 尝试转换为JPG
                try:
                    from PIL import Image
                    img = Image.open(bmp_path)
                    img.save(file_path)
                    os.remove(bmp_path)
                    print(f"BMP转JPG成功，最终文件: {file_path}")
                    return True
                except ImportError:
                    print("PIL库不可用，保留BMP格式")
                    return True
                except Exception as e:
                    print(f"BMP转JPG失败: {str(e)}，保留BMP格式")
                    return True
            else:
                error_code = self.Objdll.NET_DVR_GetLastError()
                error_msg = HikErrorHandler.format_error_info(
                    error_code,
                    "BMP抓图",
                    f"预览句柄: {preview_handle}, 文件: {bmp_path}"
                )
                print(error_msg)
        except Exception as e:
            print(f"方法3: BMP抓图异常: {str(e)}")
        
        print("所有抓图方法都失败了")
        return False

    def stop_preview(self, preview_handle):
        """停止预览"""
        if preview_handle != -1:
            result = self.Objdll.NET_DVR_StopRealPlay(preview_handle)
            if result:
                success_msg = HikErrorHandler.format_error_info(
                    0,
                    "停止预览",
                    f"预览句柄: {preview_handle}"
                )
                print(success_msg)
            else:
                error_code = self.Objdll.NET_DVR_GetLastError()
                error_msg = HikErrorHandler.format_error_info(
                    error_code,
                    "停止预览",
                    f"预览句柄: {preview_handle}"
                )
                print(error_msg)
            return result
        return False
        
    def logout_device(self, user_id):
        """登出设备"""
        if user_id != -1:
            result = self.Objdll.NET_DVR_Logout(user_id)
            if result:
                success_msg = HikErrorHandler.format_error_info(
                    0,
                    "设备登出",
                    f"用户ID: {user_id}"
                )
                print(success_msg)
            else:
                error_code = self.Objdll.NET_DVR_GetLastError()
                error_msg = HikErrorHandler.format_error_info(
                    error_code,
                    "设备登出",
                    f"用户ID: {user_id}"
                )
                print(error_msg)
            return result
        return False

    def cleanup(self):
        """清理SDK资源"""
        self.Objdll.NET_DVR_Cleanup()
        print("SDK资源已清理")

    def ptz_control(self, user_id, channel, command, stop=0, speed=4):
        """
        云台控制
        :param user_id: 用户ID
        :param channel: 通道号
        :param command: 控制命令
        :param stop: 0-开始，1-停止
        :param speed: 速度(1-7)
        :return: 成功返回True，失败返回False
        """
        try:
            # 使用NET_DVR_PTZControl_Other，不需要预览句柄
            result = self.Objdll.NET_DVR_PTZControl_Other(user_id, channel, command, stop)
            
            if result:
                action = "停止" if stop else "开始"
                success_msg = HikErrorHandler.format_error_info(
                    0,
                    "云台控制",
                    f"通道{channel}, 命令{command}, {action}"
                )
                print(success_msg)
                return True
            else:
                error_code = self.Objdll.NET_DVR_GetLastError()
                action = "停止" if stop else "开始"
                error_msg = HikErrorHandler.format_error_info(
                    error_code,
                    "云台控制",
                    f"通道{channel}, 命令{command}, {action}"
                )
                print(error_msg)
                return False
        except Exception as e:
            print(f"云台控制异常: {str(e)}")
            return False
    
    def ptz_control_with_speed(self, user_id, channel, command, stop=0, speed=4):
        """
        带速度的云台控制
        :param user_id: 用户ID
        :param channel: 通道号
        :param command: 控制命令
        :param stop: 0-开始，1-停止
        :param speed: 速度(1-7)
        :return: 成功返回True，失败返回False
        """
        try:
            # 使用NET_DVR_PTZControlWithSpeed_Other
            result = self.Objdll.NET_DVR_PTZControlWithSpeed_Other(user_id, channel, command, stop, speed)
            
            if result:
                action = "停止" if stop else "开始"
                success_msg = HikErrorHandler.format_error_info(
                    0,
                    "云台控制(带速度)",
                    f"通道{channel}, 命令{command}, {action}, 速度{speed}"
                )
                print(success_msg)
                return True
            else:
                error_code = self.Objdll.NET_DVR_GetLastError()
                action = "停止" if stop else "开始"
                error_msg = HikErrorHandler.format_error_info(
                    error_code,
                    "云台控制(带速度)",
                    f"通道{channel}, 命令{command}, {action}, 速度{speed}"
                )
                print(error_msg)
                return False
        except Exception as e:
            print(f"云台控制(带速度)异常: {str(e)}")
            return False

    # 镜头调整功能
    def ptz_move_up(self, user_id, channel, speed=4):
        """向上移动镜头"""
        return self.ptz_control_with_speed(user_id, channel, 21, 0, speed)  # TILT_UP
    
    def ptz_move_down(self, user_id, channel, speed=4):
        """向下移动镜头"""
        return self.ptz_control_with_speed(user_id, channel, 22, 0, speed)  # TILT_DOWN
    
    def ptz_move_left(self, user_id, channel, speed=4):
        """向左移动镜头"""
        return self.ptz_control_with_speed(user_id, channel, 23, 0, speed)  # PAN_LEFT
    
    def ptz_move_right(self, user_id, channel, speed=4):
        """向右移动镜头"""
        return self.ptz_control_with_speed(user_id, channel, 24, 0, speed)  # PAN_RIGHT
    
    def ptz_zoom_in(self, user_id, channel, speed=4):
        """增加焦距（放大）"""
        return self.ptz_control_with_speed(user_id, channel, 11, 0, speed)  # ZOOM_IN
    
    def ptz_zoom_out(self, user_id, channel, speed=4):
        """缩小焦距（缩小）"""
        return self.ptz_control_with_speed(user_id, channel, 12, 0, speed)  # ZOOM_OUT
    
    def ptz_focus_near(self, user_id, channel, speed=4):
        """缩聚焦"""
        return self.ptz_control_with_speed(user_id, channel, 13, 0, speed)  # FOCUS_NEAR
    
    def ptz_focus_far(self, user_id, channel, speed=4):
        """伸聚焦"""
        return self.ptz_control_with_speed(user_id, channel, 14, 0, speed)  # FOCUS_FAR
    
    def ptz_iris_open(self, user_id, channel, speed=4):
        """增大光圈"""
        return self.ptz_control_with_speed(user_id, channel, 15, 0, speed)  # IRIS_OPEN
    
    def ptz_iris_close(self, user_id, channel, speed=4):
        """缩小光圈"""
        return self.ptz_control_with_speed(user_id, channel, 16, 0, speed)  # IRIS_CLOSE
    
    def ptz_stop_all(self, user_id, channel):
        """停止所有云台动作"""
        commands = [21, 22, 23, 24, 11, 12, 13, 14, 15, 16]  # 所有可能的控制命令
        success = True
        for cmd in commands:
            try:
                self.Objdll.NET_DVR_PTZControl_Other(user_id, channel, cmd, 1)  # 1表示停止
            except:
                success = False
        return success


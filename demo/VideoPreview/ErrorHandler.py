"""
海康威视SDK错误码处理工具类
提供错误码解析和友好的错误信息显示
"""

class HikErrorHandler:
    """海康威视SDK错误码处理器"""
    
    # 错误码映射表
    ERROR_CODES = {
        0: "操作成功",
        1: "用户名或密码错误，请检查登录凭据",
        2: "权限不足，请检查用户权限设置",
        3: "SDK未初始化，请先调用NET_DVR_Init",
        4: "通道号错误，请检查通道号是否有效",
        5: "设备连接数超过最大值，请释放其他连接",
        6: "SDK版本与设备版本不匹配",
        7: "连接设备失败，请检查设备IP地址和网络连接",
        8: "向设备发送数据失败，请检查网络连接",
        9: "从设备接收数据失败，请检查网络连接",
        10: "从设备接收数据超时，请检查网络状况",
        11: "传送的数据有误，请检查参数格式",
        12: "调用次序错误，请按正确顺序调用接口",
        13: "无此权限，请检查用户功能权限",
        14: "设备命令执行超时，请重试操作",
        15: "串口号错误，指定的串口不存在",
        16: "报警端口错误，指定的端口不存在",
        17: "参数错误，请检查输入参数的有效性",
        18: "设备通道处于错误状态",
        19: "设备无硬盘，无法进行录像相关操作",
        20: "硬盘号错误，指定的硬盘不存在",
        21: "设备硬盘已满，请清理存储空间",
        22: "设备硬盘出错，请检查硬盘状态",
        23: "设备不支持此功能",
        24: "设备忙，请稍后重试",
        25: "设备修改操作失败",
        26: "密码格式不正确，请检查密码格式",
        27: "硬盘正在格式化，无法执行操作",
        28: "设备资源不足，请释放其他资源",
        29: "设备操作失败，请重试",
        30: "音频设备操作失败，请检查音频设备",
        31: "设备语音对讲被占用",
        32: "时间输入不正确，请检查时间格式",
        33: "回放时找不到指定文件",
        34: "创建文件失败，请检查路径和权限",
        35: "打开文件失败，请检查文件是否存在",
        36: "上次操作尚未完成，请等待",
        37: "获取播放时间失败",
        38: "播放操作失败",
        39: "文件格式不正确",
        40: "路径错误，请检查文件路径",
        41: "SDK资源分配错误",
        42: "声卡模式错误",
        43: "缓冲区太小，请增加缓冲区大小",
        44: "创建网络连接失败",
        45: "设置网络连接失败",
        46: "连接数达到最大值",
        47: "用户不存在或已注销",
        48: "写入FLASH失败",
        49: "设备升级失败",
        50: "解码卡已初始化",
        51: "播放库函数调用失败",
        52: "登录用户数达到最大值",
        53: "获取本地网络信息失败",
        54: "设备通道未启动编码",
        55: "IP地址不匹配",
        56: "MAC地址不匹配",
        57: "升级文件语言不匹配",
        58: "播放器路数达到最大",
        59: "备份空间不足",
        60: "找不到备份设备",
    }
    
    # 错误类别分类
    ERROR_CATEGORIES = {
        "登录认证": [1, 2, 3, 47, 52, 55, 56],
        "网络连接": [7, 8, 9, 10, 44, 45],
        "参数错误": [4, 11, 17, 26, 32, 39, 40],
        "权限问题": [2, 13],
        "设备状态": [18, 23, 24, 28, 29, 54],
        "存储相关": [19, 20, 21, 22, 27, 59, 60],
        "文件操作": [33, 34, 35, 36, 38, 39, 40],
        "资源限制": [5, 41, 43, 46, 51, 58],
        "硬件相关": [15, 16, 30, 31, 42, 48, 49, 50],
    }
    
    @classmethod
    def get_error_message(cls, error_code):
        """
        获取错误码对应的友好错误信息
        
        Args:
            error_code (int): 错误码
            
        Returns:
            str: 友好的错误信息
        """
        if error_code in cls.ERROR_CODES:
            return cls.ERROR_CODES[error_code]
        else:
            return f"未知错误码: {error_code}，请查阅SDK文档"
    
    @classmethod
    def get_error_category(cls, error_code):
        """
        获取错误码所属的类别
        
        Args:
            error_code (int): 错误码
            
        Returns:
            str: 错误类别
        """
        for category, codes in cls.ERROR_CATEGORIES.items():
            if error_code in codes:
                return category
        return "其他错误"
    
    @classmethod
    def format_error_info(cls, error_code, operation="操作", context=""):
        """
        格式化错误信息，提供完整的错误描述
        
        Args:
            error_code (int): 错误码
            operation (str): 操作名称
            context (str): 上下文信息
            
        Returns:
            str: 格式化的错误信息
        """
        if error_code == 0:
            return f"{operation}成功"
        
        error_msg = cls.get_error_message(error_code)
        category = cls.get_error_category(error_code)
        
        result = f"【{operation}失败】错误码: {error_code}\n"
        result += f"错误类别: {category}\n"
        result += f"错误描述: {error_msg}"
        
        if context:
            result += f"\n上下文: {context}"
        
        # 添加解决建议
        suggestions = cls.get_error_suggestions(error_code)
        if suggestions:
            result += f"\n解决建议: {suggestions}"
        
        return result
    
    @classmethod
    def get_error_suggestions(cls, error_code):
        """
        根据错误码提供解决建议
        
        Args:
            error_code (int): 错误码
            
        Returns:
            str: 解决建议
        """
        suggestions = {
            1: "请检查用户名和密码是否正确",
            2: "请联系管理员检查用户权限设置",
            4: "请确认通道号在有效范围内",
            5: "请先断开其他连接或等待连接释放",
            7: "请检查设备IP地址、端口号和网络连接",
            13: "请联系管理员分配相应功能权限",
            17: "请检查传入参数的格式和取值范围",
            21: "请清理设备存储空间或更换大容量硬盘",
            23: "请确认设备型号是否支持此功能",
            24: "请稍后重试或检查设备当前状态",
            34: "请检查文件保存路径是否存在且有写入权限",
            43: "请增加缓冲区大小或优化内存使用",
            54: "请检查设备通道编码设置",
        }
        
        return suggestions.get(error_code, "请查阅SDK文档或联系技术支持")
    
    @classmethod
    def log_error(cls, error_code, operation="操作", context="", logger=None):
        """
        记录错误信息到日志
        
        Args:
            error_code (int): 错误码
            operation (str): 操作名称
            context (str): 上下文信息
            logger: 日志记录器
        """
        error_info = cls.format_error_info(error_code, operation, context)
        
        if logger:
            if error_code == 0:
                logger.info(error_info)
            else:
                logger.error(error_info)
        else:
            print(error_info)
    
    @classmethod
    def is_success(cls, error_code):
        """
        判断操作是否成功
        
        Args:
            error_code (int): 错误码
            
        Returns:
            bool: 是否成功
        """
        return error_code == 0
    
    @classmethod
    def is_network_error(cls, error_code):
        """
        判断是否为网络相关错误
        
        Args:
            error_code (int): 错误码
            
        Returns:
            bool: 是否为网络错误
        """
        network_errors = [7, 8, 9, 10, 44, 45]
        return error_code in network_errors
    
    @classmethod
    def is_permission_error(cls, error_code):
        """
        判断是否为权限相关错误
        
        Args:
            error_code (int): 错误码
            
        Returns:
            bool: 是否为权限错误
        """
        permission_errors = [1, 2, 13]
        return error_code in permission_errors
    
    @classmethod
    def is_resource_error(cls, error_code):
        """
        判断是否为资源相关错误
        
        Args:
            error_code (int): 错误码
            
        Returns:
            bool: 是否为资源错误
        """
        resource_errors = [5, 21, 28, 41, 43, 46, 52, 58, 59]
        return error_code in resource_errors 
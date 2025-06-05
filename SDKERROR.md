# 海康威视SDK错误码参考手册

## 网络通讯库错误码

| 错误类型 | 错误值 | 错误信息 |
|---------|--------|----------|
| NET_DVR_NOERROR | 0 | 没有错误 |
| NET_DVR_PASSWORD_ERROR | 1 | 用户名密码错误。注册时输入的用户名或者密码错误 |
| NET_DVR_NOENOUGHPRI | 2 | 权限不足。一般和通道相关，例如有预览通道1权限，无预览通道2权限 |
| NET_DVR_NOINIT | 3 | SDK未初始化。必须先调用NET_DVR_Init |
| NET_DVR_CHANNEL_ERROR | 4 | 通道号错误。设备通道分模拟通道和数字通道（IP通道） |
| NET_DVR_OVER_MAXLINK | 5 | 设备总的连接数超过最大。例如网络摄像机只支持6路预览，预览第7路即会返回失败 |
| NET_DVR_VERSIONNOMATCH | 6 | 版本不匹配。SDK和设备的版本不匹配 |
| NET_DVR_NETWORK_FAIL_CONNECT | 7 | 连接设备失败。设备不在线或网络原因引起的连接超时等 |
| NET_DVR_NETWORK_SEND_ERROR | 8 | 向设备发送失败 |
| NET_DVR_NETWORK_RECV_ERROR | 9 | 从设备接收数据失败 |
| NET_DVR_NETWORK_RECV_TIMEOUT | 10 | 从设备接收数据超时 |
| NET_DVR_NETWORK_ERRORDATA | 11 | 传送的数据有误。发送给设备或者从设备接收到的数据错误 |
| NET_DVR_ORDER_ERROR | 12 | 调用次序错误 |
| NET_DVR_OPERNOPERMIT | 13 | 无此权限。用户对某个功能模块的权限 |
| NET_DVR_COMMANDTIMEOUT | 14 | 设备命令执行超时 |
| NET_DVR_ERRORSERIALPORT | 15 | 串口号错误。指定的设备串口号不存在 |
| NET_DVR_ERRORALARMPORT | 16 | 报警端口错误。指定的设备报警输入或者输出端口不存在 |
| NET_DVR_PARAMETER_ERROR | 17 | 参数错误。SDK接口中给入的输入或输出参数为空，或者参数格式或值不符合要求 |
| NET_DVR_CHAN_EXCEPTION | 18 | 设备通道处于错误状态 |
| NET_DVR_NODISK | 19 | 设备无硬盘。当设备无硬盘时，对设备的录像文件、硬盘配置等操作失败 |
| NET_DVR_ERRORDISKNUM | 20 | 硬盘号错误。当对设备进行硬盘管理操作时，指定的硬盘号不存在时返回该错误 |
| NET_DVR_DISK_FULL | 21 | 设备硬盘满 |
| NET_DVR_DISK_ERROR | 22 | 设备硬盘出错 |
| NET_DVR_NOSUPPORT | 23 | 设备不支持 |
| NET_DVR_BUSY | 24 | 设备忙 |
| NET_DVR_MODIFY_FAIL | 25 | 设备修改不成功 |
| NET_DVR_PASSWORD_FORMAT_ERROR | 26 | 密码输入格式不正确 |
| NET_DVR_DISK_FORMATING | 27 | 硬盘正在格式化，不能启动操作 |
| NET_DVR_DVRNORESOURCE | 28 | 设备资源不足 |
| NET_DVR_DVROPRATEFAILED | 29 | 设备操作失败 |
| NET_DVR_OPENHOSTSOUND_FAIL | 30 | 语音对讲、语音广播操作中采集本地音频或打开音频输出失败 |
| NET_DVR_DVRVOICEOPENED | 31 | 设备语音对讲被占用 |
| NET_DVR_TIMEINPUTERROR | 32 | 时间输入不正确 |
| NET_DVR_NOSPECFILE | 33 | 回放时设备没有指定的文件 |
| NET_DVR_CREATEFILE_ERROR | 34 | 创建文件出错。本地录像、保存图片、获取配置文件和远程下载录像时创建文件失败 |
| NET_DVR_FILEOPENFAIL | 35 | 打开文件出错。可能因为文件不存在或者路径错误 |
| NET_DVR_OPERNOTFINISH | 36 | 上次的操作还没有完成 |
| NET_DVR_GETPLAYTIMEFAIL | 37 | 获取当前播放的时间出错 |
| NET_DVR_PLAYFAIL | 38 | 播放出错 |
| NET_DVR_FILEFORMAT_ERROR | 39 | 文件格式不正确 |
| NET_DVR_DIR_ERROR | 40 | 路径错误 |
| NET_DVR_ALLOC_RESOURCE_ERROR | 41 | SDK资源分配错误 |
| NET_DVR_AUDIO_MODE_ERROR | 42 | 声卡模式错误。当前打开声音播放模式与实际设置的模式不符出错 |
| NET_DVR_NOENOUGH_BUF | 43 | 缓冲区太小。接收设备数据的缓冲区或存放图片缓冲区不足 |
| NET_DVR_CREATESOCKET_ERROR | 44 | 创建SOCKET出错 |
| NET_DVR_SETSOCKET_ERROR | 45 | 设置SOCKET出错 |
| NET_DVR_MAX_NUM | 46 | 个数达到最大。分配的注册连接数、预览连接数超过SDK支持的最大数 |
| NET_DVR_USERNOTEXIST | 47 | 用户不存在。注册的用户ID已注销或不可用 |
| NET_DVR_WRITEFLASHERROR | 48 | 写FLASH出错。设备升级时写FLASH失败 |
| NET_DVR_UPGRADEFAIL | 49 | 设备升级失败。网络或升级文件语言不匹配等原因升级失败 |
| NET_DVR_CARDHAVEINIT | 50 | 解码卡已经初始化过 |
| NET_DVR_PLAYERFAILED | 51 | 调用播放库中某个函数失败 |
| NET_DVR_MAX_USERNUM | 52 | 登录设备的用户数达到最大 |
| NET_DVR_GETLOCALIPANDMACFAIL | 53 | 获得本地PC的IP地址或物理地址失败 |
| NET_DVR_NOENCODEING | 54 | 设备该通道没有启动编码 |
| NET_DVR_IPMISMATCH | 55 | IP地址不匹配 |
| NET_DVR_MACMISMATCH | 56 | MAC地址不匹配 |
| NET_DVR_UPGRADELANGMISMATCH | 57 | 升级文件语言不匹配 |
| NET_DVR_MAX_PLAYERPORT | 58 | 播放器路数达到最大 |
| NET_DVR_NOSPACEBACKUP | 59 | 备份设备中没有足够空间进行备份 |
| NET_DVR_NODEVICEBACKUP | 60 | 没有找到指定的备份设备 |

## 常见错误码快速查询

### 登录相关错误
- **错误码 1**: 用户名密码错误
- **错误码 7**: 连接设备失败，检查网络和设备状态
- **错误码 5**: 设备连接数超过最大值

### 预览相关错误
- **错误码 4**: 通道号错误
- **错误码 2**: 权限不足，检查用户权限
- **错误码 54**: 设备该通道没有启动编码

### 抓图录像相关错误
- **错误码 34**: 创建文件出错，检查路径和权限
- **错误码 43**: 缓冲区太小
- **错误码 40**: 路径错误

### 云台控制相关错误
- **错误码 23**: 设备不支持该功能
- **错误码 13**: 无此权限
- **错误码 17**: 参数错误

## 错误处理建议

1. **网络连接问题**: 检查设备IP、端口、网络连通性
2. **权限问题**: 确认用户账号权限设置
3. **参数问题**: 检查传入参数的有效性和格式
4. **资源问题**: 检查设备资源使用情况，适当释放连接
5. **设备状态**: 确认设备在线状态和功能支持情况 
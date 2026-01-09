import json
import os
from cryptography.fernet import Fernet


class ConfigManager:
    def __init__(self, config_file='devices.json', key_file='secret.key'):
        self.config_file = config_file
        self.key_file = key_file
        self.key = self._load_or_generate_key()
        self.cipher = Fernet(self.key)

    def _load_or_generate_key(self):
        """加载现有密钥或生成新密钥"""
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            return key

    def save_devices(self, devices_list):
        """
        保存设备列表到文件（加密密码）
        devices_list: List[dict], 每个dict包含 name, address, port, username, password
        """
        encrypted_list = []
        for device in devices_list:
            # 复制一份数据，避免修改原内存数据
            dev_copy = device.copy()

            # 加密密码
            if 'password' in dev_copy:
                pwd_bytes = dev_copy['password'].encode('utf-8')
                encrypted_pwd = self.cipher.encrypt(pwd_bytes)
                dev_copy['password'] = encrypted_pwd.decode('utf-8')  # 转回字符串以便存入JSON

            encrypted_list.append(dev_copy)

        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(encrypted_list, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False

    def load_devices(self):
        """
        从文件加载设备列表（解密密码）
        :return: List[dict]
        """
        if not os.path.exists(self.config_file):
            return []

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                encrypted_list = json.load(f)

            decrypted_list = []
            for device in encrypted_list:
                dev_copy = device.copy()

                # 解密密码
                if 'password' in dev_copy:
                    try:
                        encrypted_pwd = dev_copy['password'].encode('utf-8')
                        decrypted_pwd = self.cipher.decrypt(encrypted_pwd).decode('utf-8')
                        dev_copy['password'] = decrypted_pwd
                    except Exception:
                        # 如果解密失败（比如密钥文件丢了），密码置空或标记错误
                        dev_copy['password'] = ""

                decrypted_list.append(dev_copy)

            return decrypted_list
        except Exception as e:
            print(f"加载配置失败: {e}")
            return []
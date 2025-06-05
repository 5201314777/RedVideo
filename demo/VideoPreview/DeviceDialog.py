from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QPoint
from PyQt5 import QtWidgets
class DeviceDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('添加设备')

        # 创建布局和表单元素
        self.layout = QtWidgets.QVBoxLayout()

        self.form_layout = QtWidgets.QFormLayout()

        self.name_label = QtWidgets.QLabel('设备名称:')
        self.name_input = QtWidgets.QLineEdit()
        self.form_layout.addRow(self.name_label, self.name_input)

        self.address_label = QtWidgets.QLabel('设备地址:')
        self.address_input = QtWidgets.QLineEdit()
        self.form_layout.addRow(self.address_label, self.address_input)

        self.port_label = QtWidgets.QLabel('端口号:')
        self.port_input = QtWidgets.QSpinBox()
        self.port_input.setRange(1, 65535)  # 设置合理的端口号范围
        self.form_layout.addRow(self.port_label, self.port_input)

        self.username_label = QtWidgets.QLabel('用户名:')
        self.username_input = QtWidgets.QLineEdit()
        self.form_layout.addRow(self.username_label, self.username_input)

        self.password_label = QtWidgets.QLabel('密码:')
        self.password_input = QtWidgets.QLineEdit()
        self.password_input.setEchoMode(QtWidgets.QLineEdit.Password)  # 设置为密码输入模式
        self.form_layout.addRow(self.password_label, self.password_input)

        # 添加表单布局到主布局
        self.layout.addLayout(self.form_layout)

        # 创建按钮并添加到布局
        self.button_box = QtWidgets.QVBoxLayout()
        self.add_button = QtWidgets.QPushButton('添加')
        self.add_button.clicked.connect(self.accept)
        self.cancel_button = QtWidgets.QPushButton('取消')
        self.cancel_button.clicked.connect(self.reject)
        self.button_box.addWidget(self.add_button)
        self.button_box.addWidget(self.cancel_button)
        self.layout.addLayout(self.button_box)

        # 设置对话框的主布局
        self.setLayout(self.layout)

    def get_device_info(self):
        # 如果用户点击了“添加”按钮，则返回设备信息
        if self.result() == QtWidgets.QDialog.Accepted:
            return {
                'name': self.name_input.text(),
                'address': self.address_input.text(),
                'port': self.port_input.value(),
                'username': self.username_input.text(),
                'password': self.password_input.text()
            }
            # 如果用户点击了“取消”按钮或关闭了对话框，则返回None
        return None

    def show_device_info(self, info: dict):
        self.setWindowTitle("查看设备信息")

        self.name_input.setText(info.get('name', ''))
        self.address_input.setText(info.get('address', ''))
        self.port_input.setValue(info.get('port', 0))
        self.username_input.setText(info.get('username', ''))
        self.password_input.setText(info.get('password', ''))

        # 禁用输入控件，使其只读
        self.name_input.setReadOnly(True)
        self.address_input.setReadOnly(True)
        self.port_input.setReadOnly(True)
        self.username_input.setReadOnly(True)
        self.password_input.setReadOnly(True)

        self.add_button.hide()
        self.cancel_button.setText("关闭")



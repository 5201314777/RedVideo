from datetime import datetime
import os

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHeaderView, QPushButton, QHBoxLayout, QFileDialog, QMessageBox

#192.168.0.63       abcd1234

class Logger(QtWidgets.QWidget):
    """
    日志记录器类，用于显示日志信息。
    """

    def __init__(self, parent=None):
        super(Logger, self).__init__(parent)
        self.setMinimumHeight(150)
        
        # 创建主布局
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建标题和按钮栏
        title_bar = QtWidgets.QWidget()
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(5, 2, 5, 2)
        
        # 添加标题
        title_label = QtWidgets.QLabel("操作日志")
        title_label.setStyleSheet("font-weight: bold; color: #333;")
        title_layout.addWidget(title_label)
        
        # 添加空白占位符
        title_layout.addStretch()
        
        # 添加按钮
        self.clear_btn = QPushButton("清空日志")
        self.clear_btn.setMaximumWidth(80)
        self.clear_btn.clicked.connect(self.clear_logs)
        title_layout.addWidget(self.clear_btn)
        
        self.export_btn = QPushButton("导出日志")
        self.export_btn.setMaximumWidth(80)
        self.export_btn.clicked.connect(self.export_logs)
        title_layout.addWidget(self.export_btn)
        
        # 添加标题栏到主布局
        main_layout.addWidget(title_bar)
        
        # 创建表格
        self.table_widget = QtWidgets.QTableWidget(self)
        self.table_widget.setRowCount(0)  # 初始化行数为0
        self.table_widget.setColumnCount(5)  # 设置列数为5
        self.table_widget.setHorizontalHeaderLabels(["时间", "状态", "操作", "设备信息", "详细信息"])

        # 设置表格属性
        self.table_widget.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)  # 不可编辑
        self.table_widget.setAlternatingRowColors(True)  # 设置交替行颜色
        self.table_widget.setStyleSheet("""
            QTableWidget {
                gridline-color: #d0d0d0;
                background-color: #f8f8f8;
                border: 1px solid #d0d0d0;
            }
            QTableWidget::item:selected {
                background-color: #e0e0e0;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                border: 1px solid #d0d0d0;
                padding: 4px;
                font-weight: bold;
            }
        """)

        # 设置列宽
        self.table_widget.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)  # 时间列固定宽度
        self.table_widget.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)  # 状态列固定宽度
        self.table_widget.horizontalHeader().setSectionResizeMode(2, QHeaderView.Interactive)  # 操作列可调整
        self.table_widget.horizontalHeader().setSectionResizeMode(3, QHeaderView.Interactive)  # 设备信息列可调整
        self.table_widget.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)  # 详细信息列自动调整
        
        self.table_widget.setColumnWidth(0, 160)  # 时间列宽度
        self.table_widget.setColumnWidth(1, 50)   # 状态列宽度
        self.table_widget.setColumnWidth(2, 150)  # 操作列宽度
        self.table_widget.setColumnWidth(3, 200)  # 设备信息列宽度
        
        # 添加表格到主布局
        main_layout.addWidget(self.table_widget)
        
        # 设置布局
        self.setLayout(main_layout)
        
        # 创建日志存储目录
        self.log_dir = os.path.join(os.path.expanduser("~"), "RedInspect-vice", "logs")
        os.makedirs(self.log_dir, exist_ok=True)
        
        # 添加初始日志
        self.add_log(True, "系统启动", "RedInspect-vice", "应用程序已启动")

    def add_log(self, success, operation_type, deviceMes, errorMes):
        """添加日志条目"""
        row_position = self.table_widget.rowCount()
        self.table_widget.insertRow(row_position)  # 插入新行

        # 创建单元格并设置数据
        curTime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        time_item = QtWidgets.QTableWidgetItem(curTime)
        time_item.setTextAlignment(Qt.AlignCenter)

        # 状态单元格
        status_text = "成功" if success else "失败"
        status_item = QtWidgets.QTableWidgetItem(status_text)
        status_item.setTextAlignment(Qt.AlignCenter)
        
        # 设置状态单元格的颜色
        if success:
            status_item.setForeground(QtGui.QColor(0, 128, 0))  # 绿色
        else:
            status_item.setForeground(QtGui.QColor(255, 0, 0))  # 红色

        # 操作单元格
        operation_item = QtWidgets.QTableWidgetItem(operation_type)
        operation_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        # 设备信息单元格
        deviceMes_item = QtWidgets.QTableWidgetItem(deviceMes)
        deviceMes_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        # 错误信息单元格
        errorMes_item = QtWidgets.QTableWidgetItem(errorMes)
        errorMes_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        # 将单元格添加到表格中
        self.table_widget.setItem(row_position, 0, time_item)
        self.table_widget.setItem(row_position, 1, status_item)
        self.table_widget.setItem(row_position, 2, operation_item)
        self.table_widget.setItem(row_position, 3, deviceMes_item)
        self.table_widget.setItem(row_position, 4, errorMes_item)
        
        # 滚动到最新的日志
        self.table_widget.scrollToBottom()
        
        # 同时写入到日志文件
        self._write_log_to_file(curTime, status_text, operation_type, deviceMes, errorMes)

    def clear_logs(self):
        """清空日志表格"""
        reply = QMessageBox.question(self, '清空日志', 
                                     "确定要清空所有日志记录吗？\n(日志文件不会被删除)",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.table_widget.setRowCount(0)
            self.add_log(True, "清空日志", "系统", "日志记录已清空")

    def export_logs(self):
        """导出日志到文件"""
        try:
            # 获取当前日期时间作为文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"RedInspect_Log_{timestamp}.csv"
            default_path = os.path.join(self.log_dir, default_filename)
            
            # 打开文件对话框
            file_path, _ = QFileDialog.getSaveFileName(
                self, "导出日志", default_path, "CSV文件 (*.csv);;所有文件 (*.*)"
            )
            
            if not file_path:  # 用户取消
                return
                
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 写入CSV文件
            with open(file_path, 'w', encoding='utf-8') as f:
                # 写入表头
                f.write("时间,状态,操作,设备信息,详细信息\n")
                
                # 写入数据
                for row in range(self.table_widget.rowCount()):
                    time = self.table_widget.item(row, 0).text()
                    status = self.table_widget.item(row, 1).text()
                    operation = self.table_widget.item(row, 2).text()
                    device = self.table_widget.item(row, 3).text()
                    detail = self.table_widget.item(row, 4).text()
                    
                    # 处理CSV中的特殊字符
                    time = f'"{time}"'
                    status = f'"{status}"'
                    operation = f'"{operation}"'
                    device = f'"{device}"'
                    detail = f'"{detail}"'
                    
                    f.write(f"{time},{status},{operation},{device},{detail}\n")
                    
            self.add_log(True, "导出日志", "系统", f"日志已导出到: {file_path}")
            QMessageBox.information(self, "导出成功", f"日志已成功导出到:\n{file_path}")
            
        except Exception as e:
            self.add_log(False, "导出日志", "系统", f"导出失败: {str(e)}")
            QMessageBox.critical(self, "导出失败", f"导出日志时发生错误:\n{str(e)}")
            import traceback
            traceback.print_exc()
            
    def _write_log_to_file(self, time, status, operation, device, detail):
        """将日志写入到文件"""
        try:
            # 确保目录存在
            os.makedirs(self.log_dir, exist_ok=True)
            
            # 创建日志文件名（按日期）
            log_date = datetime.now().strftime("%Y%m%d")
            log_file = os.path.join(self.log_dir, f"RedInspect_Log_{log_date}.txt")
            
            # 写入日志
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"[{time}] [{status}] [{operation}] [{device}] {detail}\n")
                
        except Exception as e:
            print(f"写入日志文件失败: {str(e)}")
            import traceback
            traceback.print_exc()

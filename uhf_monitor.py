import sys
import time
import struct
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QPushButton, QComboBox, 
                            QGroupBox, QGridLayout, QTableWidget, QTableWidgetItem,
                            QHeaderView, QMessageBox, QSplitter)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
import serial.tools.list_ports
from pymodbus.client.serial import ModbusSerialClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder # 重新导入 BinaryPayloadDecoder

# 添加中文支持
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号


class UHFMonitorCanvas(FigureCanvas):
    """UHF图谱显示画布"""
    
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        """初始化画布"""
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super(UHFMonitorCanvas, self).__init__(self.fig)
        self.setParent(parent)
        
        # 初始化图表
        self.init_plot()
        
    def init_plot(self):
        """初始化图表"""
        self.axes.clear()
        self.axes.set_title('UHF图谱数据')
        self.axes.set_xlabel('采样点')
        self.axes.set_ylabel('幅值')
        self.axes.grid(True)
        self.fig.tight_layout()
        self.draw()
        
    def update_plot(self, data):
        """更新图表数据"""
        self.axes.clear()
        self.axes.plot(data, 'b-')
        self.axes.set_title('UHF图谱数据')
        self.axes.set_xlabel('采样点')
        self.axes.set_ylabel('幅值')
        self.axes.grid(True)
        self.fig.tight_layout()
        self.draw()


class UHFMonitor:
    """UHF局部放电监测装置数据读取类"""
    
    def __init__(self, port, slave_address=1):
        """
        初始化监测装置连接
        
        参数:
            port: 串口名称，如 'COM1'
            slave_address: 从站地址，默认为1
        """
        self.client = ModbusSerialClient(
            port=port,
            baudrate=9600,
            bytesize=8,
            parity='N',
            stopbits=1,
            timeout=1
        )
        self.slave_address = slave_address
        self.connected = False
    
    def connect(self):
        """建立与设备的连接"""
        try:
            self.connected = self.client.connect()
            return self.connected
        except Exception as e:
            print(f"连接错误: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """断开与设备的连接"""
        try:
            self.client.close()
            self.connected = False
        except Exception as e:
            print(f"断开连接错误: {e}")
    
    def read_float(self, address):
        """
        读取浮点型数据（占用两个连续寄存器）
        
        参数:
            address: 起始寄存器地址
        返回:
            浮点数值
        """
        if not self.connected:
            return None
        
        try:    
            # 读取两个连续寄存器（4字节）
            response = self.client.read_input_registers(address=address, count=2, slave=self.slave_address)
            if response.isError():
                print(f"读取寄存器 {address} 错误: {response}")
                return None
                
            # --- 使用 struct 模块 ---
            registers = response.registers
            # 假设设备使用小端序存储浮点数 (低位寄存器在前)
            # 如果是大端序 (高位寄存器在前)，使用: combined = (registers[0] << 16) | registers[1]
            combined = (registers[1] << 16) | registers[0] 
            # 使用 struct 将整数转换为浮点数 (注意字节序 '!' 表示网络字节序/大端)
            # 如果设备本身是小端浮点数，可能需要 '<f' 或 '>f' 取决于合并后的整数字节序
            # 通常 Modbus 传输是大端，但寄存器内的字序可能是小端，这里假设最终组合是符合大端浮点表示
            value = struct.unpack('!f', struct.pack('!I', combined))[0] 
            return value
            # --- struct 模块结束 ---

            # # --- BinaryPayloadDecoder (注释掉) ---
            # decoder = BinaryPayloadDecoder.fromRegisters(
            #     response.registers,
            #     byteorder=Endian.BIG,
            #     wordorder=Endian.LITTLE
            # )
            # return decoder.decode_32bit_float()
            # # --- BinaryPayloadDecoder 结束 ---

        except Exception as e:
            print(f"读取浮点数据错误 (地址 {address}): {e}")
            return None
    
    def read_short(self, address):
        """
        读取短整型数据（占用一个寄存器）
        
        参数:
            address: 寄存器地址
        返回:
            短整型数值
        """
        if not self.connected:
            return None
        
        try:    
            response = self.client.read_input_registers(address=address, count=1, slave=self.slave_address)
            if response.isError():
                print(f"读取寄存器 {address} 错误: {response}")
                return None
                
            return response.registers[0]
        except Exception as e:
            print(f"读取短整型数据错误 (地址 {address}): {e}")
            return None
    
    def read_uhf_telemetry(self):
        """
        读取UHF遥测数据
        
        返回:
            包含UHF遥测数据的字典
        """
        if not self.connected:
            return None
        
        try:    
            data = {}
            
            # 读取UHF放电次数
            data['UHF放电次数'] = self.read_short(101)
            
            # 读取UHF dB值
            data['UHF_dB值'] = self.read_float(106)
            
            # 读取UHF mV值
            data['UHF_mV值'] = self.read_short(111)
            
            return data
        except Exception as e:
            print(f"读取UHF遥测数据错误: {e}")
            return None
    
    def read_uhf_waveform(self):
        """
        读取UHF图谱数据 (分块读取)
        
        返回:
            UHF图谱数据列表
        """
        if not self.connected:
            return []
        
        waveform_data = []
        registers_to_read = 128
        start_address = 2256
        max_read_count = 125 # Modbus 协议或设备限制

        try:
            while registers_to_read > 0:
                count = min(registers_to_read, max_read_count)
                response = self.client.read_input_registers(address=start_address, count=count, slave=self.slave_address)
                
                if response.isError():
                    print(f"读取UHF图谱数据错误 (地址 {start_address}, 数量 {count}): {response}")
                    return [] # 如果任何一次读取失败，则返回空列表
                
                waveform_data.extend(response.registers)
                registers_to_read -= count
                start_address += count
                
                # 短暂延时，避免过于频繁地请求设备 (可选)
                time.sleep(0.1) 

            return waveform_data

        except Exception as e:
            print(f"读取UHF图谱数据异常: {e}")
            return []


class UHFMonitorApp(QMainWindow):
    """UHF局部放电监测应用程序"""
    
    def __init__(self):
        super().__init__()
        
        self.monitor = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)
        
        self.init_ui()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle('开关柜UHF局部放电监测')
        self.setGeometry(100, 100, 1000, 600)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 顶部控制区域
        control_group = QGroupBox('连接控制')
        control_layout = QHBoxLayout()
        
        # 串口选择
        self.port_label = QLabel('串口:')
        self.port_combo = QComboBox()
        self.refresh_ports()
        self.refresh_btn = QPushButton('刷新')
        self.refresh_btn.clicked.connect(self.refresh_ports)
        
        # 连接按钮
        self.connect_btn = QPushButton('连接')
        self.connect_btn.clicked.connect(self.toggle_connection)
        
        # 自动刷新控制
        self.auto_refresh_label = QLabel('自动刷新:')
        self.auto_refresh_combo = QComboBox()
        self.auto_refresh_combo.addItems(['关闭', '1秒', '2秒', '5秒', '10秒'])
        # 默认选择2秒自动刷新
        self.auto_refresh_combo.setCurrentIndex(2)
        self.auto_refresh_combo.currentIndexChanged.connect(self.set_refresh_rate)
        
        # 添加控件到控制布局
        control_layout.addWidget(self.port_label)
        control_layout.addWidget(self.port_combo)
        control_layout.addWidget(self.refresh_btn)
        control_layout.addWidget(self.connect_btn)
        control_layout.addStretch()
        control_layout.addWidget(self.auto_refresh_label)
        control_layout.addWidget(self.auto_refresh_combo)
        
        control_group.setLayout(control_layout)
        main_layout.addWidget(control_group)
        
        # 创建分割器
        splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(splitter)
        
        # 遥测数据区域
        telemetry_group = QGroupBox('UHF遥测数据')
        telemetry_layout = QGridLayout()
        
        # 创建遥测数据表格
        self.telemetry_table = QTableWidget(3, 2)
        self.telemetry_table.setHorizontalHeaderLabels(['参数', '数值'])
        self.telemetry_table.verticalHeader().setVisible(False)
        self.telemetry_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # 设置表格初始内容
        self.telemetry_table.setItem(0, 0, QTableWidgetItem('UHF放电次数'))
        self.telemetry_table.setItem(1, 0, QTableWidgetItem('UHF dB值'))
        self.telemetry_table.setItem(2, 0, QTableWidgetItem('UHF mV值'))
        
        self.telemetry_table.setItem(0, 1, QTableWidgetItem('--'))
        self.telemetry_table.setItem(1, 1, QTableWidgetItem('--'))
        self.telemetry_table.setItem(2, 1, QTableWidgetItem('--'))
        
        telemetry_layout.addWidget(self.telemetry_table)
        telemetry_group.setLayout(telemetry_layout)
        splitter.addWidget(telemetry_group)
        
        # 图谱数据区域
        waveform_group = QGroupBox('UHF图谱数据')
        waveform_layout = QVBoxLayout()
        
        # 创建图谱画布
        self.canvas = UHFMonitorCanvas(self, width=5, height=4)
        waveform_layout.addWidget(self.canvas)
        
        # 手动刷新按钮
        self.refresh_data_btn = QPushButton('刷新数据')
        self.refresh_data_btn.clicked.connect(self.update_data)
        waveform_layout.addWidget(self.refresh_data_btn)
        
        waveform_group.setLayout(waveform_layout)
        splitter.addWidget(waveform_group)
        
        # 设置分割器比例
        splitter.setSizes([200, 400])
        
        # 状态栏
        self.statusBar().showMessage('就绪')
        
        # 显示窗口
        self.show()
    
    def refresh_ports(self):
        """刷新可用串口列表"""
        self.port_combo.clear()
        ports = []
        for port in serial.tools.list_ports.comports():
            self.port_combo.addItem(f"{port.device} - {port.description}")
            ports.append(port.device)
        
        if not ports:
            self.statusBar().showMessage('未检测到可用串口')
        else:
            self.statusBar().showMessage(f'检测到 {len(ports)} 个可用串口')
    
    def toggle_connection(self):
        """切换连接状态"""
        if self.monitor is None or not self.monitor.connected:
            # 连接设备
            try:
                port_text = self.port_combo.currentText()
                if not port_text:
                    QMessageBox.warning(self, '警告', '请选择一个可用串口')
                    return
                
                # 提取串口名称
                port = port_text.split(' - ')[0]
                
                # 创建监测器并连接
                self.monitor = UHFMonitor(port)
                if self.monitor.connect():
                    self.connect_btn.setText('断开')
                    self.statusBar().showMessage(f'已连接到 {port}')
                    self.port_combo.setEnabled(False)
                    self.refresh_btn.setEnabled(False)
                    
                    # 立即更新一次数据
                    self.update_data()
                    
                    # 连接成功后自动启动定时器（如果选择了自动刷新）
                    self.set_refresh_rate(self.auto_refresh_combo.currentIndex())
                else:
                    QMessageBox.critical(self, '错误', f'无法连接到 {port}')
                    self.monitor = None
            except Exception as e:
                error_msg = f'连接时发生错误: {str(e)}'
                print(error_msg)  # 输出到控制台
                QMessageBox.critical(self, '错误', error_msg)
                self.monitor = None
        else:
            # 断开连接
            try:
                # 停止自动刷新
                self.timer.stop()
                self.auto_refresh_combo.setCurrentIndex(0)
                
                # 断开设备
                self.monitor.disconnect()
                self.monitor = None
                
                self.connect_btn.setText('连接')
                self.statusBar().showMessage('已断开连接')
                self.port_combo.setEnabled(True)
                self.refresh_btn.setEnabled(True)
                
                # 清空数据显示
                self.telemetry_table.setItem(0, 1, QTableWidgetItem('--'))
                self.telemetry_table.setItem(1, 1, QTableWidgetItem('--'))
                self.telemetry_table.setItem(2, 1, QTableWidgetItem('--'))
                self.canvas.init_plot()
            except Exception as e:
                error_msg = f'断开连接时发生错误: {str(e)}'
                print(error_msg)  # 输出到控制台
                QMessageBox.critical(self, '错误', error_msg)
    
    def set_refresh_rate(self, index):
        """设置自动刷新频率"""
        # 停止当前计时器
        self.timer.stop()
        
        # 根据选择设置新的刷新频率
        if index == 0:  # 关闭
            self.statusBar().showMessage('自动刷新已关闭')
            return
        
        # 获取刷新间隔（毫秒）
        intervals = [0, 1000, 2000, 5000, 10000]
        interval = intervals[index]
        
        # 如果已连接，则启动计时器
        if self.monitor and self.monitor.connected:
            self.timer.start(interval)
            self.statusBar().showMessage(f'自动刷新已设置为 {self.auto_refresh_combo.currentText()}')
        else:
            QMessageBox.warning(self, '警告', '请先连接设备')
            self.auto_refresh_combo.setCurrentIndex(0)
    
    def update_data(self):
        """更新数据显示"""
        if not self.monitor or not self.monitor.connected:
            return
        
        try:
            # 更新状态栏
            self.statusBar().showMessage('正在读取数据...')
            
            # 读取遥测数据
            telemetry_data = self.monitor.read_uhf_telemetry()
            if telemetry_data:
                # 处理 UHF放电次数
                uhf_count = telemetry_data.get('UHF放电次数', '--') # 使用 get 获取，提供默认值
                self.telemetry_table.setItem(0, 1, QTableWidgetItem(str(uhf_count)))
                
                # 处理 UHF dB值 (添加 None 值检查)
                uhf_db = telemetry_data.get('UHF_dB值') # 使用 get 获取
                if uhf_db is not None:
                    self.telemetry_table.setItem(1, 1, QTableWidgetItem(f"{uhf_db:.2f}"))
                else:
                    self.telemetry_table.setItem(1, 1, QTableWidgetItem("--")) # 如果是 None 或未获取到，显示 '--'
                    
                # 处理 UHF mV值
                uhf_mv = telemetry_data.get('UHF_mV值', '--') # 使用 get 获取，提供默认值
                self.telemetry_table.setItem(2, 1, QTableWidgetItem(str(uhf_mv)))
            else:
                 # 如果 telemetry_data 为 None，清空表格
                self.telemetry_table.setItem(0, 1, QTableWidgetItem('--'))
                self.telemetry_table.setItem(1, 1, QTableWidgetItem('--'))
                self.telemetry_table.setItem(2, 1, QTableWidgetItem('--'))

            # 读取图谱数据
            waveform_data = self.monitor.read_uhf_waveform()
            if waveform_data:
                self.canvas.update_plot(waveform_data)
            else:
                # 如果图谱数据为空，可以考虑清空或显示提示
                self.canvas.init_plot() # 例如，清空图表
            
            # 更新状态栏
            self.statusBar().showMessage('数据已更新 ' + time.strftime('%H:%M:%S'))
            
        except Exception as e:
            error_msg = f'读取或更新数据错误: {str(e)}' # 更明确的错误信息
            print(error_msg)  # 输出到控制台
            self.statusBar().showMessage(error_msg)
            # 如果发生错误，停止自动刷新
            self.timer.stop()
            self.auto_refresh_combo.setCurrentIndex(0)


def main():
    app = QApplication(sys.argv)
    window = UHFMonitorApp()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
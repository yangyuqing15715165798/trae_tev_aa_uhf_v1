import sys # 导入 sys
import time
import struct
import numpy as np # 导入 numpy
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QLabel, QPushButton, QComboBox,
                            QGroupBox, QGridLayout, QTableWidget, QTableWidgetItem,
                            QHeaderView, QMessageBox, QSplitter)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from pymodbus.client.serial import ModbusSerialClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
import serial.tools.list_ports  # 导入串口列表工具

# 添加中文支持 (如果需要绘图)
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

class AllSensorsReader:
    """读取 TEV, 超声波, UHF 传感器数据的类"""

    def __init__(self, port, slave_address=1):
        """
        初始化监测装置连接

        参数:
            port: 串口名称，如 'COM1'
            slave_address: 从站地址，默认为1
        """
        self.port = port # 保存传入的端口号
        self.client = ModbusSerialClient(
            port=port,
            baudrate=9600,
            bytesize=8,
            parity='N',
            stopbits=1,
            timeout=1  # 设置超时时间
        )
        self.slave_address = slave_address
        self.connected = False

    def connect(self):
        """建立与设备的连接"""
        try:
            self.connected = self.client.connect()
            # 不再在此处打印，由 GUI 处理状态显示
        except Exception as e:
            print(f"连接时发生错误: {e}") # 保留控制台错误输出
            self.connected = False
        return self.connected

    def disconnect(self):
        """断开与设备的连接"""
        if self.connected:
            try:
                self.client.close()
                self.connected = False
                # 不再在此处打印
            except Exception as e:
                print(f"断开连接时发生错误: {e}") # 保留控制台错误输出
        # else:
            # print("设备未连接，无需断开") # GUI 会处理状态，无需打印


    def read_float(self, address):
        """
        读取浮点型数据（占用两个连续寄存器）
        """
        if not self.connected:
            # print("错误：设备未连接") # 由GUI处理
            return None
        try:
            response = self.client.read_input_registers(address=address, count=2, slave=self.slave_address)
            if response.isError():
                print(f"读取寄存器 {address} (float) 错误: {response}") # 保留错误日志
                return None
            decoder = BinaryPayloadDecoder.fromRegisters(
                response.registers,
                byteorder=Endian.BIG,
                wordorder=Endian.LITTLE
            )
            return decoder.decode_32bit_float()
        except Exception as e:
            print(f"读取浮点数据时发生异常 (地址 {address}): {e}") # 保留错误日志
            return None

    def read_short(self, address):
        """
        读取短整型数据（占用一个寄存器）
        """
        if not self.connected:
            # print("错误：设备未连接") # 由GUI处理
            return None
        try:
            response = self.client.read_input_registers(address=address, count=1, slave=self.slave_address)
            if response.isError():
                print(f"读取寄存器 {address} (short) 错误: {response}") # 保留错误日志
                return None
            return response.registers[0]
        except Exception as e:
            print(f"读取短整型数据时发生异常 (地址 {address}): {e}") # 保留错误日志
            return None

    def read_telemetry_data(self):
        """
        读取所有遥测数据（TEV, 超声波, UHF）
        返回: 包含所有遥测数据的字典, 或 None
        """
        if not self.connected: return None
        # print("开始读取遥测数据...") # 由GUI处理状态
        data = {}
        read_success = True

        # 读取短整型数据
        tev_count = self.read_short(100); data['TEV放电次数'] = tev_count if tev_count is not None else None; read_success &= (tev_count is not None)
        uhf_count = self.read_short(101); data['UHF放电次数'] = uhf_count if uhf_count is not None else None; read_success &= (uhf_count is not None)
        tev_mv = self.read_short(109); data['TEV_mV值'] = tev_mv if tev_mv is not None else None; read_success &= (tev_mv is not None)
        ultrasonic_mv = self.read_short(110); data['超声波_mV值'] = ultrasonic_mv if ultrasonic_mv is not None else None; read_success &= (ultrasonic_mv is not None)
        uhf_mv = self.read_short(111); data['UHF_mV值'] = uhf_mv if uhf_mv is not None else None; read_success &= (uhf_mv is not None)
        tev_db = self.read_float(102); data['TEV_dB值'] = tev_db if tev_db is not None else None; read_success &= (tev_db is not None)
        ultrasonic_db = self.read_float(104); data['超声波_dB值'] = ultrasonic_db if ultrasonic_db is not None else None; read_success &= (ultrasonic_db is not None)
        uhf_db = self.read_float(106); data['UHF_dB值'] = uhf_db if uhf_db is not None else None; read_success &= (uhf_db is not None)

        if not read_success:
            print("警告：部分遥测数据读取失败") # 保留警告
            # 返回包含 None 值的数据字典，让 GUI 处理显示
        # print("遥测数据读取完成.") # 由GUI处理状态
        return data


    def read_waveform_data(self, max_read_count=125):
        """
        读取三种图谱数据 (TEV, 超声波, UHF)，支持分块读取
        返回: 包含三种图谱数据的字典, 或 None
        """
        if not self.connected: return None
        # print("开始读取图谱数据...") # 由GUI处理状态
        waveforms = {}
        read_success = True
        waveform_info = {
            'TEV图谱': {'start_address': 2000, 'registers_to_read': 128},
            '超声波图谱': {'start_address': 2128, 'registers_to_read': 128},
            'UHF图谱': {'start_address': 2256, 'registers_to_read': 128},
        }
        for name, info in waveform_info.items():
            # print(f"  正在读取 {name}...")
            waveform_data = []
            start_address = info['start_address']
            registers_to_read = info['registers_to_read']
            current_address = start_address
            error_occurred = False
            try:
                while registers_to_read > 0:
                    count = min(registers_to_read, max_read_count)
                    response = self.client.read_input_registers(address=current_address, count=count, slave=self.slave_address)
                    if response.isError():
                        print(f"    读取 {name} 数据错误 (地址 {current_address}, 数量 {count}): {response}")
                        error_occurred = True; break
                    waveform_data.extend(response.registers)
                    registers_to_read -= count
                    current_address += count
                    time.sleep(0.05)
                if not error_occurred:
                    waveforms[name] = waveform_data
                    # print(f"  {name} 读取成功 ({len(waveform_data)} 个点).")
                else:
                    waveforms[name] = []; read_success = False
            except Exception as e:
                print(f"  读取 {name} 时发生异常: {e}")
                waveforms[name] = []; read_success = False; break
        if not read_success:
            print("警告：部分图谱数据读取失败或发生异常") # 保留警告
        # print("图谱数据读取完成.") # 由GUI处理状态
        return waveforms

    # plot_waveforms 方法不再需要，绘图由 GUI 处理

# --- Matplotlib Canvas Class (通用化) ---
class MonitorCanvas(FigureCanvas):
    """通用数据显示画布"""
    def __init__(self, parent=None, width=5, height=2, dpi=100): # 调整默认高度
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super(MonitorCanvas, self).__init__(self.fig)
        self.setParent(parent)
        self.init_plot("图谱数据") # 默认标题

    def init_plot(self, title="图谱数据"):
        """初始化图表"""
        self.axes.clear()
        self.axes.set_title(title)
        self.axes.set_xlabel('采样点')
        self.axes.set_ylabel('幅值')
        self.axes.grid(True)
        self.fig.tight_layout() # 调整布局
        self.draw()

    def update_plot(self, data, title="图谱数据"):
        """更新图表数据"""
        self.axes.clear()
        if data: # 检查数据是否有效
             self.axes.plot(data, 'b-')
        self.axes.set_title(title)
        self.axes.set_xlabel('采样点')
        self.axes.set_ylabel('幅值')
        self.axes.grid(True)
        self.fig.tight_layout() # 调整布局
        self.draw()

# --- PyQt5 Application Class ---
class AllSensorsApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('多传感器监测软件')
        self.setGeometry(100, 100, 1000, 700) # 调整窗口大小

        self.reader = None # 初始化 reader 为 None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)

        self.initUI()
        self.refresh_ports() # 初始化时刷新串口列表

    def initUI(self):
        # --- 主控件 ---
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # --- 1. 连接控制区 ---
        connection_group = QGroupBox("连接设置")
        connection_layout = QHBoxLayout()
        connection_group.setLayout(connection_layout)

        self.port_combo = QComboBox()
        self.port_combo.setToolTip("选择设备连接的串口")
        self.refresh_button = QPushButton("刷新串口")
        self.refresh_button.clicked.connect(self.refresh_ports)
        self.connect_button = QPushButton("连接")
        self.connect_button.clicked.connect(self.connect_device)
        self.disconnect_button = QPushButton("断开")
        self.disconnect_button.clicked.connect(self.disconnect_device)
        self.disconnect_button.setEnabled(False) # 初始时断开按钮不可用

        connection_layout.addWidget(QLabel("串口:"))
        connection_layout.addWidget(self.port_combo, 1) # 占据更多空间
        connection_layout.addWidget(self.refresh_button)
        connection_layout.addWidget(self.connect_button)
        connection_layout.addWidget(self.disconnect_button)

        # --- 2. 数据显示区 (使用 QSplitter 分割) ---
        splitter = QSplitter(Qt.Horizontal)

        # --- 2.1 遥测数据显示区 ---
        telemetry_group = QGroupBox("遥测数据")
        telemetry_layout = QVBoxLayout()
        telemetry_group.setLayout(telemetry_layout)

        self.telemetry_table = QTableWidget()
        self.telemetry_table.setRowCount(8) # TEV(次数,dB,mV), 超声(dB,mV), UHF(次数,dB,mV)
        self.telemetry_table.setColumnCount(2)
        self.telemetry_table.setHorizontalHeaderLabels(['参数', '值'])
        self.telemetry_table.verticalHeader().setVisible(False) # 隐藏行号
        self.telemetry_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch) # 参数列自适应
        self.telemetry_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch) # 值列自适应
        self.telemetry_table.setEditTriggers(QTableWidget.NoEditTriggers) # 禁止编辑

        # 初始化表格内容
        param_names = ['TEV放电次数', 'TEV_dB值', 'TEV_mV值',
                       '超声波_dB值', '超声波_mV值',
                       'UHF放电次数', 'UHF_dB值', 'UHF_mV值']
        for i, name in enumerate(param_names):
            self.telemetry_table.setItem(i, 0, QTableWidgetItem(name))
            self.telemetry_table.setItem(i, 1, QTableWidgetItem('--')) # 初始值

        telemetry_layout.addWidget(self.telemetry_table)
        splitter.addWidget(telemetry_group)

        # --- 2.2 图谱显示区 ---
        waveform_group = QGroupBox("图谱数据")
        waveform_layout = QVBoxLayout() # 垂直排列三个图谱
        waveform_group.setLayout(waveform_layout)

        self.tev_canvas = MonitorCanvas(self)
        self.ultrasonic_canvas = MonitorCanvas(self)
        self.uhf_canvas = MonitorCanvas(self)

        self.tev_canvas.init_plot("TEV图谱")
        self.ultrasonic_canvas.init_plot("超声波图谱")
        self.uhf_canvas.init_plot("UHF图谱")

        waveform_layout.addWidget(self.tev_canvas)
        waveform_layout.addWidget(self.ultrasonic_canvas)
        waveform_layout.addWidget(self.uhf_canvas)
        splitter.addWidget(waveform_group)

        # 设置 Splitter 初始比例
        splitter.setSizes([300, 700]) # 左侧窄，右侧宽

        # --- 3. 自动刷新控制 ---
        refresh_control_layout = QHBoxLayout()
        self.auto_refresh_combo = QComboBox()
        self.auto_refresh_combo.addItems(['手动刷新', '1秒', '2秒', '5秒', '10秒'])
        self.auto_refresh_combo.currentIndexChanged.connect(self.set_auto_refresh)
        self.manual_refresh_button = QPushButton("手动刷新数据")
        self.manual_refresh_button.clicked.connect(self.update_data)
        self.manual_refresh_button.setEnabled(False) # 初始不可用

        refresh_control_layout.addWidget(QLabel("自动刷新:"))
        refresh_control_layout.addWidget(self.auto_refresh_combo)
        refresh_control_layout.addWidget(self.manual_refresh_button)
        refresh_control_layout.addStretch() # 将控件推到左侧

        # --- 布局整合 ---
        main_layout.addWidget(connection_group)
        main_layout.addWidget(splitter, 1) # 让 splitter 占据主要空间
        main_layout.addLayout(refresh_control_layout)

        # --- 状态栏 ---
        self.statusBar().showMessage('准备就绪')

    def refresh_ports(self):
        """刷新可用串口列表"""
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        if not ports:
            self.port_combo.addItem("未找到串口")
            self.port_combo.setEnabled(False)
            self.connect_button.setEnabled(False)
        else:
            for port, desc, hwid in sorted(ports):
                self.port_combo.addItem(f"{port} - {desc}", port) # 显示名称和描述，存储端口名
            self.port_combo.setEnabled(True)
            self.connect_button.setEnabled(True)
        self.statusBar().showMessage('串口列表已刷新')

    def connect_device(self):
        """连接到选定的设备"""
        selected_index = self.port_combo.currentIndex()
        if selected_index == -1 or not self.port_combo.itemData(selected_index):
             QMessageBox.warning(self, "连接错误", "请选择一个有效的串口")
             return

        port_name = self.port_combo.itemData(selected_index) # 获取存储的端口名
        self.statusBar().showMessage(f'正在连接 {port_name}...')
        QApplication.processEvents() # 处理界面事件，避免卡顿

        # 如果已有连接，先断开
        if self.reader and self.reader.connected:
            self.disconnect_device()

        self.reader = AllSensorsReader(port_name)
        if self.reader.connect():
            self.statusBar().showMessage(f'成功连接到 {port_name}')
            self.connect_button.setEnabled(False)
            self.disconnect_button.setEnabled(True)
            self.port_combo.setEnabled(False) # 连接后禁止切换串口
            self.refresh_button.setEnabled(False)
            self.manual_refresh_button.setEnabled(True)
            self.set_auto_refresh(self.auto_refresh_combo.currentIndex()) # 触发一次自动刷新设置
            self.update_data() # 连接成功后立即读取一次数据
        else:
            QMessageBox.critical(self, "连接失败", f"无法连接到 {port_name}。\n请检查设备是否连接或被占用。")
            self.statusBar().showMessage('连接失败')
            self.reader = None # 连接失败，重置 reader

    def disconnect_device(self):
        """断开设备连接"""
        if self.reader and self.reader.connected:
            self.timer.stop() # 停止自动刷新
            self.reader.disconnect()
            self.statusBar().showMessage('设备已断开')
            self.connect_button.setEnabled(True)
            self.disconnect_button.setEnabled(False)
            self.port_combo.setEnabled(True)
            self.refresh_button.setEnabled(True)
            self.manual_refresh_button.setEnabled(False)
            self.reader = None
            # 清空显示数据 (可选)
            self.clear_display()
        else:
            self.statusBar().showMessage('设备未连接')

    def set_auto_refresh(self, index):
        """设置自动刷新间隔"""
        self.timer.stop() # 先停止当前的定时器
        if index == 0: # 手动刷新
            self.statusBar().showMessage('自动刷新已关闭')
        else:
            intervals = [1000, 2000, 5000, 10000] # 毫秒
            interval = intervals[index - 1]
            if self.reader and self.reader.connected: # 只有连接状态下才启动定时器
                self.timer.start(interval)
                self.statusBar().showMessage(f'自动刷新间隔: {interval/1000} 秒')
            else:
                 self.statusBar().showMessage('请先连接设备以启动自动刷新')


    def update_data(self):
        """更新遥测和图谱数据"""
        if not self.reader or not self.reader.connected:
            # print("尝试更新数据，但设备未连接") # 调试信息
            # 可以选择停止定时器或显示提示
            if self.timer.isActive():
                self.timer.stop()
                self.auto_refresh_combo.setCurrentIndex(0) # 回到手动刷新
                QMessageBox.warning(self, "连接断开", "设备连接已断开，自动刷新已停止。")
            return

        self.statusBar().showMessage('正在读取数据...')
        QApplication.processEvents()

        # --- 读取遥测数据 ---
        telemetry_data = self.reader.read_telemetry_data()
        if telemetry_data:
            param_map = { # 表格行索引映射
                'TEV放电次数': 0, 'TEV_dB值': 1, 'TEV_mV值': 2,
                '超声波_dB值': 3, '超声波_mV值': 4,
                'UHF放电次数': 5, 'UHF_dB值': 6, 'UHF_mV值': 7
            }
            for key, value in telemetry_data.items():
                row = param_map.get(key)
                if row is not None:
                    display_value = '--' # 默认值
                    if value is not None:
                        # 特殊处理 UHF dB 值
                        if key == 'UHF_dB值' and abs(value - 54321.99) < 0.01:
                             display_value = "无信号(54321.99)" # 或仅显示 '--'
                        elif isinstance(value, float):
                            display_value = f"{value:.2f}"
                        else:
                            display_value = str(value)
                    self.telemetry_table.setItem(row, 1, QTableWidgetItem(display_value))
        else:
            print("读取遥测数据失败") # 控制台日志
            # 可以选择清空表格或显示错误
            for i in range(self.telemetry_table.rowCount()):
                 self.telemetry_table.setItem(i, 1, QTableWidgetItem('读取失败'))


        # --- 读取图谱数据 ---
        waveform_data = self.reader.read_waveform_data()
        if waveform_data:
            self.tev_canvas.update_plot(waveform_data.get('TEV图谱', []), "TEV图谱")
            self.ultrasonic_canvas.update_plot(waveform_data.get('超声波图谱', []), "超声波图谱")
            self.uhf_canvas.update_plot(waveform_data.get('UHF图谱', []), "UHF图谱")
        else:
            print("读取图谱数据失败") # 控制台日志
            # 清空图谱
            self.tev_canvas.init_plot("TEV图谱 (读取失败)")
            self.ultrasonic_canvas.init_plot("超声波图谱 (读取失败)")
            self.uhf_canvas.init_plot("UHF图谱 (读取失败)")

        self.statusBar().showMessage('数据已更新 ' + time.strftime('%H:%M:%S'))

    def clear_display(self):
         """清空数据显示区域"""
         # 清空遥测表格
         for i in range(self.telemetry_table.rowCount()):
             self.telemetry_table.setItem(i, 1, QTableWidgetItem('--'))
         # 清空图谱
         self.tev_canvas.init_plot("TEV图谱")
         self.ultrasonic_canvas.init_plot("超声波图谱")
         self.uhf_canvas.init_plot("UHF图谱")

    def closeEvent(self, event):
        """关闭窗口前确保断开连接"""
        self.disconnect_device()
        event.accept()

# --- Main Execution Block ---
def main_gui(): # 重命名 main 函数以避免冲突
    app = QApplication(sys.argv)
    mainWin = AllSensorsApp()
    mainWin.show()
    sys.exit(app.exec_())

# 移除旧的 list_available_ports 和 main 函数
# def list_available_ports(): ...
# def main(): ...

if __name__ == "__main__":
    main_gui() # 运行 GUI 版本
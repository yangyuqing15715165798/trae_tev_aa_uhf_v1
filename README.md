# 开关柜多传感器局部放电监测软件

本软件用于通过 Modbus RTU (Serial) 协议连接开关柜内的 TEV、超声波、UHF 局部放电监测装置，读取遥测数据和图谱数据，并在图形用户界面中显示。

项目包含两个主要脚本：
*   `all_sensors_reader.py`: 读取并显示 TEV、超声波、UHF 三种传感器的数据（推荐使用）。
*   `uhf_monitor.py`: 仅读取并显示 UHF 传感器的数据。

## 主要功能 (`all_sensors_reader.py`)

*   通过串口连接到监测装置。
*   实时显示 TEV、超声波、UHF 的遥测数据（放电次数、dB 值、mV 值）。
*   实时绘制 TEV、超声波、UHF 的图谱数据。
*   支持自动刷新数据（可选择刷新间隔）。
*   支持手动刷新串口列表和数据。
*   清晰的图形用户界面 (GUI)。

## 依赖

*   Python 3.x
*   PyQt5
*   matplotlib
*   pyserial
*   pymodbus==3.9.2
*   numpy

## 运行

推荐运行多传感器读取脚本：
```bash
python all_sensors_reader.py
```
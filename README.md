# 开关柜多传感器局部放电监测软件

本软件用于通过 Modbus RTU (Serial) 协议连接开关柜内的 TEV、超声波、UHF 局部放电监测装置，读取遥测数据和图谱数据，并在图形用户界面中显示。

项目包含两个主要脚本版本：
*   `all_sensors_reader.py`: 基于 **PyQt5**，读取并显示 TEV、超声波、UHF 三种传感器的数据。
*   `all_sensors_reader_pyside.py`: 基于 **PySide6**，功能与 PyQt5 版本相同，作为技术栈转换的示例。
*   `uhf_monitor.py`: (较旧版本) 仅读取并显示 UHF 传感器的数据。
*   `uhf_monitor_pyside.py`: (较新版本) 仅读取并显示 UHF 传感器的数据。
*   pyqt5版本代码界面与pyside6版本界面相同。

**推荐使用 `all_sensors_reader.py` 或 `all_sensors_reader_pyside.py`。**
### 下面是PyQt5版本代码界面：
![PyQt5 版本界面](https://github.com/user-attachments/assets/7090f3b4-c4a4-4268-acf8-1ab8d1d09a26)
![PyQt5 版本界面](https://github.com/user-attachments/assets/d0a539c1-3743-4240-b75a-77268d1cff96)

### 下面是pyside版本代码界面：
![image](https://github.com/user-attachments/assets/c584869f-4962-4021-a323-f1a8136cf46b)




## 主要功能 (`all_sensors_reader.py` / `all_sensors_reader_pyside.py`)

*   通过串口连接到监测装置。
*   实时显示 TEV、超声波、UHF 的遥测数据（放电次数、dB 值、mV 值）。
*   实时绘制 TEV、超声波、UHF 的图谱数据。
*   支持自动刷新数据（可选择刷新间隔）。
*   支持手动刷新串口列表和数据。
*   清晰的图形用户界面 (GUI)。
*   提供 PyQt5 和 PySide6 两个版本。

## 依赖

*   Python 3.x
*   **PyQt5** (用于 `all_sensors_reader.py`) **或 PySide6** (用于 `all_sensors_reader_pyside.py`)
*   matplotlib
*   pyserial
*   pymodbus==3.9.2
*   numpy

您可以使用 pip 安装依赖：
```bash
# 如果运行 PyQt5 版本
pip install PyQt5 matplotlib pyserial pymodbus numpy

# 如果运行 PySide6 版本
pip install PySide6 matplotlib pyserial pymodbus numpy
python all_sensors_reader.py
```

注意：PyQt5 和 PySide6 通常不建议在同一个 Python 环境中同时安装，请根据需要选择安装其中一个。




## 运行

选择您想运行的版本对应的命令：

**运行 PyQt5 版本:**
```bash
python all_sensors_reader.py
```

**运行 PySide6 版本:**
```bash
python all_sensors_reader_pyside.py
```

## PyQt5 到 PySide6 技术栈转换详解

本项目最初使用 PyQt5 构建图形用户界面。为了探索不同的 Qt for Python 绑定库并利用 PySide6 可能带来的一些优势（例如更宽松的 LGPL 许可证），我们创建了一个基于 PySide6 的版本 (`all_sensors_reader_pyside.py`)。

以下是本次转换过程中涉及的主要差异和修改点：

1.  **包导入**:
    *   PyQt5: `from PyQt5.QtWidgets import ...`, `from PyQt5.QtCore import ...`, `from PyQt5.QtGui import ...`
    *   PySide6: `from PySide6.QtWidgets import ...`, `from PySide6.QtCore import ...`, `from PySide6.QtGui import ...`
    *   主要修改是将所有 `PyQt5` 替换为 `PySide6`。

2.  **信号和槽 (Signals and Slots)**:
    *   PyQt5: 信号连接通常直接使用 `.connect()`。槽函数可以用 `@pyqtSlot()` 装饰，但这通常不是必需的。
    *   PySide6: 信号连接方式相同 (`.connect()`)。推荐使用 `@Slot()` 装饰器明确标记槽函数，尤其是在需要指定参数类型时（例如 `@Slot(int)`)。虽然不强制，但这有助于提高代码清晰度和类型检查。我们在 PySide6 版本中添加了 `@Slot()` 装饰器。

3.  **枚举 (Enums)**:
    *   PyQt5: 枚举值通常直接通过类访问，例如 `Qt.Horizontal`, `QHeaderView.Stretch`, `QTableWidget.NoEditTriggers`。
    *   PySide6: 枚举值需要通过更明确的路径访问，通常是 `Qt.Orientation.Horizontal`, `QHeaderView.ResizeMode.Stretch`, `QTableWidget.EditTrigger.NoEditTriggers`。需要注意枚举成员名称和所属类的变化。

4.  **Matplotlib 后端**:
    *   PyQt5: 使用 `matplotlib.backends.backend_qt5agg`。
    *   PySide6: 可以使用通用的 `matplotlib.backends.backend_qtagg`，它能同时兼容 PyQt5, PyQt6, PySide2, 和 PySide6。本次转换采用了 `backend_qtagg` 以获得更好的兼容性。

5.  **`exec_()` vs `exec()`**:
    *   PyQt5: 应用程序主循环启动使用 `app.exec_()` (带下划线)。
    *   PySide6: 应用程序主循环启动使用 `app.exec()` (不带下划线)。这是 Python 3 语法更新后，`exec` 不再是关键字，因此 PySide6 使用了更标准的名称。

6.  **代码结构**:
    *   为了便于维护和演示，我们将 PySide6 版本的代码放在了一个单独的文件 `all_sensors_reader_pyside.py` 中。核心的数据读取逻辑 (`AllSensorsReader` 类) 在两个文件中基本保持一致，主要的改动集中在 GUI 部分 (`AllSensorsApp` 类) 和导入语句。

通过这次转换，我们验证了在 PyQt5 和 PySide6 之间迁移的可行性。对于此类应用，两者在功能和性能上差异不大，主要区别在于 API 的细微之处和许可证。
```

        

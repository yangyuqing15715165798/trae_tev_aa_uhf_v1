# PyQt5 到 PySide6 技术栈转换详解

本项目最初使用 PyQt5 构建图形用户界面 (`all_sensors_reader.py`)。为了探索不同的 Qt for Python 绑定库，并利用 PySide6 可能带来的一些优势（例如更宽松的 LGPL 许可证），我们创建了一个功能相同但基于 PySide6 的版本 (`all_sensors_reader_pyside.py`)。
![在这里插入图片描述](https://i-blog.csdnimg.cn/direct/59fdfc8e963a43fd8eee256f4d867dec.png)

本文档详细介绍了从 PyQt5 迁移到 PySide6 的主要差异和修改点，并以本项目中的代码为例进行说明。

## 1. 包导入 (Package Imports)

最明显的变化是包名需从 `PyQt5` 替换为 `PySide6`。

**PyQt5 (`all_sensors_reader.py`)**:
```python
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QLabel, QPushButton, QComboBox,
                            QGroupBox, QGridLayout, QTableWidget, QTableWidgetItem,
                            QHeaderView, QMessageBox, QSplitter)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
```

**PySide6 (`all_sensors_reader_pyside.py`)**:
```python
import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QPushButton, QComboBox,
                             QGroupBox, QGridLayout, QTableWidget, QTableWidgetItem,
                             QHeaderView, QMessageBox, QSplitter)
from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtGui import QFont
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
```

**主要修改**: 将所有 `PyQt5` 替换为 `PySide6`，并根据需要导入 `Slot`。

## 2. 信号和槽 (Signals and Slots)

信号连接方式在两者中一致，但 PySide6 推荐使用 `@Slot()` 装饰器标记槽函数，以提高可读性和类型安全性。

**PyQt5 (`all_sensors_reader.py`)**:
```python
class AllSensorsApp(QMainWindow):
    def __init__(self):
        self.refresh_button.clicked.connect(self.refresh_ports)
        self.connect_button.clicked.connect(self.connect_device)
        self.disconnect_button.clicked.connect(self.disconnect_device)
        self.auto_refresh_combo.currentIndexChanged.connect(self.set_auto_refresh)
        self.manual_refresh_button.clicked.connect(self.update_data)

    def refresh_ports(self):
        pass

    def connect_device(self):
        pass

    def set_auto_refresh(self, index):
        pass

    def update_data(self):
        pass
```

**PySide6 (`all_sensors_reader_pyside.py`)**:
```python
from PySide6.QtCore import Slot

class AllSensorsApp(QMainWindow):
    def __init__(self):
        self.refresh_button.clicked.connect(self.refresh_ports)
        self.connect_button.clicked.connect(self.connect_device)
        self.disconnect_button.clicked.connect(self.disconnect_device)
        self.auto_refresh_combo.currentIndexChanged.connect(self.set_auto_refresh)
        self.manual_refresh_button.clicked.connect(self.update_data)

    @Slot()
    def refresh_ports(self):
        pass

    @Slot()
    def connect_device(self):
        pass

    @Slot(int)
    def set_auto_refresh(self, index):
        pass

    @Slot()
    def update_data(self):
        pass
```

**主要修改**: 添加 `@Slot()` 装饰器，并为需要参数的槽函数指定类型（如 `@Slot(int)`）。

## 3. 枚举 (Enums)

PySide6 对枚举访问路径要求更明确。

**PyQt5 (`all_sensors_reader.py`)**:
```python
splitter = QSplitter(Qt.Horizontal)
self.telemetry_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
self.telemetry_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
self.telemetry_table.setEditTriggers(QTableWidget.NoEditTriggers)
```

**PySide6 (`all_sensors_reader_pyside.py`)**:
```python
splitter = QSplitter(Qt.Orientation.Horizontal)
self.telemetry_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
self.telemetry_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
self.telemetry_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
```

**主要修改**:
- `Qt.Horizontal` -> `Qt.Orientation.Horizontal`
- `QHeaderView.Stretch` -> `QHeaderView.ResizeMode.Stretch`
- `QTableWidget.NoEditTriggers` -> `QTableWidget.EditTrigger.NoEditTriggers`

## 4. Matplotlib 后端 (Matplotlib Backend)

Matplotlib 后端需调整以兼容 PySide6。

**PyQt5 (`all_sensors_reader.py`)**:
```python
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
```

**PySide6 (`all_sensors_reader_pyside.py`)**:
```python
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
```

**主要修改**: 使用通用后端 `backend_qtagg`，兼容多种 Qt 绑定。

## 5. 应用程序执行 (exec_() vs exec())

主事件循环方法名有所不同。

**PyQt5 (`all_sensors_reader.py`)**:
```python
if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWin = AllSensorsApp()
    mainWin.show()
    sys.exit(app.exec_())
```

**PySide6 (`all_sensors_reader_pyside.py`)**:
```python
def main_gui():
    app = QApplication(sys.argv)
    mainWin = AllSensorsApp()
    mainWin.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main_gui()
```

**主要修改**: `app.exec_()` 改为 `app.exec()`，符合 Python 3 的命名规范。

## 总结

从 PyQt5 到 PySide6 的迁移主要涉及包名替换、信号槽装饰器调整、枚举路径更新、Matplotlib 后端更换及 `exec()` 方法修改。两者的功能和性能差异不大，PySide6 的 LGPL 许可证为其在商业场景中提供了优势。
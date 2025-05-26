import os
import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QLineEdit, QPushButton, QFileDialog, QMessageBox)
from PySide6.QtCore import Qt, QSettings, QProcess
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QPixmap


# 自定义支持拖放的文件输入框
class DragDropLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)  # 允许拖放

    # 重写拖放事件以支持文件拖放，当拖拽进入控件时触发
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    # 当释放拖拽内容时触发
    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()  # 获取第一个文件的本地路径
            self.setText(file_path)  # 设置文本为文件路径


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RePKG-GUI")
        self.setGeometry(100, 100, 720, 490)

        # 配置文件
        self.settings = QSettings("config.ini", QSettings.Format.IniFormat)

        # 初始化UI
        self.init_ui()

        # 加载保存的路径
        self.load_settings()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # RePKG路径部分
        self.repkg_layout = QHBoxLayout()
        self.lbl_repkg = QLabel("RePKG程序位置:")
        self.txt_repkg = DragDropLineEdit()
        self.btn_repkg = QPushButton("选择文件")
        self.btn_repkg.clicked.connect(lambda: self.select_file(self.txt_repkg, "选择RePKG程序", "*.exe"))
        self.repkg_layout.addWidget(self.lbl_repkg)
        self.repkg_layout.addWidget(self.txt_repkg)
        self.repkg_layout.addWidget(self.btn_repkg)

        # 保存路径部分
        self.save_layout = QHBoxLayout()
        self.lbl_save = QLabel("保存位置:")
        self.txt_save = DragDropLineEdit()
        self.btn_save = QPushButton("选择文件夹")
        self.btn_save.clicked.connect(lambda: self.select_directory(self.txt_save))
        self.save_layout.addWidget(self.lbl_save)
        self.save_layout.addWidget(self.txt_save)
        self.save_layout.addWidget(self.btn_save)

        # 壁纸文件部分
        self.wallpaper_layout = QHBoxLayout()
        self.lbl_wallpaper = QLabel("壁纸文件:")
        self.txt_wallpaper = DragDropLineEdit()
        self.txt_wallpaper.setAcceptDrops(True)
        self.btn_wallpaper = QPushButton("选择文件")
        self.btn_wallpaper.clicked.connect(lambda: self.select_file(self.txt_wallpaper, "选择壁纸文件", "*.pkg"))
        self.wallpaper_layout.addWidget(self.lbl_wallpaper)
        self.wallpaper_layout.addWidget(self.txt_wallpaper)
        self.wallpaper_layout.addWidget(self.btn_wallpaper)

        # 提取按钮
        self.btn_extract = QPushButton("提取")
        self.btn_extract.clicked.connect(self.extract_files)

        # 状态提示
        self.lbl_status = QLabel()

        # 添加所有部件到主布局
        main_layout.addLayout(self.repkg_layout)
        main_layout.addLayout(self.save_layout)
        main_layout.addLayout(self.wallpaper_layout)
        main_layout.addWidget(self.btn_extract)
        main_layout.addWidget(self.lbl_status)

    #     # 允许拖放
    #     self.setAcceptDrops(True)
    #
    # def dragEnterEvent(self, event: QDragEnterEvent):
    #     if event.mimeData().hasUrls():
    #         event.acceptProposedAction()
    #
    # def dropEvent(self, event: QDropEvent):
    #     urls = event.mimeData().urls()
    #     if urls:
    #         # 自动检测拖放目标
    #         target_widget = self.childAt(event.position().toPoint())
    #         if isinstance(target_widget, QLineEdit):
    #             target_widget.setText(urls[0].toLocalFile())
    #         else:
    #             # 根据文件类型自动分配
    #             for url in urls:
    #                 path = url.toLocalFile()
    #                 if path.lower().endswith(".exe"):
    #                     self.txt_repkg.setText(path)
    #                 elif path.lower().endswith(".pkg"):
    #                     self.txt_wallpaper.setText(path)
    #                 elif os.path.isdir(path):
    #                     self.txt_save.setText(path)

    def select_file(self, target, title, file_type):
        path, _ = QFileDialog.getOpenFileName(self, title, "", f"{file_type} Files (*{file_type})")
        if path:
            target.setText(path)

    def select_directory(self, target):
        path = QFileDialog.getExistingDirectory(self, "选择保存目录")
        if path:
            target.setText(path)

    #
    def load_settings(self):
        self.txt_repkg.setText(self.settings.value("repkg_path"))
        self.txt_save.setText(self.settings.value("save_path"))

    def save_settings(self):
        self.settings.setValue("repkg_path", self.txt_repkg.text())
        self.settings.setValue("save_path", self.txt_save.text())

    def extract_files(self):
        repkg = self.txt_repkg.text()
        pkg_file = self.txt_wallpaper.text()
        save_path = self.txt_save.text()

        if not all([repkg, pkg_file, save_path]):
            QMessageBox.warning(self, "错误", "请填写所有必要路径")
            return

        if not os.path.exists(repkg):
            QMessageBox.warning(self, "错误", "RePKG程序路径不存在")
            return

        cmd = f'"{repkg}" extract "{pkg_file}" -o "{save_path}"'
        self.process = QProcess()
        self.process.finished.connect(self.on_extract_finished)
        self.process.startCommand(cmd)
        self.lbl_status.setText("正在提取...")
        self.btn_extract.setEnabled(False)

    def on_extract_finished(self, exit_code, exit_status):
        self.btn_extract.setEnabled(True)
        if exit_code == 0:
            self.lbl_status.setText("提取成功！保存路径：%s" % self.txt_save.text())
            QMessageBox.information(self, "完成", "文件提取成功！")
        else:
            self.lbl_status.setText("提取失败")
            error = self.process.readAllStandardError().data().decode()
            QMessageBox.critical(self, "错误", f"提取失败：\n{error}")

    def closeEvent(self, event):
        self.save_settings()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

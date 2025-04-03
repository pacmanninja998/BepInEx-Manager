import os
import platform
import sys
import subprocess
import shutil
from PluginManager import PluginManager
from Config import ConfigEditor
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
                             QLabel, QPushButton, QListWidget, QListWidgetItem,
                             QCheckBox, QComboBox, QMessageBox, QFileDialog)
from PyQt5.QtCore import Qt, QThread, QObject, pyqtSignal
from PyQt5.QtGui import QPixmap, QIcon

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class GameManagementWindow(QMainWindow):
    def __init__(self, game_name, game_path):
        super().__init__()
        self.game_name = game_name
        self.game_path = game_path
        self.setWindowTitle(f"BepInEx - {game_name}")
        self.setMinimumSize(800, 600)

        self.tabs = QTabWidget()

        self.plugin_tab = PluginManager(game_path)
        self.config_tab = ConfigEditor(game_path)

        self.tabs.addTab(self.plugin_tab, QIcon(resource_path("icons/plugin.png")), "Plugins")
        self.tabs.addTab(self.config_tab, QIcon(resource_path("icons/config.png")), "Configuration")

        open_folder_btn = QPushButton()
        open_folder_btn.setIcon(QIcon(resource_path("icons/folder.png")))
        open_folder_btn.setToolTip("Open Game Directory")
        open_folder_btn.clicked.connect(self.open_game_directory)

        self.tabs.setCornerWidget(open_folder_btn, Qt.TopRightCorner)

        launch_btn = QPushButton("Launch Game")
        launch_btn.clicked.connect(self.launch_game)

        uninstall_btn = QPushButton("Uninstall BepInEx")
        uninstall_btn.clicked.connect(self.uninstall_bepinex)

        button_layout = QHBoxLayout()
        button_layout.addWidget(launch_btn)
        button_layout.addWidget(uninstall_btn)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tabs)
        main_layout.addLayout(button_layout)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def launch_game(self):
        for file in os.listdir(self.game_path):
            if file.endswith(".exe") and not file.endswith("UnityCrashHandler.exe"):
                try:
                    subprocess.Popen([os.path.join(self.game_path, file)])
                    return
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to launch game: {str(e)}")
                    return
        QMessageBox.warning(self, "Error", "Could not find game executable")

    def uninstall_bepinex(self):
        reply = QMessageBox.question(self, "Uninstall BepInEx",
                                     "Are you sure you want to uninstall BepInEx from this game?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.No:
            return

        try:
            bepinex_path = os.path.join(self.game_path, "BepInEx")
            if os.path.exists(bepinex_path):
                shutil.rmtree(bepinex_path)

            for file in [".doorstop_version", "doorstop_config.ini", "winhttp.dll"]:
                file_path = os.path.join(self.game_path, file)
                if os.path.exists(file_path):
                    os.remove(file_path)

            QMessageBox.information(self, "Success", "BepInEx has been uninstalled successfully")
            self.close()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to uninstall BepInEx: {str(e)}")

    def open_game_directory(self):
        try:
            if platform.system() == "Windows":
                os.startfile(self.game_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.Popen(["open", self.game_path])
            else:  # Linux
                subprocess.Popen(["xdg-open", self.game_path])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to open game directory: {str(e)}")

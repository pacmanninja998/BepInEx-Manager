import os
import sys
from PyQt5.QtWidgets import QApplication
from MainWindow import MainWindow
from GameManager import GameManagementWindow
from PluginManager import PluginManager
from Config import ConfigEditor
from Installer import Installer
from InstallHelper import InstallHelper

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

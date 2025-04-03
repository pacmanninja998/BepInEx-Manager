import os
import sys
import platform
import requests
import zipfile
import shutil
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QLabel, QPushButton, QListWidget, QListWidgetItem,
                            QCheckBox, QComboBox, QMessageBox, QFileDialog,
                            QProgressDialog, QPlainTextEdit)
from PyQt5.QtCore import Qt, QThread, QObject, pyqtSignal
from PyQt5.QtGui import QPixmap, QIcon
from download import BepInExDownloader

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class Installer(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.progress_dialog = None
        
    def get_system_info(self):
        system = platform.system().lower()
        if system == "windows":
            os_name = "win"
        elif system == "linux":
            os_name = "linux"
        elif system == "darwin":
            os_name = "macos"
        else:
            os_name = system
            
        arch = platform.machine().lower()
        if arch in ["x86_64", "amd64"]:
            arch = "x64"
        elif arch in ["i386", "i686", "x86"]:
            arch = "x86"
            
        return os_name, arch
        
    def install_bepinex(self, game_path, game_architecture):
        """Install BepInEx to the selected game"""
        # Get OS info
        os_name, arch = self.get_system_info()
        
        # Override arch with the game's architecture if needed
        if game_architecture == "x86":
            arch = "x86"
        
        # Show confirmation dialog
        reply = QMessageBox.question(self.parent(), "Install BepInEx", 
                                    f"Install BepInEx for {os_name}_{arch} to the selected game?",
                                    QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.No:
            return
        
        # Show progress dialog
        self.progress_dialog = QProgressDialog("Downloading BepInEx...", "Cancel", 0, 100, self.parent())
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.show()
        
        # Download BepInEx
        downloader = BepInExDownloader()
        downloader.progress_signal.connect(self.update_progress)
        downloader.download_latest(lambda success, path: self.on_download_complete(success, path, game_path))
    
    def update_progress(self, value):
        """Update progress dialog"""
        if self.progress_dialog:
            self.progress_dialog.setValue(value)
    
    def on_download_complete(self, success, zip_path, game_path):
        """Handle download completion"""
        if not success or not zip_path:
            QMessageBox.warning(self.parent(), "Error", "Failed to download BepInEx")
            if self.progress_dialog:
                self.progress_dialog.close()
            return
        
        self.progress_dialog.setLabelText("Extracting BepInEx...")
        
        # Extract BepInEx to game directory
        try:
            # Create game folder if it doesn't exist
            os.makedirs(game_path, exist_ok=True)
            
            # Extract the zip file to a temporary folder
            temp_dir = "temp_extract"
            os.makedirs(temp_dir, exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Copy required files to game folder
            required_files = [
                '.doorstop_version',
                'doorstop_config.ini',
                'winhttp.dll'
            ]
            
            for file in required_files:
                src_path = os.path.join(temp_dir, file)
                if os.path.exists(src_path):
                    shutil.copy2(src_path, os.path.join(game_path, file))
            
            # Copy BepInEx folder
            src_bepinex = os.path.join(temp_dir, 'BepInEx')
            if os.path.exists(src_bepinex):
                dest_bepinex = os.path.join(game_path, 'BepInEx')
                if os.path.exists(dest_bepinex):
                    shutil.rmtree(dest_bepinex)
                shutil.copytree(src_bepinex, dest_bepinex)
            
            # Clean up
            shutil.rmtree(temp_dir)
            os.remove(zip_path)
            
            QMessageBox.information(self.parent(), "Success", "BepInEx has been installed successfully")
            
        except Exception as e:
            QMessageBox.warning(self.parent(), "Error", f"Failed to extract BepInEx: {str(e)}")
        
        if self.progress_dialog:
            self.progress_dialog.close()

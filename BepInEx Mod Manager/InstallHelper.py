import os
import sys
import time
import subprocess
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import Qt, QThread, QObject, pyqtSignal

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class InstallHelper(QObject):
    installation_complete = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.monitor_thread = None
        self.monitor_worker = None
    
    def launch_game(self, game_path):
        """Launch the game executable"""
        for file in os.listdir(game_path):
            if file.endswith(".exe") and not file.endswith("UnityCrashHandler.exe"):
                try:
                    subprocess.Popen([os.path.join(game_path, file)])
                    return True
                except Exception as e:
                    QMessageBox.warning(self.parent(), "Error", f"Failed to launch game: {str(e)}")
                    return False
        
        QMessageBox.warning(self.parent(), "Error", "Could not find game executable")
        return False
    
    def monitor_installation(self, game_path):
        """Monitor the game to ensure BepInEx is properly installed"""
        # Launch the game
        if not self.launch_game(game_path):
            return
        
        # Create a monitoring thread
        self.monitor_thread = QThread()
        self.monitor_worker = MonitorWorker(game_path)
        self.monitor_worker.moveToThread(self.monitor_thread)
        
        self.monitor_thread.started.connect(self.monitor_worker.run)
        self.monitor_worker.finished.connect(self.monitor_thread.quit)
        self.monitor_worker.finished.connect(self.on_monitoring_complete)
        
        self.monitor_thread.start()
    
    def on_monitoring_complete(self, success):
        """Handle monitoring completion"""
        if success:
            QMessageBox.information(self.parent(), "Success", "BepInEx has been successfully installed and initialized")
        else:
            QMessageBox.warning(self.parent(), "Warning", "BepInEx installation may not have completed successfully")
        
        self.installation_complete.emit(success)

class MonitorWorker(QObject):
    finished = pyqtSignal(bool)
    
    def __init__(self, game_path):
        super().__init__()
        self.game_path = game_path
        
    def run(self):
        """Monitor the BepInEx installation"""
        folders_to_check = [
            os.path.join(self.game_path, "BepInEx", "cache"),
            os.path.join(self.game_path, "BepInEx", "config"),
            os.path.join(self.game_path, "BepInEx", "patchers"),
            os.path.join(self.game_path, "BepInEx", "plugins")
        ]
        
        # Check every second for up to 2 minutes
        for _ in range(120):
            if all(os.path.exists(folder) for folder in folders_to_check):
                self.finished.emit(True)
                return
            time.sleep(1)
        
        # If we get here, installation might have failed
        self.finished.emit(False)

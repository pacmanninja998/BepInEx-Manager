import os
import sys
import requests
import zipfile
import shutil
from PyQt5.QtCore import QThread, pyqtSignal, QObject

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class DownloadThread(QThread):
    progress_updated = pyqtSignal(int)

    def __init__(self, url, save_path):
        super().__init__()
        self.url = url
        self.save_path = save_path
        self.success = False

    def run(self):
        try:
            response = requests.get(self.url, stream=True)
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            with open(self.save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = int((downloaded / total_size) * 100)
                            self.progress_updated.emit(progress)
            self.success = True
        except Exception as e:
            print(f"Download error: {str(e)}")
            self.success = False

class ExtractThread(QThread):
    def __init__(self, zip_path, target_dir):
        super().__init__()
        self.zip_path = zip_path
        self.target_dir = target_dir
        self.success = False

    def run(self):
        try:
            os.makedirs(self.target_dir, exist_ok=True)
            temp_dir = "temp_extract"
            os.makedirs(temp_dir, exist_ok=True)
            
            with zipfile.ZipFile(self.zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            required_files = [
                '.doorstop_version',
                'doorstop_config.ini',
                'winhttp.dll'
            ]
            
            for file in required_files:
                src_path = os.path.join(temp_dir, file)
                if os.path.exists(src_path):
                    shutil.copy2(src_path, os.path.join(self.target_dir, file))
            
            src_bepinex = os.path.join(temp_dir, 'BepInEx')
            if os.path.exists(src_bepinex):
                dest_bepinex = os.path.join(self.target_dir, 'BepInEx')
                if os.path.exists(dest_bepinex):
                    shutil.rmtree(dest_bepinex)
                shutil.copytree(src_bepinex, dest_bepinex)
            
            shutil.rmtree(temp_dir)
            self.success = True
        except Exception as e:
            print(f"Extraction error: {str(e)}")
            self.success = False

class BepInExDownloader(QObject):
    progress_signal = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.api_url = "https://api.github.com/repos/BepInEx/BepInEx/releases/latest"

    def download_latest(self, callback):
        try:
            response = requests.get(self.api_url)
            response.raise_for_status()
            release_data = response.json()
            
            version = release_data["tag_name"].replace("v", "")
            os_name, arch = self.get_system_info()
            
            asset_name_pattern = f"BepInEx_{os_name}_{arch}_{version}.zip"
            
            asset_url = None
            for asset in release_data["assets"]:
                if asset["name"] == asset_name_pattern:
                    asset_url = asset["browser_download_url"]
                    break
            
            if not asset_url:
                for asset in release_data["assets"]:
                    if f"{os_name}_{arch}" in asset["name"] and asset["name"].endswith(".zip"):
                        asset_url = asset["browser_download_url"]
                        asset_name_pattern = asset["name"]
                        break
            
            if not asset_url:
                print(f"Could not find appropriate asset for {os_name}_{arch}")
                callback(False, None)
                return
            
            save_path = asset_name_pattern
            download_thread = DownloadThread(asset_url, save_path)
            download_thread.progress_updated.connect(self.progress_signal)
            download_thread.finished.connect(lambda: callback(download_thread.success, save_path))
            download_thread.start()
        
        except Exception as e:
            print(f"Error getting latest release: {str(e)}")
            callback(False, None)

    def get_system_info(self):
        import platform
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

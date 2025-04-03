import os
import sys
import platform
import winreg
import json
from PyQt5.QtCore import QObject

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class GameFinder(QObject):
    def __init__(self):
        super().__init__()

    def find_unity_games(self):
        games = {}
        
        steam_games = self.find_steam_games()
        for game_name, game_path in steam_games.items():
            if self.is_unity_game(game_path):
                games[game_name] = {
                    'path': game_path,
                    'platform': self.get_unity_platform(game_path),
                    'source': 'Steam'
                }
        
        epic_games = self.find_epic_games()
        for game_name, game_path in epic_games.items():
            if self.is_unity_game(game_path):
                games[game_name] = {
                    'path': game_path,
                    'platform': self.get_unity_platform(game_path),
                    'source': 'Epic Games'
                }
        
        ms_store_games = self.find_ms_store_games()
        for game_name, game_path in ms_store_games.items():
            if self.is_unity_game(game_path):
                games[game_name] = {
                    'path': game_path,
                    'platform': self.get_unity_platform(game_path),
                    'source': 'Microsoft Store'
                }
        
        return games

    def is_unity_game(self, game_path):
        for root, dirs, files in os.walk(game_path):
            if 'UnityEngine.dll' in files:
                return True
        return False

    def get_unity_platform(self, game_path):
        for root, dirs, files in os.walk(game_path):
            if 'UnityPlayer.dll' in files:
                dll_path = os.path.join(root, 'UnityPlayer.dll')
                return 'x64' if self.is_64bit_dll(dll_path) else 'x86'
        
        unity_dlls = ['GameAssembly.dll', 'mono.dll', 'UnityEngine.dll']
        for root, dirs, files in os.walk(game_path):
            for dll in unity_dlls:
                if dll in files:
                    dll_path = os.path.join(root, dll)
                    return 'x64' if self.is_64bit_dll(dll_path) else 'x86'
        
        for root, dirs, files in os.walk(game_path):
            if 'il2cpp_data' in dirs and os.path.basename(root) == 'Data':
                return 'x64 (IL2CPP)'
            if 'Mono' in dirs:
                mono_path = os.path.join(root, 'Mono')
                if os.path.exists(os.path.join(mono_path, 'x86_64')):
                    return 'x64 (Mono)'
                elif os.path.exists(os.path.join(mono_path, 'x86')):
                    return 'x86 (Mono)'
        
        for root, dirs, files in os.walk(game_path):
            for file in files:
                if file.endswith('.exe'):
                    exe_path = os.path.join(root, file)
                    try:
                        if self.is_64bit_dll(exe_path):
                            return 'x64 (from EXE)'
                        else:
                            return 'x86 (from EXE)'
                    except:
                        pass
        
        for root, dirs, files in os.walk(game_path):
            if 'globalgamemanagers' in files:
                return 'Unity (globalgamemanagers found)'
        
        return 'Unknown'

    def is_64bit_dll(self, file_path):
        with open(file_path, 'rb') as f:
            dos_header = f.read(64)
            if len(dos_header) != 64:
                return False
            e_lfanew = int.from_bytes(dos_header[60:64], byteorder='little')
            f.seek(e_lfanew)
            signature = f.read(4)
            if signature != b'PE\x00\x00':
                return False
            machine = int.from_bytes(f.read(2), byteorder='little')
            return machine == 0x8664

    def find_steam_games(self):
        games = {}
        steam_path = self._find_steam_path()
        if not steam_path:
            return games
        
        steamapps_path = os.path.join(steam_path, 'steamapps')
        if not os.path.exists(steamapps_path):
            return games
        
        # Find all library folders
        library_folders = [steamapps_path]
        vdf_path = os.path.join(steamapps_path, 'libraryfolders.vdf')
        
        if os.path.exists(vdf_path):
            try:
                with open(vdf_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Parse library folders from VDF
                import re
                paths = re.findall(r'"path"\s+"([^"]+)"', content)
                for path in paths:
                    library_path = os.path.join(path, 'steamapps')
                    if os.path.exists(library_path):
                        library_folders.append(library_path)
            except:
                pass
        
        # Find games in all library folders
        for library in library_folders:
            for file in os.listdir(library):
                if file.startswith('appmanifest_') and file.endswith('.acf'):
                    try:
                        with open(os.path.join(library, file), 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        name_match = re.search(r'"name"\s+"([^"]+)"', content)
                        installdir_match = re.search(r'"installdir"\s+"([^"]+)"', content)
                        
                        if name_match and installdir_match:
                            game_name = name_match.group(1)
                            install_dir = installdir_match.group(1)
                            game_path = os.path.join(library, 'common', install_dir)
                            
                            if os.path.exists(game_path):
                                games[game_name] = game_path
                    except:
                        pass
        
        return games

    def _find_steam_path(self):
        try:
            if platform.system() == 'Windows':
                # Try to get Steam path from registry
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam") as key:
                    return winreg.QueryValueEx(key, "InstallPath")[0]
            elif platform.system() == 'Darwin':  # macOS
                return os.path.expanduser("~/Library/Application Support/Steam")
            elif platform.system() == 'Linux':
                return os.path.expanduser("~/.local/share/Steam")
        except:
            pass
        
        # Default paths if registry fails
        if platform.system() == 'Windows':
            return "C:\\Program Files (x86)\\Steam"
        return None

    def find_epic_games(self):
        """Find Epic Games Store games installed on the system"""
        games = {}
        
        # Find Epic Games manifest file
        manifest_path = self._find_epic_manifest_path()
        if not manifest_path or not os.path.exists(manifest_path):
            return games
        
        try:
            # Find all manifest files
            manifest_dir = os.path.dirname(manifest_path)
            manifests_dir = os.path.join(manifest_dir, "Manifests")
            
            if os.path.exists(manifests_dir):
                for file in os.listdir(manifests_dir):
                    if file.endswith('.item'):
                        try:
                            with open(os.path.join(manifests_dir, file), 'r', encoding='utf-8') as f:
                                manifest_data = json.load(f)
                                
                            if "DisplayName" in manifest_data and "InstallLocation" in manifest_data:
                                game_name = manifest_data["DisplayName"]
                                install_path = manifest_data["InstallLocation"]
                                
                                if os.path.exists(install_path):
                                    games[game_name] = install_path
                        except:
                            pass
        except:
            pass
        
        return games

    def _find_epic_manifest_path(self):
        try:
            if platform.system() == 'Windows':
                # Try to get Epic Games path from registry
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Epic Games\EpicGamesLauncher") as key:
                    return winreg.QueryValueEx(key, "AppDataPath")[0]
            elif platform.system() == 'Darwin':  # macOS
                return os.path.expanduser("~/Library/Application Support/Epic/EpicGamesLauncher")
            elif platform.system() == 'Linux':
                return os.path.expanduser("~/.config/Epic/EpicGamesLauncher")
        except:
            pass
        
        # Default paths if registry fails
        if platform.system() == 'Windows':
            programdata = os.environ.get('PROGRAMDATA', 'C:\\ProgramData')
            return os.path.join(programdata, "Epic", "EpicGamesLauncher", "Data")
        return None

    def find_ms_store_games(self):
        """Find Microsoft Store games installed on the system"""
        games = {}
        
        if platform.system() != 'Windows':
            return games
        
        try:
            # Microsoft Store games are typically installed in WindowsApps folder
            program_files = os.environ.get('PROGRAMFILES', 'C:\\Program Files')
            windowsapps_path = os.path.join(program_files, 'WindowsApps')
            
            # This folder requires admin access, so we might not be able to read it
            if os.path.exists(windowsapps_path) and os.access(windowsapps_path, os.R_OK):
                for folder in os.listdir(windowsapps_path):
                    try:
                        game_path = os.path.join(windowsapps_path, folder)
                        # Extract game name from folder name (remove version and publisher)
                        game_name = folder.split('_')[0]
                        if os.path.isdir(game_path):
                            games[game_name] = game_path
                    except:
                        pass
            
            # Also check XboxGames folder
            xbox_path = os.path.join(os.environ.get('LOCALAPPDATA', 'C:\\Users\\' + os.getenv('USERNAME') + '\\AppData\\Local'), 'Packages')
            if os.path.exists(xbox_path):
                for folder in os.listdir(xbox_path):
                    if folder.startswith('Microsoft.XboxApp'):
                        try:
                            game_path = os.path.join(xbox_path, folder)
                            if os.path.isdir(game_path):
                                games[folder] = game_path
                        except:
                            pass
        except:
            pass
        
        return games

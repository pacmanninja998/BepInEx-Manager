import os
import sys
import shutil
import zipfile
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QLabel,
                           QCheckBox, QListWidgetItem, QMessageBox, QFileDialog, QInputDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QDragEnterEvent, QDropEvent

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class DropListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            # Check if at least one URL is a .dll or .zip file
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.endswith('.dll') or file_path.endswith('.zip'):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            # Check if at least one URL is a .dll or .zip file
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.endswith('.dll') or file_path.endswith('.zip'):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            files = [url.toLocalFile() for url in event.mimeData().urls() 
                    if url.toLocalFile().endswith('.dll') or url.toLocalFile().endswith('.zip')]
            if files:
                self.parent_widget.process_files(files)
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()

class PluginManager(QWidget):
    def __init__(self, game_path):
        super().__init__()
        self.game_path = game_path
        self.plugins_path = os.path.join(game_path, "BepInEx", "plugins")
        
        layout = QVBoxLayout()
        
        header = QLabel("Installed Plugins:")
        header.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        instructions = QLabel("Drag and drop .dll or .zip files to install plugins.\nEach plugin is stored in its own subfolder.")
        instructions.setStyleSheet("color: #888888;")
        
        button_layout = QHBoxLayout()
        
        add_btn = QPushButton("Add Plugin")
        add_btn.clicked.connect(self.add_plugin)
        button_layout.addWidget(add_btn)
        
        refresh_btn = QPushButton("Refresh Plugins")
        refresh_btn.clicked.connect(self.load_plugins)
        button_layout.addWidget(refresh_btn)
        
        # Use our custom list widget with drag and drop support
        self.plugin_list = DropListWidget(self)
        self.plugin_list.setAlternatingRowColors(True)
        
        layout.addWidget(header)
        layout.addWidget(instructions)
        layout.addLayout(button_layout)
        layout.addWidget(self.plugin_list)
        
        self.setLayout(layout)
        
        if not os.path.exists(self.plugins_path):
            os.makedirs(self.plugins_path)
            
        self.load_plugins()
    
    def load_plugins(self):
        self.plugin_list.clear()
        
        if not os.path.exists(self.plugins_path):
            os.makedirs(self.plugins_path)
            return
        
        subfolders = [f for f in os.listdir(self.plugins_path) 
                     if os.path.isdir(os.path.join(self.plugins_path, f))]
        
        if not subfolders:
            self.plugin_list.addItem("No plugins installed")
            return
        
        for subfolder in subfolders:
            subfolder_path = os.path.join(self.plugins_path, subfolder)
            
            folder_item = QListWidgetItem(f"📁 {subfolder}")
            folder_item.setData(Qt.UserRole, {"type": "folder", "path": subfolder_path})
            folder_item.setIcon(QIcon(resource_path("icons/folder.png")))
            self.plugin_list.addItem(folder_item)
            
            dll_files = [f for f in os.listdir(subfolder_path) 
                        if f.endswith(".dll") or f.endswith(".bak")]
            
            for dll_file in dll_files:
                item = QListWidgetItem(f"    {dll_file}")
                item.setData(Qt.UserRole, {"type": "file", "path": os.path.join(subfolder_path, dll_file)})
                
                checkbox = QCheckBox()
                checkbox.setChecked(dll_file.endswith(".dll"))
                checkbox.stateChanged.connect(lambda state, f=dll_file, sf=subfolder_path: self.toggle_plugin(f, sf, state))
                
                self.plugin_list.addItem(item)
                self.plugin_list.setItemWidget(item, checkbox)
    
    def toggle_plugin(self, filename, subfolder_path, state):
        full_path = os.path.join(subfolder_path, filename)
        
        if state == Qt.Checked and filename.endswith(".bak"):
            # Enable plugin
            new_path = full_path.replace(".bak", ".dll")
            os.rename(full_path, new_path)
        elif state == Qt.Unchecked and filename.endswith(".dll"):
            # Disable plugin
            new_path = full_path + ".bak"
            os.rename(full_path, new_path)
        
        self.load_plugins()
    
    def add_plugin(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, 
            "Select Plugin Files", 
            "", 
            "Plugin Files (*.dll *.zip);;DLL Files (*.dll);;ZIP Files (*.zip)"
        )
        if files:
            self.process_files(files)
    
    def process_files(self, files):
        plugin_name, ok = QInputDialog.getText(self, "Plugin Name", "Enter a name for this plugin/mod:")
        if not ok or not plugin_name:
            return
        
        plugin_folder = os.path.join(self.plugins_path, plugin_name)
        if not os.path.exists(plugin_folder):
            os.makedirs(plugin_folder)
        
        dll_count = 0
        
        for file_path in files:
            if file_path.endswith('.dll'):
                shutil.copy(file_path, os.path.join(plugin_folder, os.path.basename(file_path)))
                dll_count += 1
            elif file_path.endswith('.zip'):
                extracted_dlls = self.handle_zip(file_path, plugin_folder)
                dll_count += extracted_dlls
        
        QMessageBox.information(self, "Success", f"{dll_count} DLL files installed to {plugin_name}")
        self.load_plugins()
    
    def handle_zip(self, zip_path, plugin_folder):
        extracted_count = 0
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Get all files in the zip
                all_files = zip_ref.namelist()
                
                # Find all DLL files (including those in subfolders)
                dll_files = [f for f in all_files if f.endswith('.dll')]
                
                if not dll_files:
                    QMessageBox.warning(self, "Warning", f"No DLL files found in {os.path.basename(zip_path)}")
                    return 0
                
                # Extract each DLL file
                for dll_file in dll_files:
                    # Extract to a temporary location
                    zip_ref.extract(dll_file, "temp_extract")
                    
                    # Get just the filename without any path
                    dll_filename = os.path.basename(dll_file)
                    
                    # Copy from temp location to plugin folder
                    temp_path = os.path.join("temp_extract", dll_file)
                    dest_path = os.path.join(plugin_folder, dll_filename)
                    
                    # If the file already exists, add a number to the filename
                    if os.path.exists(dest_path):
                        base_name, ext = os.path.splitext(dll_filename)
                        counter = 1
                        while os.path.exists(os.path.join(plugin_folder, f"{base_name}_{counter}{ext}")):
                            counter += 1
                        dest_path = os.path.join(plugin_folder, f"{base_name}_{counter}{ext}")
                    
                    # Copy the file
                    shutil.copy2(temp_path, dest_path)
                    extracted_count += 1
                
                # Clean up temp directory
                if os.path.exists("temp_extract"):
                    shutil.rmtree("temp_extract")
                
                return extracted_count
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to extract ZIP file: {str(e)}")
            return 0

import os
import sys
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QLabel, QPushButton, QListWidget, QListWidgetItem,
                           QCheckBox, QComboBox, QMessageBox, QFileDialog,
                           QPlainTextEdit)
from PyQt5.QtCore import Qt

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class ConfigEditor(QWidget):
    def __init__(self, game_path):
        super().__init__()
        self.game_path = game_path
        self.config_path = os.path.join(game_path, "BepInEx", "config")
        
        # Create layout
        layout = QVBoxLayout()
        
        # Config file selector
        self.config_selector = QComboBox()
        self.config_selector.currentIndexChanged.connect(self.load_selected_config)
        
        # Config editor
        self.editor = QPlainTextEdit()
        self.editor.setLineWrapMode(QPlainTextEdit.NoWrap)
        
        # Save button
        save_btn = QPushButton("Save Changes")
        save_btn.clicked.connect(self.save_config)
        
        layout.addWidget(QLabel("Select Configuration File:"))
        layout.addWidget(self.config_selector)
        layout.addWidget(self.editor)
        layout.addWidget(save_btn)
        
        self.setLayout(layout)
        self.load_config_files()
    
    def load_config_files(self):
        """Load all config files from the config directory"""
        self.config_selector.clear()
        
        if not os.path.exists(self.config_path):
            return
        
        for file in os.listdir(self.config_path):
            if file.endswith(".cfg"):
                self.config_selector.addItem(file)
    
    def load_selected_config(self):
        """Load the selected config file into the editor"""
        selected = self.config_selector.currentText()
        if not selected:
            return
        
        file_path = os.path.join(self.config_path, selected)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.editor.setPlainText(f.read())
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load config: {str(e)}")
    
    def save_config(self):
        """Save changes to the config file"""
        selected = self.config_selector.currentText()
        if not selected:
            return
        
        file_path = os.path.join(self.config_path, selected)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.editor.toPlainText())
            QMessageBox.information(self, "Success", "Configuration saved successfully")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save config: {str(e)}")

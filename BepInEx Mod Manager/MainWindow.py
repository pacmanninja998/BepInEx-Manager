import os
import sys
from PyQt5.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
                             QListWidget, QListWidgetItem, QMessageBox, QFileDialog,
                             QStyledItemDelegate, QStyle)
from PyQt5.QtCore import Qt, QSize, QRect
from PyQt5.QtGui import QPixmap, QIcon
from GameManager import GameManagementWindow
from Installer import Installer
from game_finder import GameFinder

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class GameItemDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def paint(self, painter, option, index):
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
            painter.setPen(option.palette.highlightedText().color())
        else:
            painter.setPen(option.palette.text().color())

        text_rect = option.rect.adjusted(24, 0, -24, 0)
        painter.drawText(text_rect, Qt.AlignVCenter, index.data())

        status_icon = index.data(Qt.UserRole + 1)
        if status_icon:
            icon_size = QSize(16, 16)
            icon_rect = QRect(option.rect.left() + 4, option.rect.top() + (option.rect.height() - icon_size.height()) // 2,
                              icon_size.width(), icon_size.height())
            status_icon.paint(painter, icon_rect)

        source_icon = index.data(Qt.DecorationRole)
        if source_icon:
            icon_size = QSize(16, 16)
            icon_rect = QRect(option.rect.right() - icon_size.width() - 4,
                              option.rect.top() + (option.rect.height() - icon_size.height()) // 2,
                              icon_size.width(), icon_size.height())
            source_icon.paint(painter, icon_rect)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BepInEx Loader Installer")
        self.setMinimumSize(500, 600)
        self.setStyleSheet("""
            QMainWindow, QWidget { background-color: #2D2D2D; color: #FFFFFF; }
            QPushButton { background-color: #3D3D3D; border-radius: 4px; padding: 8px; }
            QPushButton:hover { background-color: #4D4D4D; }
        """)

        self.logo_label = QLabel()
        logo_pixmap = QPixmap(resource_path("icons/app_icon.png"))
        self.logo_label.setPixmap(logo_pixmap.scaled(200, 100, Qt.KeepAspectRatio))
        self.logo_label.setAlignment(Qt.AlignCenter)

        self.instructions = QLabel("To install BepInEx, click on one of the games below.\nIf you can't find your game on the list, add it manually.")
        self.instructions.setAlignment(Qt.AlignCenter)

        self.game_list = QListWidget()
        self.game_list.setStyleSheet("QListWidget::item { padding: 10px; }")
        self.game_list.itemClicked.connect(self.on_game_selected)
        self.game_list.setItemDelegate(GameItemDelegate(self.game_list))

        self.add_game_btn = QPushButton("Add Game Manually")
        self.add_game_btn.clicked.connect(self.add_game_manually)

        self.author_label = QLabel("@Pacmanninja998")
        self.URL_label = QLabel("github.com/pacmanninja998/BepInEx-Manager")
        self.version_label = QLabel("v1.0.0")

        footer_layout = QHBoxLayout()
        footer_layout.addWidget(self.author_label, alignment=Qt.AlignLeft)
        footer_layout.addWidget(self.URL_label, alignment=Qt.AlignCenter)
        footer_layout.addWidget(self.version_label, alignment=Qt.AlignRight)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.logo_label)
        main_layout.addWidget(self.instructions)
        main_layout.addWidget(self.game_list)
        main_layout.addWidget(self.add_game_btn)
        main_layout.addLayout(footer_layout)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.load_games()

    def load_games(self):
        self.game_list.clear()
        game_finder = GameFinder()
        games = game_finder.find_unity_games()

        for game_name, game_info in games.items():
            item = QListWidgetItem(game_name)
            item.setData(Qt.UserRole, game_info)

            source = game_info['source']
            if source == 'Steam':
                source_icon = QIcon(resource_path("icons/steam_icon.png"))
            elif source == 'Epic Games':
                source_icon = QIcon(resource_path("icons/epic_icon.png"))
            elif source == 'Microsoft Store':
                source_icon = QIcon(resource_path("icons/ms_store_icon.png"))
            else:
                source_icon = QIcon()

            item.setIcon(source_icon)

            if os.path.exists(os.path.join(game_info['path'], 'BepInEx')):
                item.setData(Qt.UserRole + 1, QIcon(resource_path("icons/checkmark.png")))
            else:
                item.setData(Qt.UserRole + 1, QIcon(resource_path("icons/download.png")))

            self.game_list.addItem(item)

    def on_game_selected(self, item):
        game_name = item.text()
        game_info = item.data(Qt.UserRole)
        game_path = game_info['path']

        if os.path.exists(os.path.join(game_path, 'BepInEx')):
            self.game_window = GameManagementWindow(game_name, game_path)
            self.game_window.show()
        else:
            reply = QMessageBox.question(self, "Install BepInEx",
                                         f"Would you like to install BepInEx for {game_name}?",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                installer = Installer(self)
                installer.install_bepinex(game_path, game_info['platform'])

    def add_game_manually(self):
        game_dir = QFileDialog.getExistingDirectory(self, "Select Game Directory")
        if not game_dir:
            return

        if not os.path.isdir(game_dir):
            QMessageBox.warning(self, "Invalid Directory", "Please select a valid game directory")
            return

        game_name = os.path.basename(game_dir)
        game_finder = GameFinder()
        platform = game_finder.get_unity_platform(game_dir) if game_finder.is_unity_game(game_dir) else "Unknown"

        if platform == "Unknown":
            reply = QMessageBox.question(self, "Non-Unity Game",
                                         "This doesn't appear to be a Unity game. Continue anyway?",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.No:
                return

        item = QListWidgetItem(game_name)
        item.setData(Qt.UserRole, {'path': game_dir, 'platform': platform, 'source': 'Manual'})
        self.game_list.addItem(item)

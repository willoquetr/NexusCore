import sys
import os
import json
from core.logger import logger
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                               QStackedWidget, QFrame, QScrollArea, QGridLayout,
                               QSizePolicy, QGraphicsDropShadowEffect, QProgressBar,
                               QSplitter, QFileDialog, QInputDialog, QSpacerItem,
                               QFileIconProvider, QMenu)
from PySide6.QtCore import Qt, QSize, QTimer, QFileInfo, QThread, Signal
from PySide6.QtGui import QIcon, QColor, QFontDatabase, QFont, QPainter, QPainterPath, QPen, QLinearGradient, QPixmap
import qtawesome as qta
from core.database import get_session, GameSession, HardwareSnapshot, CustomGame
from core.telemetry.collector import TelemetryCollector
from core.ai.nexus_agent import NexusAgent, load_key
from core.telemetry.session_manager import SessionManager

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class Sidebar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(260)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 40, 0, 30) # Increased bottom margin from 20 to 30
        layout.setSpacing(12) # Slightly tighter spacing to gain space below

        # Logo Area - Centered & Enlarged (~3x from 65 to 180)
        self.logo_icon = QLabel()
        self.logo_icon.setObjectName("LogoIcon")
        self.logo_icon.setFixedSize(180, 180)
        logo_pix = QPixmap(resource_path("assets/logonexuscore.png"))
        if not logo_pix.isNull():
            self.logo_icon.setPixmap(logo_pix.scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.logo_icon.setText("NX")
        self.logo_icon.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(self.logo_icon, alignment=Qt.AlignCenter)
        layout.addSpacing(30)

        # Navigation
        self.btn_games = self.create_nav_button("DATA_LIBRARY", "fa5s.th-large", active=True)
        self.btn_system = self.create_nav_button("HARDWARE_SYNC", "fa5s.microchip")
        self.btn_settings = self.create_nav_button("CORE_CONFIG", "fa5s.terminal")

        layout.addWidget(self.btn_games)
        layout.addWidget(self.btn_system)
        layout.addWidget(self.btn_settings)
        layout.addStretch()

        # Status HUD - Centered Text
        self.status_box = QFrame()
        self.status_box.setObjectName("StatusHUD")
        status_layout = QVBoxLayout(self.status_box)
        status_layout.setAlignment(Qt.AlignCenter)
        self.st_title = QLabel("SYSTEM_STATUS")
        self.st_title.setObjectName("HUDSmallLabel")
        self.st_title.setAlignment(Qt.AlignCenter)
        self.st_val = QLabel("ENCRYPTED_LINK")
        self.st_val.setObjectName("HUDStatusLabel")
        self.st_val.setAlignment(Qt.AlignCenter)
        status_layout.addWidget(self.st_title)
        status_layout.addWidget(self.st_val)
        layout.addWidget(self.status_box)
        
        self.btn_exit = QPushButton("TERMINATE_SESSION")
        self.btn_exit.setObjectName("ExitButton")
        layout.addWidget(self.btn_exit)

        # Attribution "Made by Foz"
        self.footer_label = QLabel("Made by Foz")
        self.footer_label.setObjectName("FooterNote")
        self.footer_label.setAlignment(Qt.AlignCenter)
        layout.addSpacing(10)
        layout.addWidget(self.footer_label)

    def create_nav_button(self, text, icon_name, active=False):
        btn = QPushButton(text)
        btn.setObjectName("NavButton")
        btn.setProperty("active", active)
        btn.setIcon(qta.icon(icon_name, color="#00d1ff"))
        btn.setIconSize(QSize(24, 24)) # Increased icon size
        return btn

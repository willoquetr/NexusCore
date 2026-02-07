import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                               QStackedWidget, QFrame, QScrollArea, QGridLayout,
                               QSizePolicy, QGraphicsDropShadowEffect, QProgressBar,
                               QSplitter, QFileDialog, QInputDialog, QSpacerItem)
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QIcon, QColor, QFontDatabase, QFont, QPainter, QPainterPath, QPen, QLinearGradient
import qtawesome as qta
from core.database import get_session, GameSession, HardwareSnapshot, CustomGame
from core.telemetry.collector import TelemetryCollector
from core.ai.nexus_agent import NexusAgent, load_key
from core.telemetry.session_manager import SessionManager

class Sidebar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(260)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 40, 20, 20)
        layout.setSpacing(15)

        # Logo Area
        logo_layout = QHBoxLayout()
        self.logo_icon = QLabel("NX")
        self.logo_icon.setObjectName("LogoIcon")
        self.logo_icon.setFixedSize(45, 45)
        self.logo_icon.setAlignment(Qt.AlignCenter)
        
        logo_text_vbox = QVBoxLayout()
        logo_text = QLabel("NEXUS")
        logo_text.setObjectName("LogoTitle")
        core_text = QLabel("CORE PROTOCOL")
        core_text.setObjectName("LogoSubtitle")
        logo_text_vbox.addWidget(logo_text)
        logo_text_vbox.addWidget(core_text)
        
        logo_layout.addWidget(self.logo_icon)
        logo_layout.addLayout(logo_text_vbox)
        layout.addLayout(logo_layout)
        layout.addSpacing(50)

        # Navigation
        self.btn_games = self.create_nav_button("DATA_LIBRARY", "fa5s.th-large", active=True)
        self.btn_system = self.create_nav_button("HARDWARE_SYNC", "fa5s.microchip")
        self.btn_settings = self.create_nav_button("CORE_CONFIG", "fa5s.terminal")

        layout.addWidget(self.btn_games)
        layout.addWidget(self.btn_system)
        layout.addWidget(self.btn_settings)
        layout.addStretch()

        # Status HUD
        self.status_box = QFrame()
        self.status_box.setObjectName("StatusHUD")
        status_layout = QVBoxLayout(self.status_box)
        st_title = QLabel("SYSTEM_STATUS")
        st_title.setObjectName("HUDSmallLabel")
        self.st_val = QLabel("ENCRYPTED_LINK")
        self.st_val.setObjectName("HUDStatusLabel")
        status_layout.addWidget(st_title)
        status_layout.addWidget(self.st_val)
        layout.addWidget(self.status_box)
        
        self.btn_exit = QPushButton("TERMINATE_SESSION")
        self.btn_exit.setObjectName("ExitButton")
        layout.addWidget(self.btn_exit)

    def create_nav_button(self, text, icon_name, active=False):
        btn = QPushButton(text)
        btn.setObjectName("NavButton")
        btn.setProperty("active", active)
        btn.setIcon(qta.icon(icon_name, color="#00d1ff"))
        return btn

class Header(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Header")
        self.setFixedHeight(70)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(30, 0, 30, 0)
        
        self.search_bar = QLineEdit()
        self.search_bar.setObjectName("SearchInput")
        self.search_bar.setPlaceholderText("QUERY_DATABASE...")
        self.search_bar.setFixedWidth(350)
        
        layout.addWidget(self.search_bar)
        layout.addStretch()
        
        self.time_lbl = QLabel("LCL 00:00:00")
        self.time_lbl.setObjectName("HUDClock")
        user_info = QLabel("OPERATOR: ADMIN")
        user_info.setObjectName("HUDUser")
        
        layout.addWidget(self.time_lbl)
        layout.addSpacing(30)
        layout.addWidget(user_info)

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                               QStackedWidget, QFrame, QScrollArea, QGridLayout,
                               QSizePolicy, QGraphicsDropShadowEffect, QProgressBar,
                               QSplitter, QFileDialog, QInputDialog, QSpacerItem,
                               QFileIconProvider, QMenu)
from PySide6.QtCore import Qt, QSize, QTimer, QFileInfo

class GameCard(QFrame):

    def __init__(self, title, launcher, exe_path=None, parent_view=None):

        super().__init__(parent_view)

        self.setFixedSize(110, 140)

        self.setObjectName("GameIcon")

        self.exe_path = exe_path

        self.title = title

        self.parent_view = parent_view

        self.setCursor(Qt.PointingHandCursor)

        self.setContextMenuPolicy(Qt.CustomContextMenu)

        self.customContextMenuRequested.connect(self.show_context_menu)

        

        layout = QVBoxLayout(self)

        layout.setContentsMargins(5, 5, 5, 5)

        

        self.icon_frame = QFrame()

        self.icon_frame.setObjectName("IconContainer")

        self.icon_frame.setFixedSize(95, 95)

        

        icon_layout = QVBoxLayout(self.icon_frame)

        self.icon_lbl = QLabel()

        self.icon_lbl.setAlignment(Qt.AlignCenter)

        

        if self.exe_path and os.path.exists(self.exe_path):

            try:

                file_info = QFileInfo(self.exe_path)

                icon = QFileIconProvider().icon(file_info)

                self.icon_lbl.setPixmap(icon.pixmap(50, 50))

            except:

                self.icon_lbl.setPixmap(qta.icon("fa5s.gamepad", color="#00d1ff").pixmap(40, 40))

        else:

            self.icon_lbl.setPixmap(qta.icon("fa5s.gamepad", color="#00d1ff").pixmap(40, 40))

            

        icon_layout.addWidget(self.icon_lbl)

        

        self.title_lbl = QLabel(title)

        self.title_lbl.setObjectName("GameIconTitle")

        self.title_lbl.setAlignment(Qt.AlignCenter)

        self.title_lbl.setWordWrap(True)

        

        layout.addWidget(self.icon_frame, alignment=Qt.AlignCenter)

        layout.addWidget(self.title_lbl)



    def show_context_menu(self, pos):

        menu = QMenu(self)

        menu.setObjectName("HUDMenu")

        delete_action = menu.addAction("RETIRER DU NEXUS")

        action = menu.exec(self.mapToGlobal(pos))

        if action == delete_action:

            self.parent_view.delete_game(self.title)



    def mousePressEvent(self, event):

        if event.button() == Qt.LeftButton:

            if self.exe_path and os.path.exists(self.exe_path):

                try: os.startfile(self.exe_path)

                except: pass

        super().mousePressEvent(event)



class GamesView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_win = parent
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        header_box = QHBoxLayout()
        title_vbox = QVBoxLayout()
        title = QLabel("NEXUS LIBRARY")
        title.setObjectName("ViewTitle")
        subtitle = QLabel("Exploration des environnements virtuels détectés")
        subtitle.setObjectName("ViewSubtitle")
        title_vbox.addWidget(title)
        title_vbox.addWidget(subtitle)
        header_box.addLayout(title_vbox)
        header_box.addStretch()
        
        self.count_lbl = QLabel("0 ELEMENTS")
        self.count_lbl.setObjectName("HUDCountBadge")
        header_box.addWidget(self.count_lbl)
        header_box.addSpacing(20)
        
        self.scan_btn = QPushButton("SCAN SYSTEM")
        self.scan_btn.setObjectName("ScanBtn")
        self.add_btn = QPushButton("CUSTOM PATH")
        self.add_btn.setObjectName("ActionBtn")
        header_box.addWidget(self.add_btn)
        header_box.addWidget(self.scan_btn)
        layout.addLayout(header_box)
        
        # Launcher Filter Bar
        self.filter_bar = QHBoxLayout()
        launchers = ["TOUS", "STEAM", "EPIC", "BATTLE.NET", "RIOT", "CUSTOM"]
        for l in launchers:
            btn = QPushButton(l)
            btn.setObjectName("FilterButton")
            self.filter_bar.addWidget(btn)
        self.filter_bar.addStretch()
        layout.addLayout(self.filter_bar)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        self.content_widget = QWidget()
        self.grid = QGridLayout(self.content_widget)
        self.grid.setSpacing(25)
        self.grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        scroll.setWidget(self.content_widget)
        layout.addWidget(scroll)
        self.refresh_games()

    def add_custom_game(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Sélectionner l'exécutable", "", "Exécutables (*.exe)")
        if file_path:
            title, ok = QInputDialog.getText(self, "Nom du jeu", "Entrez le nom :", text=os.path.basename(file_path).replace(".exe", ""))
            if ok and title:
                db = get_session()
                new_game = CustomGame(title=title, exe_path=file_path)
                db.add(new_game)
                db.commit()
                db.close()
                self.refresh_games()

    def refresh_games(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        
        # ... (Scans remain same) ...
        from plugins.scanner_launchers.scanner import scan_launchers
        installed_launchers = scan_launchers()
        from plugins.scanner_steam.scanner import scan_steam_games
        steam_games = scan_steam_games()
        from plugins.scanner_epic import scan_epic_games
        epic_games = scan_epic_games()
        db = get_session()
        custom_games = db.query(CustomGame).all()
        db.close()
        
        all_items = []
        for l in installed_launchers: all_items.append({"title": l['title'], "launcher": "Launcher", "exe": l['exe']})
        for g in steam_games: 
            exe_p = None
            if os.path.exists(g['install_dir']):
                for f in os.listdir(g['install_dir']):
                    if f.endswith(".exe") and not any(x in f.lower() for x in ["unity", "crash", "helper", "redist"]):
                        exe_p = os.path.join(g['install_dir'], f); break
            all_items.append({"title": g['title'], "launcher": "Steam", "exe": exe_p})
        for g in epic_games: all_items.append({"title": g['title'], "launcher": "Epic", "exe": g['exe']})
        for g in custom_games: all_items.append({"title": g.title, "launcher": "Custom", "exe": g.exe_path})
            
        self.parent_win.session_mgr.update_games_list(all_items)
        for i, item in enumerate(all_items):
            card = GameCard(item["title"], item["launcher"], exe_path=item.get("exe"), parent_view=self)
            self.grid.addWidget(card, i // 7, i % 7) 
        self.count_lbl.setText(f"{len(all_items)} ELEMENTS")

    def delete_game(self, title):
        db = get_session()
        game = db.query(CustomGame).filter(CustomGame.title == title).first()
        if game:
            db.delete(game)
            db.commit()
            print(f"DEBUG: {title} supprimé.")
        db.close()
        self.refresh_games()

# --- TECH GEOMETRY COMPONENTS ---

class TechFrame(QFrame):
    """Un cadre avec des angles coupés et des bordures néon style HUD."""
    def __init__(self, parent=None, color="#00d1ff"):
        super().__init__(parent)
        self.color = QColor(color)
        self.bg_color = QColor(255, 255, 255, 240)
        self.hover = False

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Dimensions
        w, h = self.width(), self.height()
        cut = 15 
        
        path = QPainterPath()
        path.moveTo(cut, 0)
        path.lineTo(w - cut, 0)
        path.lineTo(w, cut)
        path.lineTo(w, h)
        path.lineTo(cut, h)
        path.lineTo(0, h - cut)
        path.closeSubpath()
        
        # Fond dynamique selon le thème
        painter.fillPath(path, self.bg_color)
        
        # Bordure Néon
        pen = QPen(self.color, 2)
        if self.hover:
            pen.setWidth(3)
            painter.setOpacity(0.3)
            painter.strokePath(path, QPen(self.color, 6))
            painter.setOpacity(1.0)
            
        painter.setPen(pen)
        painter.drawPath(path)
        
        # Déco technique
        painter.setPen(QPen(self.color, 4))
        painter.drawLine(0, 0, cut, 0)
        painter.drawLine(0, 0, 0, cut)
        painter.drawLine(w, h, w - cut, h)
        painter.drawLine(w, h, w, h - cut)
        
        painter.end()

class StatCard(TechFrame):
    def __init__(self, title, icon_name, color_hex, progress_type, parent=None):
        super().__init__(parent, color_hex)
        self.setFixedSize(240, 140)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QHBoxLayout()
        icon_lbl = QLabel()
        icon_lbl.setPixmap(qta.icon(icon_name, color=color_hex).pixmap(20, 20))
        
        text_layout = QVBoxLayout()
        text_layout.setSpacing(0)
        self.title_lbl = QLabel(title)
        self.title_lbl.setObjectName("StatTitle")
        self.value_lbl = QLabel("--")
        self.value_lbl.setObjectName("StatValue")
        
        text_layout.addWidget(self.title_lbl)
        text_layout.addWidget(self.value_lbl)
        
        header.addWidget(icon_lbl)
        header.addLayout(text_layout)
        header.addStretch()
        
        layout.addLayout(header)
        layout.addStretch()
        
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(2)
        layout.addWidget(self.progress)

    def enterEvent(self, event):
        self.hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.hover = False
        self.update()
        super().leaveEvent(event)

    def update_data(self, value_text, usage_percent):
        self.value_lbl.setText(value_text)
        self.progress.setValue(int(usage_percent))

class ThermalCard(TechFrame):
    def __init__(self, title, temp_val, parent=None):
        super().__init__(parent, color="#00d1ff")
        self.setFixedHeight(100)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        
        icon = QLabel()
        icon.setPixmap(qta.icon("fa5s.thermometer-half", color="#00d1ff").pixmap(24, 24))
        
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        title_lbl = QLabel(title)
        title_lbl.setObjectName("StatTitle")
        self.temp_lbl = QLabel(f"{temp_val}°C")
        self.temp_lbl.setObjectName("StatValue")
        
        text_layout.addWidget(title_lbl)
        text_layout.addWidget(self.temp_lbl)
        
        self.badge = QLabel("STABLE")
        self.badge.setObjectName("ActionBtn") # Réutilise le style bouton
        
        layout.addWidget(icon)
        layout.addSpacing(15)
        layout.addLayout(text_layout)
        layout.addStretch()
        layout.addWidget(self.badge)
        
    def update_temp(self, temp):
        self.temp_lbl.setText(f"{temp:.1f}°C")

    def enterEvent(self, event):
        self.hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.hover = False
        self.update()
        super().leaveEvent(event)


class BackgroundGrid(QWidget):
    """Futuristic scalable background (no bitmaps) driven by theme tokens."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme_name = "arctic"
        self.theme_color = QColor("#00d1ff")   # accent
        self.base_bg = QColor(255, 255, 255, 255)

    def set_theme(self, theme_name: str, accent_hex: str, base_bg: QColor):
        self.theme_name = theme_name
        self.theme_color = QColor(accent_hex)
        self.base_bg = QColor(base_bg)
        self.update()

    def _draw_diagonal_plate(self, painter: QPainter, rect, color: QColor, cut=24, opacity=0.18):
        painter.save()
        painter.setOpacity(opacity)
        path = QPainterPath()
        x, y, w, h = rect
        # cut-corner diagonal plate
        path.moveTo(x + cut, y)
        path.lineTo(x + w, y)
        path.lineTo(x + w, y + h - cut)
        path.lineTo(x + w - cut, y + h)
        path.lineTo(x, y + h)
        path.lineTo(x, y + cut)
        path.closeSubpath()
        painter.fillPath(path, color)
        painter.restore()

    def paintEvent(self, event):
        w, h = self.width(), self.height()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # --- Base gradient per theme ---
        grad = QLinearGradient(0, 0, w, h)
        if self.theme_name == "arctic":
            grad.setColorAt(0.0, QColor(255, 255, 255))
            grad.setColorAt(0.55, QColor(244, 250, 255))
            grad.setColorAt(1.0, QColor(226, 244, 255))
        elif self.theme_name == "dark":
            grad.setColorAt(0.0, QColor(2, 6, 23))
            grad.setColorAt(0.6, QColor(15, 23, 42))
            grad.setColorAt(1.0, QColor(30, 41, 59))
        elif self.theme_name == "cyberpunk":
            grad.setColorAt(0.0, QColor(0, 0, 0))
            grad.setColorAt(1.0, QColor(15, 0, 18))
        else:  # girly
            grad.setColorAt(0.0, QColor(255, 241, 242))
            grad.setColorAt(0.6, QColor(255, 250, 251))
            grad.setColorAt(1.0, QColor(255, 228, 238))

        painter.fillRect(self.rect(), grad)

        # --- Large diagonal plates (reference vibe) ---
        plate_color = QColor(self.theme_color)
        if self.theme_name == "arctic":
            plate_color = QColor(0, 147, 200)
        if self.theme_name == "girly":
            plate_color = QColor(244, 114, 182)

        self._draw_diagonal_plate(painter, (int(w*0.18), int(h*0.08), int(w*0.72), int(h*0.24)), plate_color, cut=28, opacity=0.08)
        self._draw_diagonal_plate(painter, (int(w*0.08), int(h*0.32), int(w*0.56), int(h*0.22)), plate_color, cut=28, opacity=0.06)
        self._draw_diagonal_plate(painter, (int(w*0.36), int(h*0.62), int(w*0.56), int(h*0.28)), plate_color, cut=32, opacity=0.05)

        # --- Technical linework / scanlines ---
        painter.save()
        if self.theme_name == "arctic":
            painter.setOpacity(0.06)
        elif self.theme_name == "dark":
            painter.setOpacity(0.07)
        elif self.theme_name == "cyberpunk":
            painter.setOpacity(0.10)
        else:
            painter.setOpacity(0.07)

        pen = QPen(self.theme_color, 1)
        painter.setPen(pen)

        # subtle scanlines
        gap = 12 if self.theme_name in ("cyberpunk", "dark") else 16
        for y in range(0, h, gap):
            painter.drawLine(0, y, w, y)

        # dotted grid (lighter than before)
        painter.setOpacity(painter.opacity() * 0.55)
        dot_gap = 44 if self.theme_name == "arctic" else 40
        for x in range(0, w, dot_gap):
            for y in range(0, h, dot_gap):
                painter.drawPoint(x, y)

        painter.restore()

        # --- Corner HUD brackets ---
        painter.setOpacity(0.9 if self.theme_name == "cyberpunk" else 0.65)
        painter.setPen(QPen(self.theme_color, 2))
        # top-left
        painter.drawLine(0, 120, 120, 0)
        # top-right
        painter.drawLine(w-120, 0, w, 120)
        # bottom-left
        painter.drawLine(0, h-120, 120, h)
        # bottom-right
        painter.drawLine(w-120, h, w, h-120)

        painter.end()

class SettingsPanel(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.parent_win = parent

        layout = QVBoxLayout(self)

        layout.setContentsMargins(50, 50, 50, 50)

        layout.setSpacing(20)

        

        title = QLabel("CORE_CONFIGURATION")

        title.setObjectName("ViewTitle")

        layout.addWidget(title)

        

        ai_box = QFrame()

        ai_box.setObjectName("SettingsCard")

        ai_layout = QVBoxLayout(ai_box)

        ai_layout.setContentsMargins(25, 25, 25, 25)

        

        ai_title = QLabel("ARTIFICIAL_INTELLIGENCE_LINK")

        ai_title.setObjectName("HUDSmallLabel")

        ai_layout.addWidget(ai_title)

        

        from PySide6.QtWidgets import QComboBox

        self.ai_provider = QComboBox()

        self.ai_provider.addItems(["Groq (Llama 3.3)", "Google Gemini (2.0 Flash)", "OpenAI (GPT-4o)"])

        self.ai_provider.setFixedHeight(45)

        ai_layout.addWidget(QLabel("PROVIDER:"))

        ai_layout.addWidget(self.ai_provider)

        

        self.api_key_input = QLineEdit()

        self.api_key_input.setPlaceholderText("ENTER_API_KEY_HERE...")

        self.api_key_input.setEchoMode(QLineEdit.Password)

        self.api_key_input.setFixedHeight(45)

        ai_layout.addWidget(QLabel("API_KEY:"))

        ai_layout.addWidget(self.api_key_input)

        

        save_ai_btn = QPushButton("UPDATE_AI_CORE")

        save_ai_btn.setObjectName("ScanBtn")

        save_ai_btn.setFixedHeight(45)

        save_ai_btn.clicked.connect(self.save_ai_settings)

        ai_layout.addWidget(save_ai_btn)

        layout.addWidget(ai_box)

        

        theme_box = QFrame()

        theme_box.setObjectName("SettingsCard")

        theme_layout = QVBoxLayout(theme_box)

        theme_layout.setContentsMargins(25, 25, 25, 25)

        theme_title = QLabel("VISUAL_INTERFACE_SKIN")

        theme_title.setObjectName("HUDSmallLabel")

        theme_layout.addWidget(theme_title)

        

        self.theme_selector = QComboBox()

        self.theme_selector.addItems(["Arctic White", "Deep Dark", "Cyberpunk", "Girly Rose"])

        self.theme_selector.setFixedHeight(45)

        theme_layout.addWidget(QLabel("SELECT_SKIN:"))

        theme_layout.addWidget(self.theme_selector)

        

        apply_theme_btn = QPushButton("APPLY_SKIN")

        apply_theme_btn.setObjectName("ActionBtn")

        apply_theme_btn.setFixedHeight(45)

        apply_theme_btn.clicked.connect(self.apply_theme)

        theme_layout.addWidget(apply_theme_btn)

        layout.addWidget(theme_box)

        layout.addStretch()



    def save_ai_settings(self):

        key = self.api_key_input.text().strip()

        provider = self.ai_provider.currentText()

        if key:

            with open("data/config.json", "w") as f:

                json.dump({"api_key": key, "provider": provider}, f)

            self.parent_win.nexus_ai.setup_model(key)



    def apply_theme(self):

        theme_map = {"Arctic White": "arctic", "Deep Dark": "dark", "Cyberpunk": "cyberpunk", "Girly Rose": "girly"}

        selected = theme_map.get(self.theme_selector.currentText(), "arctic")

        colors = {

            "arctic": {"accent": "#00d1ff", "bg": QColor(255, 255, 255, 240)},

            "dark": {"accent": "#38bdf8", "bg": QColor(30, 41, 59, 240)},

            "cyberpunk": {"accent": "#f0abfc", "bg": QColor(0, 0, 0, 240)},

            "girly": {"accent": "#f472b6", "bg": QColor(255, 255, 255, 240)}

        }

        theme_data = colors[selected]

        def update_widget(w, t):

            w.setProperty("theme", t)

            if isinstance(w, TechFrame):

                w.color = QColor(theme_data["accent"])

                w.bg_color = theme_data["bg"]

            w.style().unpolish(w)

            w.style().polish(w)

            for child in w.findChildren(QWidget): update_widget(child, t)

        update_widget(self.parent_win, selected)

        self.parent_win.bg.set_theme(selected, theme_data["accent"], theme_data["bg"])

        # Update AI module glow
        try:
            self.parent_win.chat_glow.setColor(QColor(theme_data["accent"]))
            self.parent_win.chat_glow.setBlurRadius(30 if selected == "cyberpunk" else 26)
        except Exception:
            pass



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setObjectName("MainWin")
        
        # Initialisation du fond technique
        self.bg = BackgroundGrid(self)
        self.bg.theme_color = QColor("#00d1ff")
        self.bg.lower() 
        
        self.setWindowTitle("Nexus Core")
        self.resize(1100, 700) 
        
        # Thème initial
        self.setProperty("theme", "arctic")
        
        self.collector = TelemetryCollector()


        self.nexus_ai = NexusAgent(api_key=load_key())
        self.session_mgr = SessionManager()
        
        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = Sidebar()
        main_layout.addWidget(self.sidebar)
        
        # Content Area (Right of Sidebar)
        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        self.header = Header()
        content_layout.addWidget(self.header)
        
        # Splitter for Stacked Content + Chat
        from PySide6.QtWidgets import QSplitter
        self.main_splitter = QSplitter(Qt.Horizontal)
        
        # STACKED VIEWS
        self.stack = QStackedWidget()
        
        # 1. Library View
        self.games_view = GamesView(self)
        self.stack.addWidget(self.games_view)
        
        # 2. Telemetry View
        self.telemetry_view = QWidget()
        tele_layout = QVBoxLayout(self.telemetry_view)
        tele_layout.setContentsMargins(40, 40, 40, 40)
        tele_layout.setSpacing(30)
        
        title_box = QHBoxLayout()
        title = QLabel("CORE_TELEMETRY")
        title.setObjectName("ViewTitle")
        status_badge = QLabel("  SYSTEM_STABLE  ")
        status_badge.setObjectName("HUDStatusLabel")
        title_box.addWidget(title)
        title_box.addSpacing(10)
        title_box.addWidget(status_badge)
        title_box.addStretch()
        tele_layout.addLayout(title_box)
        
        stats_grid = QGridLayout()
        stats_grid.setSpacing(20)
        self.card_cpu = StatCard("CPU_LOAD", "fa5s.microchip", "#00d1ff", "cpu")
        self.card_gpu = StatCard("GPU_LOAD", "fa5s.memory", "#00d1ff", "gpu")
        self.card_ram = StatCard("RAM_USAGE", "fa5s.bolt", "#00d1ff", "ram")
        self.card_disk = StatCard("SSD_ACTIVITY", "fa5s.hdd", "#00d1ff", "disk") 
        stats_grid.addWidget(self.card_cpu, 0, 0)
        stats_grid.addWidget(self.card_gpu, 0, 1)
        stats_grid.addWidget(self.card_ram, 1, 0)
        stats_grid.addWidget(self.card_disk, 1, 1)
        tele_layout.addLayout(stats_grid)
        
        thermal_lbl = QLabel("THERMAL_STATUS_MONITOR")
        thermal_lbl.setObjectName("HUDSmallLabel")
        tele_layout.addWidget(thermal_lbl)
        thermal_layout = QHBoxLayout()
        self.temp_cpu_card = ThermalCard("CPU_PACKAGE", 0.0)
        self.temp_gpu_card = ThermalCard("GPU_CORE", 0.0)
        thermal_layout.addWidget(self.temp_cpu_card)
        thermal_layout.addWidget(self.temp_gpu_card)
        tele_layout.addLayout(thermal_layout)
        tele_layout.addStretch()
        
        self.stack.addWidget(self.telemetry_view)
        
        # 3. Settings View
        self.settings_view = SettingsPanel(self)
        self.stack.addWidget(self.settings_view)
        
        self.main_splitter.addWidget(self.stack)
        
        # CHAT PANEL
        self.chat_panel = QFrame()
        self.chat_panel.setObjectName("ChatPanel")
        self.chat_panel.setFixedWidth(350)

        # Visible AI module glow (updated by theme)
        self.chat_glow = QGraphicsDropShadowEffect(self.chat_panel)
        self.chat_glow.setBlurRadius(28)
        self.chat_glow.setOffset(0, 0)
        self.chat_glow.setColor(QColor("#00d1ff"))
        self.chat_panel.setGraphicsEffect(self.chat_glow)

        chat_layout = QVBoxLayout(self.chat_panel)
        # AI MODULE HEADER
        ai_header = QFrame()
        ai_header.setObjectName("AIModuleHeader")
        ai_hbox = QHBoxLayout(ai_header)
        ai_hbox.setContentsMargins(12, 10, 12, 10)
        ai_hbox.setSpacing(10)

        ai_dot = QLabel("●")
        ai_dot.setObjectName("AIModuleDot")
        ai_title = QLabel("NEXUS AI MODULE")
        ai_title.setObjectName("AIModuleTitle")
        ai_state = QLabel("ONLINE")
        ai_state.setObjectName("AIModuleState")

        ai_hbox.addWidget(ai_dot)
        ai_hbox.addWidget(ai_title)
        ai_hbox.addStretch()
        ai_hbox.addWidget(ai_state)

        chat_layout.addWidget(ai_header)
        self.chat_history = QScrollArea()
        self.chat_history.setWidgetResizable(True)
        self.chat_history.setFrameShape(QFrame.NoFrame)
        self.chat_content = QWidget()
        self.chat_vbox = QVBoxLayout(self.chat_content)
        self.chat_vbox.addStretch() 
        self.chat_history.setWidget(self.chat_content)
        chat_layout.addWidget(self.chat_history)
        input_layout = QHBoxLayout()
        self.chat_input = QLineEdit()
        self.chat_input.setObjectName("ChatInput")
        self.chat_input.setPlaceholderText("ENTER_QUERY...")
        self.chat_input.returnPressed.connect(self.send_message)
        send_btn = QPushButton("SEND")
        send_btn.setObjectName("ActionBtn")
        send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(self.chat_input)
        input_layout.addWidget(send_btn)
        chat_layout.addLayout(input_layout)
        
        self.main_splitter.addWidget(self.chat_panel)
        content_layout.addWidget(self.main_splitter)
        main_layout.addWidget(content_area)
        
        # CONNECTIONS
        self.sidebar.btn_games.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.sidebar.btn_system.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        self.sidebar.btn_settings.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        
        # Timer for Telemetry + Clock
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_telemetry)
        self.timer.start(1000) 
        
        self.load_styles()

    def send_message(self):
        msg = self.chat_input.text().strip()
        if not msg: return
        lbl = QLabel(f"USER >> {msg}")
        lbl.setObjectName("ChatBubbleUser")
        lbl.setWordWrap(True)
        self.chat_vbox.addWidget(lbl)
        self.chat_input.clear()
        stats = self.collector.get_stats()
        response_text = self.nexus_ai.get_response(msg, hardware_stats=stats)
        self.add_ai_response(response_text)
        
    def add_ai_response(self, text):
        lbl = QLabel(f"NEXUS >> {text}")
        lbl.setObjectName("ChatBubbleAI")
        lbl.setWordWrap(True)
        self.chat_vbox.addWidget(lbl)
        self.chat_history.verticalScrollBar().setValue(self.chat_history.verticalScrollBar().maximum())

    def update_telemetry(self):
        # Clock Animation (Local Time)
        from datetime import datetime
        self.header.time_lbl.setText(f"LCL {datetime.now().strftime('%H:%M:%S')}")
        
        stats = self.collector.get_stats()
        
        # Check for game sessions
        is_gaming = self.session_mgr.check_running_games()
        session_id = self.session_mgr.get_current_session_id()
        
        # Update UI Cards
        self.card_cpu.update_data(f"{stats['cpu']}%", stats['cpu'])
        self.card_ram.update_data(f"{stats['ram']}%", stats['ram'])
        # ... GPU updates ...
        
        # Interval logic: Log more often if gaming
        log_interval = 2 if is_gaming else 15
        
        if hasattr(self, 'db_counter'):
            self.db_counter += 1
        else:
            self.db_counter = 0
            
        if self.db_counter >= log_interval:
            # On enregistre le snapshot AVEC l'id de session
            db_session = get_session()
            snapshot = HardwareSnapshot(
                cpu_usage=stats["cpu"],
                ram_usage=stats["ram"],
                gpu_usage=stats.get("gpu", 0),
                gpu_temp=stats.get("gpu_temp", 0),
                session_id=session_id
            )
            db_session.add(snapshot)
            db_session.commit()
            db_session.close()
            self.db_counter = 0

        # Update Thermals
        if stats.get('cpu_temp'):
            self.temp_cpu_card.update_temp(stats['cpu_temp'])
        if stats.get('gpu_temp'):
            self.temp_gpu_card.update_temp(stats['gpu_temp'])

    def resizeEvent(self, event):
        self.bg.setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(event)

    def load_styles(self):
        try:
            with open("app_ui/styles.qss", "r") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print("Styles not found")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

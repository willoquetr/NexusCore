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
from PySide6.QtCore import Qt, QSize, QTimer, QFileInfo, QThread, Signal, QPoint
from PySide6.QtGui import QIcon, QColor, QFontDatabase, QFont, QPainter, QPainterPath, QPen, QLinearGradient, QPixmap
import qtawesome as qta
from core.database import get_session, GameSession, HardwareSnapshot, CustomGame, Favorite
from core.telemetry.collector import TelemetryCollector
from core.ai.nexus_agent import NexusAgent, load_key
from core.telemetry.session_manager import SessionManager
from app_ui.optimization_view import OptimizationView

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class OptimizationWorker(QThread):
    finished = Signal(dict)
    
    def __init__(self, agent, title, config, hardware):
        super().__init__()
        self.agent = agent
        self.title = title
        self.config = config
        self.hardware = hardware
        
    def run(self):
        optimized = self.agent.generate_optimization_config(self.title, self.config, self.hardware)
        self.finished.emit(optimized if optimized else {})

class NavButton(QPushButton):
    """Bouton de navigation avec effet d'ombre dynamique au clic."""
    def __init__(self, text, icon_name, parent=None):
        super().__init__(text, parent)
        self.setObjectName("NavButton")
        self.setIcon(qta.icon(icon_name, color="#00d1ff"))
        self.setIconSize(QSize(24, 24))
        
        # Effet d'ombre initial (plus marqué pour ressortir)
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(4) 
        self.shadow.setOffset(4, 4) 
        self.shadow.setColor(QColor(0, 0, 0, 180)) # Noir 70%
        self.setGraphicsEffect(self.shadow)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # L'ombre se rapproche pour simuler l'enfoncement
            self.shadow.setOffset(1, 1)
            self.shadow.setBlurRadius(2)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            # L'ombre revient à la normale
            self.shadow.setOffset(4, 4)
            self.shadow.setBlurRadius(4)
        super().mouseReleaseEvent(event)

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
        btn = NavButton(text, icon_name)
        btn.setProperty("active", active)
        return btn

class Header(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Header")
        self.setFixedHeight(100) 
        self.parent_win = parent # Reference to MainWindow
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(40, 0, 10, 0) # Reduced right margin for window controls
        
        self.search_bar = QLineEdit()
        self.search_bar.setObjectName("SearchInput")
        self.search_bar.setPlaceholderText("QUERY DATABASE...") 
        self.search_bar.setFixedWidth(158)
        self.search_bar.setFixedHeight(50) 
        
        layout.addWidget(self.search_bar)
        layout.addStretch()
        
        # Info Group
        info_layout = QHBoxLayout()
        self.time_lbl = QLabel("LCL 00:00:00")
        self.time_lbl.setObjectName("HUDClock")
        self.user_info = QLabel("OPERATOR: ADMIN")
        self.user_info.setObjectName("HUDUser")
        info_layout.addWidget(self.time_lbl)
        info_layout.addSpacing(30)
        info_layout.addWidget(self.user_info)
        layout.addLayout(info_layout)
        
        layout.addSpacing(40)

        # WINDOW CONTROLS
        self.win_controls = QHBoxLayout()
        self.win_controls.setSpacing(5)
        
        self.btn_min = QPushButton()
        self.btn_min.setObjectName("WinBtn")
        self.btn_min.setIcon(qta.icon("fa5s.minus", color="#000000"))
        self.btn_min.clicked.connect(lambda: self.window().showMinimized())
        
        self.btn_max = QPushButton()
        self.btn_max.setObjectName("WinBtn")
        self.btn_max.setIcon(qta.icon("fa5s.square", color="#000000"))
        self.btn_max.clicked.connect(self.toggle_maximize)
        
        self.btn_close = QPushButton()
        self.btn_close.setObjectName("WinBtnClose")
        self.btn_close.setIcon(qta.icon("fa5s.times", color="#000000"))
        self.btn_close.clicked.connect(lambda: self.window().close())
        
        self.win_controls.addWidget(self.btn_min)
        self.win_controls.addWidget(self.btn_max)
        self.win_controls.addWidget(self.btn_close)
        
        # Align controls to the very top right
        controls_container = QVBoxLayout()
        controls_container.addLayout(self.win_controls)
        controls_container.addStretch()
        layout.addLayout(controls_container)

    def toggle_maximize(self):
        if self.window().isMaximized():
            self.window().showNormal()
            self.btn_max.setIcon(qta.icon("fa5s.square", color="#000000"))
        else:
            self.window().showMaximized()
            self.btn_max.setIcon(qta.icon("fa5s.clone", color="#000000"))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.window().frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            if self.window().isMaximized():
                # Calculer le ratio horizontal de la souris avant de réduire
                screen_width = self.window().width()
                mouse_x = event.globalPosition().toPoint().x()
                ratio = mouse_x / screen_width
                
                self.toggle_maximize() # Passe en mode normal
                
                # Ajuster la position pour que la souris reste au même endroit relatif
                new_width = self.window().width()
                new_x = mouse_x - int(new_width * ratio)
                self.window().move(new_x, event.globalPosition().toPoint().y() - 20)
                
                # Mettre à jour _drag_pos pour la suite du mouvement
                self._drag_pos = QPoint(int(new_width * ratio), 20)
                return

            self.window().move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
    
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.toggle_maximize()
            event.accept()

class GameCard(QFrame):

    def __init__(self, title, launcher, exe_path=None, parent_view=None, is_favorite=False):

        super().__init__(parent_view)

        self.setFixedSize(110, 145) # Juste un peu plus haut pour le badge

        self.setObjectName("GameIcon")
        self.is_favorite = is_favorite
        self.setProperty("hovered", False)
        self._hover_fx = QGraphicsDropShadowEffect(self)
        self._hover_fx.setBlurRadius(18)
        self._hover_fx.setOffset(0, 10)
        # color set in apply_theme via stylesheet (fallback here)
        self._hover_fx.setColor(QColor(0, 209, 255, 90))
        self.setGraphicsEffect(self._hover_fx)

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

        # Launcher badge (top-left)
        l_text = str(launcher).upper()
        self.launcher_badge = QLabel(l_text)
        self.launcher_badge.setObjectName("LauncherBadge")
        self.launcher_badge.setAlignment(Qt.AlignCenter)
        self.launcher_badge.setFixedHeight(18)
        if l_text == "LAUNCHER":
            self.launcher_badge.hide()

        # Favorite star
        self.fav_lbl = QLabel("★" if is_favorite else "")
        self.fav_lbl.setStyleSheet("color: #ffca28; font-size: 14px;")

        icon_layout = QVBoxLayout(self.icon_frame)
        icon_layout.setContentsMargins(0, 0, 0, 0)

        badge_row = QHBoxLayout()
        badge_row.setContentsMargins(5, 2, 5, 0)
        badge_row.addWidget(self.launcher_badge, alignment=Qt.AlignLeft | Qt.AlignTop)
        badge_row.addStretch()
        badge_row.addWidget(self.fav_lbl, alignment=Qt.AlignRight | Qt.AlignTop)
        icon_layout.addLayout(badge_row)

        # Icon holder
        self.icon_lbl = QLabel()
        self.icon_lbl.setAlignment(Qt.AlignCenter)

        # Map for launcher icons if EXE fails or to have a cleaner look
        launcher_brand_icons = {
            "STEAM": ("fa5b.steam", "#171a21"),
            "EPIC": ("si.epicgames", "#ffffff"),
            "DISCORD": ("fa5b.discord", "#5865F2"),
            "BATTLE.NET": ("fa5b.battle-net", "#009ae4"),
            "UBISOFT": ("si.ubisoft", "#ffffff"),
            "EA": ("fa5s.play", "#ff4747"),
            "RIOT": ("si.riotgames", "#d32936")
        }

        icon_set = False
        l_upper = str(launcher).upper()
        
        # Priority 1: High quality EXE icon
        if self.exe_path and os.path.exists(self.exe_path):
            try:
                file_info = QFileInfo(self.exe_path)
                icon = QFileIconProvider().icon(file_info)
                pix = icon.pixmap(256, 256) 
                if not pix.isNull():
                    self.icon_lbl.setPixmap(pix.scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                    icon_set = True
            except: pass

        # Priority 2: Brand Icon for launchers or fallback
        if not icon_set:
            if l_upper in launcher_brand_icons:
                icon_name, icon_color = launcher_brand_icons[l_upper]
                self.icon_lbl.setPixmap(qta.icon(icon_name, color=icon_color).pixmap(55, 55))
            else:
                self.icon_lbl.setPixmap(qta.icon("fa5s.gamepad", color="#00d1ff").pixmap(50, 50))

            

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

        # Optimize Action
        opt_action = menu.addAction(self.parent_view.parent_win.tr("ctx_optimize"))
        opt_action.setIcon(qta.icon("fa5s.magic", color="#00d1ff"))
        
        menu.addSeparator()

        fav_text = "RETIRER DES FAVORIS" if self.is_favorite else "AJOUTER AUX FAVORIS"
        fav_action = menu.addAction(fav_text)
        
        menu.addSeparator()
        delete_action = menu.addAction("RETIRER DU NEXUS")

        action = menu.exec(self.mapToGlobal(pos))

        if action == delete_action:
            self.parent_view.delete_game(self.title)
        elif action == fav_action:
            self.parent_view.toggle_favorite(self.title)
        elif action == opt_action:
            self.parent_view.parent_win.run_optimization(self.title)



    def enterEvent(self, event):
        self.setProperty("hovered", True)
        self.style().unpolish(self)
        self.style().polish(self)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setProperty("hovered", False)
        self.style().unpolish(self)
        self.style().polish(self)
        super().leaveEvent(event)

    def mousePressEvent(self, event):

        if event.button() == Qt.LeftButton:

            if self.exe_path and os.path.exists(self.exe_path):

                try: os.startfile(self.exe_path)

                except: pass

        super().mousePressEvent(event)



class ScanWorker(QThread):
    finished = Signal(list)

    def run(self):
        all_items = []
        seen_exes = set()
        seen_titles = set()
        logger.info("Library: Starting system-wide game scan...")
        
        def add_item(title, launcher, exe):
            title_norm = title.lower().strip()
            if not exe:
                if title_norm not in seen_titles:
                    all_items.append({"title": title, "launcher": launcher, "exe": None})
                    seen_titles.add(title_norm)
                return
            
            normalized_exe = os.path.normpath(exe).lower()
            if normalized_exe not in seen_exes:
                all_items.append({"title": title, "launcher": launcher, "exe": exe})
                seen_exes.add(normalized_exe)
                seen_titles.add(title_norm)

        try:
            # Launchers
            from plugins.scanner_launchers.scanner import scan_launchers
            launchers = scan_launchers()
            for l in launchers:
                add_item(l['title'], "Launcher", l['exe'])
            
            # Steam
            from plugins.scanner_steam.scanner import scan_steam_games
            for g in scan_steam_games():
                exe_p = None
                if os.path.exists(g['install_dir']):
                    for f in os.listdir(g['install_dir']):
                        if f.endswith(".exe") and not any(x in f.lower() for x in ["unity", "crash", "helper", "redist", "setup"]):
                            exe_p = os.path.join(g['install_dir'], f)
                            break
                add_item(g['title'], "Steam", exe_p)

            # Epic
            from plugins.scanner_epic import scan_epic_games
            for g in scan_epic_games():
                add_item(g['title'], "Epic", g['exe'])

            # Ubisoft
            try:
                from plugins.scanner_ubisoft import scan_ubisoft_games
                for g in scan_ubisoft_games():
                    add_item(g['title'], "Ubisoft", g['exe'])
            except: pass

            # EA
            try:
                from plugins.scanner_ea import scan_ea_games
                for g in scan_ea_games():
                    add_item(g['title'], "EA", g['exe'])
            except: pass

            # Battle.net
            try:
                from plugins.scanner_battlenet import scan_battlenet_games
                for g in scan_battlenet_games():
                    add_item(g['title'], "Battle.net", g['exe'])
            except: pass

            # Riot
            try:
                from plugins.scanner_riot import scan_riot_games
                for g in scan_riot_games():
                    add_item(g['title'], "Riot", g['exe'])
            except: pass

            # Custom
            db = get_session()
            custom_games = db.query(CustomGame).all()
            for g in custom_games:
                add_item(g.title, "Custom", g.exe_path)
            db.close()
            
            logger.info(f"Library: Scan complete. Deduplicated total: {len(all_items)}")
            
        except Exception as e:
            logger.error(f"Library: Fatal error during scan: {e}", exc_info=True)
            
        self.finished.emit(all_items)

class AIWorker(QThread):
    response_ready = Signal(str)

    def __init__(self, agent, user_input, hardware_stats, is_gaming):
        super().__init__()
        self.agent = agent
        self.user_input = user_input
        self.stats = hardware_stats
        self.is_gaming = is_gaming

    def run(self):
        response = self.agent.get_response(self.user_input, hardware_stats=self.stats, is_gaming=self.is_gaming)
        self.response_ready.emit(response)

class TelemetryWorker(QThread):
    stats_ready = Signal(dict, bool) # sends stats and is_gaming status

    def __init__(self, collector, session_mgr):
        super().__init__()
        self.collector = collector
        self.session_mgr = session_mgr
        self.running = True
        self.db_counter = 0

    def run(self):
        logger.info("TelemetryWorker: Background thread started.")
        while self.running:
            try:
                # 1. Collect Stats (every 1s)
                stats = self.collector.get_stats()
                
                # 2. Check for gaming (Every 5s)
                if self.db_counter % 5 == 0:
                    is_gaming = self.session_mgr.check_running_games()
                else:
                    is_gaming = self.session_mgr.current_session is not None
                
                # 3. Send to UI
                self.stats_ready.emit(stats, is_gaming)
                
                # 4. Database Writing
                session_id = self.session_mgr.get_current_session_id()
                log_interval = 2 if is_gaming else 15
                
                if self.db_counter % log_interval == 0:
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
                
                self.db_counter += 1
                if self.db_counter > 1000: self.db_counter = 0
                
            except Exception as e:
                logger.error(f"TelemetryWorker Error: {e}")
            
            self.msleep(1000)

    def stop(self):
        self.running = False

class GamesView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_win = parent
        self.full_games_list = [] # Cache for filtering
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        header_box = QHBoxLayout()
        title_vbox = QVBoxLayout()
        self.title = QLabel("NEXUS LIBRARY")
        self.title.setObjectName("ViewTitle")
        self.subtitle = QLabel("Exploration des environnements virtuels détectés")
        self.subtitle.setObjectName("ViewSubtitle")
        title_vbox.addWidget(self.title)
        title_vbox.addWidget(self.subtitle)
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

        # Library actions
        self.add_btn.clicked.connect(self.add_custom_game)
        self.scan_btn.clicked.connect(self.refresh_games)

        # Active launcher filter
        self.active_launcher = "TOUS"
        
        # Launcher Filter Bar (Divided into 2 rows to avoid horizontal stretching)
        self.filter_buttons = {}
        launchers_row1 = ["TOUS", "FAVORIS", "STEAM", "EPIC"]
        launchers_row2 = ["UBISOFT", "EA", "BATTLE.NET", "RIOT", "CUSTOM"]
        
        filter_layout = QVBoxLayout()
        filter_layout.setSpacing(8)
        
        row1 = QHBoxLayout()
        row1.setSpacing(10)
        for l in launchers_row1:
            btn = QPushButton(l)
            btn.setObjectName("FilterButton")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, launcher=l: self.set_launcher_filter(launcher))
            row1.addWidget(btn)
            self.filter_buttons[l] = btn
        row1.addStretch()
        
        row2 = QHBoxLayout()
        row2.setSpacing(10)
        for l in launchers_row2:
            btn = QPushButton(l)
            btn.setObjectName("FilterButton")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, launcher=l: self.set_launcher_filter(launcher))
            row2.addWidget(btn)
            self.filter_buttons[l] = btn
        row2.addStretch()
        
        filter_layout.addLayout(row1)
        filter_layout.addLayout(row2)
        
        self.filter_buttons["TOUS"].setChecked(True)
        layout.addLayout(filter_layout)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.content_widget = QWidget()
        self.grid = QGridLayout(self.content_widget)
        self.grid.setSpacing(25)
        self.grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        scroll.setWidget(self.content_widget)
        layout.addWidget(scroll)

        self.scan_thread = None
        self.refresh_games()

    def set_launcher_filter(self, launcher):
        self.active_launcher = launcher
        for name, btn in self.filter_buttons.items():
            btn.setChecked(name == launcher)
        self.update_display() # No full scan here

    def update_display(self):
        """Updates the grid based on cached list and filter."""
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        flt = self.active_launcher
        
        # Récupérer les favoris depuis la DB
        db = get_session()
        fav_titles = [f.game_title for f in db.query(Favorite).all()]
        db.close()

        if flt == "TOUS":
            filtered = self.full_games_list
        elif flt == "FAVORIS":
            filtered = [it for it in self.full_games_list if it["title"] in fav_titles]
        else:
            filtered = [it for it in self.full_games_list if it.get("launcher", "").upper() == flt]

        # CALCUL DYNAMIQUE DES COLONNES
        available_width = self.width() - 260 - 300 # Fenêtre - Sidebar - Chat approx
        cols = max(1, available_width // 135) # 110px card + 25px spacing

        for i, item in enumerate(filtered):
            is_fav = item["title"] in fav_titles
            card = GameCard(item["title"], item["launcher"], exe_path=item.get("exe"), parent_view=self, is_favorite=is_fav)
            self.grid.addWidget(card, i // cols, i % cols) 
        
        self.count_lbl.setText(f"{len(filtered)} ELEMENTS")

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
        if self.scan_thread and self.scan_thread.isRunning():
            return

        self.count_lbl.setText("SCANNING...")
        self.scan_btn.setEnabled(False)
        
        self.scan_thread = ScanWorker()
        self.scan_thread.finished.connect(self.on_scan_finished)
        self.scan_thread.start()

    def on_scan_finished(self, all_items):
        self.scan_btn.setEnabled(True)
        self.full_games_list = all_items
        self.parent_win.session_mgr.update_games_list(all_items)
        self.update_display()

    def toggle_favorite(self, title):
        db = get_session()
        fav = db.query(Favorite).filter(Favorite.game_title == title).first()
        if fav:
            db.delete(fav)
            logger.info(f"Library: Removed {title} from favorites.")
        else:
            new_fav = Favorite(game_title=title)
            db.add(new_fav)
            logger.info(f"Library: Added {title} to favorites.")
        db.commit()
        db.close()
        self.update_display()

    def delete_game(self, title):
        db = get_session()
        game = db.query(CustomGame).filter(CustomGame.title == title).first()
        if game:
            db.delete(game)
            db.commit()
            logger.info(f"Custom game {title} deleted.")
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
        # If we have an object name, we might want to let QSS handle the styling (PNG textures)
        if self.objectName() in ["StatCard", "ThermalCard"]:
            return super().paintEvent(event)

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
        self.setObjectName("StatCard")
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
        self.setObjectName("ThermalCard")
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
    """Futuristic layered background driven by images and theme tokens."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme_name = "arctic"
        self.theme_color = QColor("#00d1ff")
        self.base_pixmap = None
        self.hud_pixmap = None
        self.noise_pixmap = None
        self.mask_path = None # Will be set by parent resizeEvent
        self.load_assets()

    def load_assets(self):
        # Layer 1: Base (100% opacity)
        base_p = resource_path("assets/backgroundmain.png")
        if os.path.exists(base_p):
            self.base_pixmap = QPixmap(base_p)
        
        # Layer 2: HUD Overlay (~40% opacity)
        hud_p = resource_path("assets/background2.png")
        if os.path.exists(hud_p):
            self.hud_pixmap = QPixmap(hud_p)
            
        # Layer 3: Noise / Grid (~6% opacity)
        noise_p = resource_path("assets/background3.png")
        if os.path.exists(noise_p):
            self.noise_pixmap = QPixmap(noise_p)

    def set_theme(self, theme_name: str, accent_hex: str, base_bg: QColor):
        self.theme_name = theme_name
        self.theme_color = QColor(accent_hex)
        # We could potentially swap base_pixmap here if themes have different bases
        # but following conseildegpt.txt, we focus on the 3-layer structure.
        self.update()

    def paintEvent(self, event):
        w, h = self.width(), self.height()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        painter.setRenderHint(QPainter.Antialiasing)

        # Apply Rounded Mask if available
        if self.mask_path:
            painter.setClipPath(self.mask_path)
        else:
            # Fallback default rounding
            path = QPainterPath()
            path.addRoundedRect(0, 0, w, h, 15, 15)
            painter.setClipPath(path)

        # --- Layer 1: Background BASE (100% opacity) ---
        if self.base_pixmap and not self.base_pixmap.isNull():
            painter.setOpacity(1.0)
            painter.drawPixmap(self.rect(), self.base_pixmap.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
        else:
            # Fallback gradient
            grad = QLinearGradient(0, 0, w, h)
            grad.setColorAt(0, QColor(255, 255, 255)); grad.setColorAt(1, QColor(226, 244, 255))
            painter.fillRect(self.rect(), grad)

        # --- Layer 2: HUD Overlay (~20% opacity) ---
        if self.hud_pixmap and not self.hud_pixmap.isNull():
            painter.setOpacity(0.40)
            painter.drawPixmap(self.rect(), self.hud_pixmap.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
        else:
            # Fallback HUD lines if image is missing
            painter.setOpacity(0.15)
            painter.setPen(QPen(self.theme_color, 2))
            painter.drawLine(0, 120, 120, 0)
            painter.drawLine(w-120, 0, w, 120)
            painter.drawLine(0, h-120, 120, h)
            painter.drawLine(w-120, h, w, h-120)

        # --- Layer 3: Noise / Grid (~6% opacity) ---
        # "MUST BE REPEAT, NEVER STRETCH"
        if self.noise_pixmap and not self.noise_pixmap.isNull():
            painter.setOpacity(0.06)
            # Tiling logic
            painter.drawTiledPixmap(self.rect(), self.noise_pixmap)
        else:
            # Fallback dots
            painter.setOpacity(0.05)
            dot_gap = 40
            for x in range(0, w, dot_gap):
                for y in range(0, h, dot_gap):
                    painter.drawPoint(x, y)
        
        # Border stroke to clean edges
        painter.setClipping(False) # Disable clipping to draw the border ON TOP
        painter.setPen(QPen(QColor(100, 100, 100, 50), 1))
        if self.mask_path:
            painter.drawPath(self.mask_path)
            
        painter.end()

class SettingsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_win = parent
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll Area for Settings
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setSpacing(20)

        self.title = QLabel("CORE_CONFIGURATION")
        self.title.setObjectName("ViewTitle")
        layout.addWidget(self.title)

        # AI Section
        ai_box = QFrame()
        ai_box.setObjectName("SettingsCard")
        ai_layout = QVBoxLayout(ai_box)
        ai_layout.setContentsMargins(25, 25, 25, 25)

        self.ai_title = QLabel("ARTIFICIAL_INTELLIGENCE_LINK")
        self.ai_title.setObjectName("HUDSmallLabel")
        ai_layout.addWidget(self.ai_title)

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

        self.save_ai_btn = QPushButton("UPDATE_AI_CORE")
        self.save_ai_btn.setObjectName("ScanBtn")
        self.save_ai_btn.setFixedHeight(45)
        self.save_ai_btn.clicked.connect(self.save_ai_settings)
        ai_layout.addWidget(self.save_ai_btn)
        layout.addWidget(ai_box)

        # Theme Section
        theme_box = QFrame()
        theme_box.setObjectName("SettingsCard")
        theme_layout = QVBoxLayout(theme_box)
        theme_layout.setContentsMargins(25, 25, 25, 25)
        self.theme_title = QLabel("VISUAL_INTERFACE_SKIN")
        self.theme_title.setObjectName("HUDSmallLabel")
        theme_layout.addWidget(self.theme_title)

        self.theme_selector = QComboBox()
        self.theme_selector.addItems(["Arctic White", "Deep Dark", "Cyberpunk", "Girly Rose"])
        self.theme_selector.setFixedHeight(45)
        theme_layout.addWidget(QLabel("SELECT_SKIN:"))
        theme_layout.addWidget(self.theme_selector)

        theme_layout.addSpacing(10)
        self.lang_lbl = QLabel("SELECT LANGUAGE:")
        theme_layout.addWidget(self.lang_lbl)
        self.lang_selector = QComboBox()
        self.lang_selector.addItems(["English", "Français"])
        self.lang_selector.setFixedHeight(45)
        self.lang_selector.currentIndexChanged.connect(self.on_lang_changed)
        theme_layout.addWidget(self.lang_selector)

        self.apply_theme_btn = QPushButton("APPLY_SKIN")
        self.apply_theme_btn.setObjectName("ActionBtn")
        self.apply_theme_btn.setFixedHeight(45)
        self.apply_theme_btn.clicked.connect(self.apply_theme)
        theme_layout.addWidget(self.apply_theme_btn)
        layout.addWidget(theme_box)

        layout.addStretch()
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def on_lang_changed(self, index):
        code = "en" if index == 0 else "fr"
        self.parent_win.change_language(code)

    def retranslate(self):
        self.title.setText(self.parent_win.tr("settings_title"))
        self.ai_title.setText(self.parent_win.tr("settings_ai_title"))
        self.theme_title.setText(self.parent_win.tr("settings_skin_title"))
        self.save_ai_btn.setText(self.parent_win.tr("btn_update_ai"))
        self.apply_theme_btn.setText(self.parent_win.tr("btn_apply_skin"))
        self.lang_lbl.setText(self.parent_win.tr("lang_selector"))

    def save_ai_settings(self):
        key = self.api_key_input.text().strip()
        provider = self.ai_provider.currentText()
        if key:
            self.parent_win.save_config("api_key", key)
            self.parent_win.save_config("provider", provider)
            self.parent_win.nexus_ai.setup_model(key)

    def apply_theme(self):
        theme_map = {"Arctic White": "arctic", "Deep Dark": "dark", "Cyberpunk": "cyberpunk", "Girly Rose": "girly"}
        selected = theme_map.get(self.theme_selector.currentText(), "arctic")
        self.parent_win.save_config("theme", selected)
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
        try:
            self.parent_win.chat_glow.setColor(QColor(theme_data["accent"]))
            self.parent_win.chat_glow.setBlurRadius(30 if selected == "cyberpunk" else 26)
        except Exception: pass




class SideGrip(QWidget):
    def __init__(self, parent, edge):
        super().__init__(parent)
        self.edge = edge
        self.setMouseTracking(True)
        if edge == Qt.LeftEdge:
            self.setCursor(Qt.SizeHorCursor)
        elif edge == Qt.RightEdge:
            self.setCursor(Qt.SizeHorCursor)
        elif edge == Qt.TopEdge:
            self.setCursor(Qt.SizeVerCursor)
        elif edge == Qt.BottomEdge:
            self.setCursor(Qt.SizeVerCursor)
        elif edge == Qt.TopLeftCorner or edge == Qt.BottomRightCorner:
            self.setCursor(Qt.SizeFDiagCursor)
        elif edge == Qt.TopRightCorner or edge == Qt.BottomLeftCorner:
            self.setCursor(Qt.SizeBDiagCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.mousePos = event.globalPosition().toPoint()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            delta = event.globalPosition().toPoint() - self.mousePos
            if self.edge == Qt.LeftEdge:
                new_w = self.window().width() - delta.x()
                if new_w > self.window().minimumWidth():
                    self.window().setGeometry(self.window().x() + delta.x(), self.window().y(), new_w, self.window().height())
            elif self.edge == Qt.RightEdge:
                self.window().resize(self.window().width() + delta.x(), self.window().height())
                self.mousePos = event.globalPosition().toPoint()
            elif self.edge == Qt.TopEdge:
                new_h = self.window().height() - delta.y()
                if new_h > self.window().minimumHeight():
                    self.window().setGeometry(self.window().x(), self.window().y() + delta.y(), self.window().width(), new_h)
            elif self.edge == Qt.BottomEdge:
                self.window().resize(self.window().width(), self.window().height() + delta.y())
                self.mousePos = event.globalPosition().toPoint()
            # Corner logic simplified for brevity (can be expanded)
            elif self.edge == Qt.BottomRightCorner:
                self.window().resize(self.window().width() + delta.x(), self.window().height() + delta.y())
                self.mousePos = event.globalPosition().toPoint()
            
            event.accept()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setObjectName("MainWin")
        
        # Frameless Window
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Initialisation Langues
        self.current_lang = "en"
        self.translations = {}
        self.load_languages()
        
        # Initialisation du fond technique
        self.bg = BackgroundGrid(self)
        self.bg.theme_color = QColor("#00d1ff")
        self.bg.lower() 
        
        self.setWindowTitle("Nexus Core")
        self.resize(1024, 700) # Taille sûre pour écran 1366px
        self.setMinimumSize(800, 600)
            
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
        self.tele_title_lbl = QLabel("CORE_TELEMETRY")
        self.tele_title_lbl.setObjectName("ViewTitle")
        self.tele_status_lbl = QLabel("  SYSTEM_STABLE  ")
        self.tele_status_lbl.setObjectName("HUDStatusLabel")
        title_box.addWidget(self.tele_title_lbl)
        title_box.addSpacing(10)
        title_box.addWidget(self.tele_status_lbl)
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
        
        self.thermal_monitor_lbl = QLabel("THERMAL_STATUS_MONITOR")
        self.thermal_monitor_lbl.setObjectName("HUDSmallLabel")
        tele_layout.addWidget(self.thermal_monitor_lbl)
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
        self.chat_panel.setMinimumWidth(250) # Minimum au lieu de Fixed
        self.chat_panel.setMaximumWidth(400) # Maximum pour garder le look

        # Visible AI module glow (updated by theme)
        self.chat_glow = QGraphicsDropShadowEffect(self.chat_panel)
        self.chat_glow.setBlurRadius(28)
        self.chat_glow.setOffset(0, 0)
        self.chat_glow.setColor(QColor("#00d1ff"))
        self.chat_panel.setGraphicsEffect(self.chat_glow)

        chat_layout = QVBoxLayout(self.chat_panel)
        chat_layout.setContentsMargins(15, 30, 15, 20) # Augmenté la marge haute (20 -> 30)
        
        # AI MODULE HEADER
        ai_header = QFrame()
        ai_header.setObjectName("AIModuleHeader")
        ai_header.setFixedHeight(50) # Réduit un peu pour plus de contrôle
        ai_hbox = QHBoxLayout(ai_header)
        ai_hbox.setContentsMargins(20, 5, 20, 10) # Plus de marge à gauche/droite pour le point
        ai_hbox.setSpacing(12)

        ai_dot = QLabel("●")
        ai_dot.setObjectName("AIModuleDot")
        ai_title = QLabel("NEXUS IA")
        ai_title.setObjectName("AIModuleTitle")
        ai_state = QLabel("ON")
        ai_state.setObjectName("AIModuleState")

        ai_hbox.addWidget(ai_dot, alignment=Qt.AlignVCenter) # Centré verticalement
        ai_hbox.addWidget(ai_title, alignment=Qt.AlignVCenter)
        ai_hbox.addStretch()
        ai_hbox.addWidget(ai_state, alignment=Qt.AlignVCenter)

        chat_layout.addWidget(ai_header)
        
        self.chat_history = QScrollArea()
        self.chat_history.setWidgetResizable(True)
        self.chat_history.setFrameShape(QFrame.NoFrame)
        self.chat_history.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff) # Force vertical only
        self.chat_history.setStyleSheet("background: transparent;")
        
        self.chat_content = QWidget()
        self.chat_content.setStyleSheet("background: transparent;")
        self.chat_vbox = QVBoxLayout(self.chat_content)
        self.chat_vbox.addStretch() 
        self.chat_history.setWidget(self.chat_content)
        chat_layout.addWidget(self.chat_history)
        
        # CHAT INPUT AREA - Full Width Texture
        self.input_container = QFrame()
        self.input_container.setObjectName("ChatInputContainer")
        self.input_container.setFixedHeight(50)
        input_box_layout = QHBoxLayout(self.input_container)
        input_box_layout.setContentsMargins(15, 0, 15, 0)
        
        self.chat_input = QLineEdit()
        self.chat_input.setObjectName("ChatInput")
        self.chat_input.setPlaceholderText("QUERY...")
        self.chat_input.setFrame(False)
        self.chat_input.returnPressed.connect(self.send_message)
        
        self.chat_send_btn = QPushButton("SEND")
        self.chat_send_btn.setObjectName("ChatSendBtn")
        self.chat_send_btn.setFixedWidth(60)
        self.chat_send_btn.clicked.connect(self.send_message)
        
        input_box_layout.addWidget(self.chat_input)
        input_box_layout.addWidget(self.chat_send_btn)
        chat_layout.addWidget(self.input_container)
        
        self.main_splitter.addWidget(self.chat_panel)
        content_layout.addWidget(self.main_splitter)
        main_layout.addWidget(content_area)
        
        # CONNECTIONS
        self.sidebar.btn_games.clicked.connect(lambda: self.switch_tab(0))
        self.sidebar.btn_system.clicked.connect(lambda: self.switch_tab(1))
        self.sidebar.btn_settings.clicked.connect(lambda: self.switch_tab(2))
        
        # Timer for Clock ONLY (Telemetry moved to Worker)
        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000) 
        
        # Start Telemetry Worker
        self.tele_worker = TelemetryWorker(self.collector, self.session_mgr)
        self.tele_worker.stats_ready.connect(self.update_telemetry_ui)
        self.tele_worker.start()
        
        self.load_styles()
        self.retranslate_ui() # Apply initial language
        
        # FINAL SETUP: Grips for resizing (Ensures they are on top of everything)
        self.grips = []
        for edge in [Qt.LeftEdge, Qt.RightEdge, Qt.TopEdge, Qt.BottomEdge, Qt.BottomRightCorner]:
            grip = SideGrip(self, edge)
            self.grips.append(grip)
            grip.show()
            grip.raise_()
            
        logger.info(f"UI Initialized: {self.width()}x{self.height()} | Theme: arctic | Lang: {self.current_lang}")

    def update_clock(self):
        from datetime import datetime
        self.header.time_lbl.setText(f"LCL {datetime.now().strftime('%H:%M:%S')}")

    def switch_tab(self, index):
        logger.info(f"UI: Switching to tab index {index}")
        self.stack.setCurrentIndex(index)
        # Update buttons visual state
        buttons = [self.sidebar.btn_games, self.sidebar.btn_system, self.sidebar.btn_settings]
        for i, btn in enumerate(buttons):
            active_state = (i == index)
            btn.setProperty("active", active_state)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def send_message(self):
        msg = self.chat_input.text().strip()
        if not msg: return
        
        # Display user message immediately
        lbl = QLabel(f"USER >> {msg}")
        lbl.setObjectName("ChatBubbleUser")
        lbl.setWordWrap(True)
        self.chat_vbox.addWidget(lbl)
        self.chat_input.clear()
        
        # Visual feedback: NEXUS is thinking
        self.ai_thinking_lbl = QLabel("NEXUS >> ...")
        self.ai_thinking_lbl.setObjectName("ChatBubbleAI")
        self.chat_vbox.addWidget(self.ai_thinking_lbl)
        
        # Start background task
        stats = self.collector.get_stats()
        is_gaming = self.session_mgr.check_running_games()
        self.ai_thread = AIWorker(self.nexus_ai, msg, stats, is_gaming)
        self.ai_thread.response_ready.connect(self.on_ai_response)
        self.ai_thread.start()
        
    def on_ai_response(self, response_text):
        # Update the placeholder with actual response
        if hasattr(self, 'ai_thinking_lbl'):
            self.ai_thinking_lbl.setText(f"NEXUS >> {response_text}")
            self.ai_thinking_lbl.setWordWrap(True) # Ensure it wraps after text change
        
        # Scroll to bottom
        self.chat_history.verticalScrollBar().setValue(self.chat_history.verticalScrollBar().maximum())

    def update_telemetry_ui(self, stats, is_gaming):
        # Update UI Cards
        self.card_cpu.update_data(f"{stats['cpu']}%", stats['cpu'])
        self.card_ram.update_data(f"{stats['ram']}%", stats['ram'])
        
        # Update GPU if data available
        if stats.get('gpu'):
            self.card_gpu.update_data(f"{stats['gpu']}%", stats['gpu'])

        # Update Thermals
        if stats.get('cpu_temp'):
            self.temp_cpu_card.update_temp(stats['cpu_temp'])
        if stats.get('gpu_temp'):
            self.temp_gpu_card.update_temp(stats['gpu_temp'])

    def resizeEvent(self, event):
        self.bg.setGeometry(0, 0, self.width(), self.height())
        
        # Update Grips Positions and force them on top
        if hasattr(self, 'grips') and len(self.grips) >= 5:
            rect = self.rect()
            grip_size = 8 # Slightly thinner for aesthetics
            
            # Index matching: Left, Right, Top, Bottom, BR Corner
            self.grips[0].setGeometry(0, grip_size, grip_size, rect.height() - 2*grip_size)
            self.grips[1].setGeometry(rect.width() - grip_size, grip_size, grip_size, rect.height() - 2*grip_size)
            self.grips[2].setGeometry(grip_size, 0, rect.width() - 2*grip_size, grip_size)
            self.grips[3].setGeometry(grip_size, rect.height() - grip_size, rect.width() - 2*grip_size, grip_size)
            self.grips[4].setGeometry(rect.width() - grip_size, rect.height() - grip_size, grip_size, grip_size)
            
            for g in self.grips:
                g.raise_()
        
        # Apply Rounded Mask to Background
        path = QPainterPath()
        path.addRoundedRect(self.rect(), 15, 15)
        self.bg.mask_path = path
        
        # Mettre à jour la grille de jeux si on est sur l'onglet bibliothèque
        if hasattr(self, 'stack') and self.stack.currentIndex() == 0:
            self.games_view.update_display()
        super().resizeEvent(event)

    def load_styles(self):
        # Load custom font
        font_path = resource_path("assets/Orbitron-Bold.ttf")
        if os.path.exists(font_path):
            font_id = QFontDatabase.addApplicationFont(font_path)
            if font_id != -1:
                family = QFontDatabase.applicationFontFamilies(font_id)[0]
                logger.info(f"UI: Loaded custom font -> {family}")
        
        try:
            qss_path = resource_path("app_ui/styles.qss")
            with open(qss_path, "r") as f:
                style_content = f.read()
            
            # Correction dynamique des chemins pour l'EXE
            # On remplace url("assets/ par le chemin absolu (avec des slashs compatibles CSS)
            base_assets_path = resource_path("assets").replace("\\", "/")
            style_content = style_content.replace('url("assets/', f'url("{base_assets_path}/')
            
            self.setStyleSheet(style_content)
            logger.info("UI: Stylesheet applied with dynamic asset paths.")
        except FileNotFoundError:
            logger.error("UI: Stylesheet not found.")

    def load_languages(self):
        # 1. Trouver le chemin racine (DEHORS) pour la config modifiable
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
        data_dir = os.path.join(base_dir, "data")
        os.makedirs(data_dir, exist_ok=True)
        
        # 2. Charger la config globale (DEHORS)
        self.config_path = os.path.join(data_dir, "config.json")
        user_config = {}
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    user_config = json.load(f)
                    self.current_lang = user_config.get("language", "en")
            except: pass

        # 3. Charger les dictionnaires (DEDANS l'EXE)
        try:
            lang_path = resource_path("data/languages.json")
            if os.path.exists(lang_path):
                with open(lang_path, "r", encoding="utf-8") as f:
                    self.translations = json.load(f)
                    logger.info(f"Languages: Loaded successfully from internal {lang_path}")
            else:
                logger.error(f"Languages: Internal file not found at {lang_path}")
                self.translations = {"en": {}, "fr": {}}
        except Exception as e:
            logger.error(f"Languages: Error loading: {e}")
            self.translations = {"en": {}, "fr": {}}

    def save_config(self, key=None, value=None):
        """Sauvegarde un paramètre dans config.json."""
        config = {}
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    config = json.load(f)
            except: pass
        
        if key and value:
            config[key] = value
            
        try:
            with open(self.config_path, "w") as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            logger.error(f"Config: Error saving: {e}")

    def tr(self, key):
        """Récupère la traduction pour la clé donnée."""
        if not self.translations:
            return key
        return self.translations.get(self.current_lang, {}).get(key, key)

    def change_language(self, lang_code):
        logger.info(f"UI: Language changed to {lang_code}")
        self.current_lang = lang_code
        self.save_config("language", lang_code) # Sauvegarde persistante
        self.retranslate_ui()

    def retranslate_ui(self):
        # Navigation (Sidebar)
        self.sidebar.btn_games.setText(self.tr("nav_library"))
        self.sidebar.btn_system.setText(self.tr("nav_system"))
        self.sidebar.btn_settings.setText(self.tr("nav_settings"))
        self.sidebar.st_title.setText(self.tr("status_title"))
        self.sidebar.st_val.setText(self.tr("status_val"))
        self.sidebar.btn_exit.setText(self.tr("btn_exit"))
        
        # Header
        self.header.search_bar.setPlaceholderText(self.tr("search_placeholder"))
        self.header.user_info.setText(self.tr("operator"))
        
        # Library
        self.games_view.title.setText(self.tr("view_lib_title"))
        self.games_view.subtitle.setText(self.tr("view_lib_sub"))
        self.games_view.scan_btn.setText(self.tr("btn_scan"))
        self.games_view.add_btn.setText(self.tr("btn_custom"))
        
        # Chat
        self.chat_input.setPlaceholderText(self.tr("chat_placeholder"))
        self.chat_send_btn.setText(self.tr("btn_send"))
        
        # Telemetry
        self.tele_title_lbl.setText(self.tr("tele_title"))
        self.tele_status_lbl.setText(self.tr("tele_status"))
        self.thermal_monitor_lbl.setText(self.tr("thermal_title"))
        
        # Settings
        self.settings_view.retranslate()

    def run_optimization(self, game_title):
        logger.info(f"Optimization: Starting analysis for {game_title}")
        
        # 1. Open Window Immediately (Loading State)
        self.opt_view = OptimizationView(self, game_title)
        self.opt_view.show()
        
        # 2. Get Hardware & Config (Async simulation for UI fluidity)
        hardware = self.collector.get_stats()
        current_config = self.nexus_ai.config_reader.get_settings(game_title)
        
        if not current_config:
            # Fallback for demo
            current_config = {"Resolution": "1920x1080", "VSync": "On", "Shadows": "High", "TextureQuality": "Ultra"}
            
        # 3. Start AI Worker
        self.opt_worker = OptimizationWorker(self.nexus_ai, game_title, current_config, hardware)
        self.opt_worker.finished.connect(lambda opt_conf: self.show_optimization_result(current_config, opt_conf))
        self.opt_worker.start()

    def show_optimization_result(self, current, optimized):
        if not optimized:
            optimized = current.copy()
            optimized["AI_STATUS"] = "FAILED_TO_GENERATE"
            
        if hasattr(self, 'opt_view') and self.opt_view.isVisible():
            self.opt_view.set_data(current, optimized)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QTimer, QRect, QSize, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont, QFontDatabase, QLinearGradient, QPen, QPainterPath
import os
import sys

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class NexusSplash(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(0.0) 
        
        # Dimensions
        self.setFixedSize(600, 400)
        
        # Animation state
        self.anim_tick = 0
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.update_animation)
        self.refresh_timer.start(16) # ~60 FPS
        
        # Assets Loading
        self.base_bg = QPixmap(resource_path("assets/backgroundmain.png"))
        self.hud_bg = QPixmap(resource_path("assets/background2.png"))
        self.noise_bg = QPixmap(resource_path("assets/background3.png"))
        self.logo = QPixmap(resource_path("assets/logonexuscore.png"))
        
        # Font Loading
        font_path = resource_path("assets/Orbitron-Bold.ttf")
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id != -1:
            family = QFontDatabase.applicationFontFamilies(font_id)[0]
            self.title_font = QFont(family, 28, QFont.Bold)
            self.status_font = QFont(family, 8)
        else:
            self.title_font = QFont("Arial", 28, QFont.Bold)
            self.status_font = QFont("Arial", 8)
            
        self.progress = 0.0
        self.current_status = "INITIALIZING..."
        self.theme_color = QColor("#00d1ff")

    def update_animation(self):
        self.anim_tick += 1
        self.update() # Triggers repaint for animation

    def fade_in(self):
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(800)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.anim.start()

    def fade_out(self, callback):
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(800)
        self.anim.setStartValue(1.0)
        self.anim.setEndValue(0.0)
        self.anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.anim.finished.connect(callback)
        self.anim.start()
        
    def update_progress(self, percent, message):
        self.progress = percent / 100.0
        self.current_status = message.upper()
        # On ne force pas le repaint ici, le timer s'en occupe
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        w, h = self.width(), self.height()
        
        # --- 1. Background Composition ---
        path = QPainterPath()
        path.addRoundedRect(0, 0, w, h, 15, 15)
        painter.setClipPath(path)
        
        painter.fillRect(self.rect(), QColor(10, 10, 15))
        
        if not self.base_bg.isNull():
            painter.setOpacity(0.3)
            painter.drawPixmap(self.rect(), self.base_bg.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
            
        if not self.hud_bg.isNull():
            painter.setOpacity(0.8) 
            painter.drawPixmap(self.rect(), self.hud_bg.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
            
        if not self.noise_bg.isNull():
            painter.setOpacity(0.1)
            painter.drawTiledPixmap(self.rect(), self.noise_bg)
            
        painter.setOpacity(1.0)
        painter.setPen(QPen(QColor(40, 40, 60), 2))
        painter.drawRoundedRect(1, 1, w-2, h-2, 15, 15)
        
        # --- 2. Logo (Centered Exactly) ---
        logo_size = 280
        if not self.logo.isNull():
            scaled_logo = self.logo.scaled(logo_size, logo_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            lx = (w - scaled_logo.width()) // 2
            ly = (h - scaled_logo.height()) // 2 - 20 
            painter.drawPixmap(lx, ly, scaled_logo)
            
            # --- ANIMATION: SCAN LINE ---
            scan_y = ly + (self.anim_tick % 150) * (logo_size / 150)
            grad = QLinearGradient(lx, scan_y, lx + logo_size, scan_y)
            grad.setColorAt(0, QColor(0, 209, 255, 0))
            grad.setColorAt(0.5, QColor(0, 209, 255, 150))
            grad.setColorAt(1, QColor(0, 209, 255, 0))
            painter.setPen(QPen(grad, 2))
            painter.drawLine(lx + 10, scan_y, lx + logo_size - 10, scan_y)
            
        # --- 3. "GAMING HUB" Text Fill Effect ---
        text = "GAMING HUB"
        painter.setFont(self.title_font)
        text_rect = painter.fontMetrics().boundingRect(text)
        text_w = text_rect.width()
        text_h = text_rect.height()
        
        text_x = (w - text_w) // 2
        text_y = ly + logo_size + 15
        
        painter.setPen(QColor(60, 70, 80))
        painter.drawText(text_x, text_y, text)
        
        painter.save()
        clip_w = int(text_w * self.progress)
        painter.setClipRect(text_x, text_y - text_h, clip_w, text_h + 10)
        
        # Pulse opacity for the active text
        pulse = (abs(100 - (self.anim_tick % 200)) / 100.0) * 0.5 + 0.5
        c = QColor(self.theme_color)
        c.setAlphaF(pulse)
        painter.setPen(c)
        painter.drawText(text_x, text_y, text)
        painter.restore()
        
        # --- 4. Status Text & Activity Indicator ---
        painter.setFont(self.status_font)
        painter.setPen(QColor(200, 200, 200))
        status_w = painter.fontMetrics().horizontalAdvance(self.current_status)
        sx = (w - status_w) // 2
        sy = text_y + 30
        painter.drawText(sx, sy, self.current_status)
        
        # Rotating Tech circle
        painter.save()
        painter.translate(sx - 20, sy - 4)
        painter.rotate(self.anim_tick * 5)
        painter.setPen(QPen(self.theme_color, 2))
        painter.drawArc(-6, -6, 12, 12, 0, 250 * 16)
        painter.restore()
        
        painter.end()
        
        painter.end()


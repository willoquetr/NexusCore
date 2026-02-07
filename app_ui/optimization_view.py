from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, 
                               QFrame, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
                               QStackedWidget, QProgressBar, QWidget)
from PySide6.QtCore import Qt, QSize, QPoint
from PySide6.QtGui import QColor, QBrush, QFont
import qtawesome as qta

class OptimizationView(QWidget):
    """Indepedent window for AI Optimization results."""
    def __init__(self, parent_win, game_title):
        super().__init__()
        self.parent_win = parent_win # Reference for translations
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window) # Top-level window
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(900, 600)
        
        # Main Container with Border
        self.container = QFrame(self)
        self.container.setObjectName("OptContainer")
        self.container.setStyleSheet("""
            #OptContainer {
                background-color: #0f172a; 
                border: 2px solid #00d1ff; 
                border-radius: 12px;
            }
            QLabel { border: none; color: #e2e8f0; }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(self.container)
        
        inner_layout = QVBoxLayout(self.container)
        inner_layout.setContentsMargins(20, 20, 20, 20)
        
        # Header (Draggable zone)
        self.header = QFrame()
        self.header.setFixedHeight(50)
        self.header.setStyleSheet("background: transparent; border: none;")
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        title_lbl = QLabel(f"{self.parent_win.tr('opt_window_title')} : {game_title.upper()}")
        title_lbl.setStyleSheet("font-size: 18px; font-weight: 900; color: #00d1ff; letter-spacing: 1px;")
        
        self.close_btn = QPushButton()
        self.close_btn.setIcon(qta.icon("fa5s.times", color="#ffffff"))
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.setStyleSheet("""
            QPushButton { background: transparent; border: none; } 
            QPushButton:hover { background: #ef4444; border-radius: 15px; }
        """)
        self.close_btn.clicked.connect(self.close)
        
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()
        header_layout.addWidget(self.close_btn)
        inner_layout.addWidget(self.header)
        
        inner_layout.addSpacing(10)
        
        # Stacked Content (Loading vs Data)
        self.stack = QStackedWidget()
        inner_layout.addWidget(self.stack)
        
        # PAGE 1: LOADING
        self.page_loading = QWidget()
        load_layout = QVBoxLayout(self.page_loading)
        load_layout.setAlignment(Qt.AlignCenter)
        
        loading_lbl = QLabel(self.parent_win.tr("opt_loading"))
        loading_lbl.setStyleSheet("color: #94a3b8; font-size: 14px; font-weight: bold;")
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(400)
        self.progress_bar.setRange(0, 0) # Indeterminate animation
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: rgba(30, 41, 59, 0.5);
                border: none;
                height: 4px;
                border-radius: 2px;
            }
            QProgressBar::chunk { background-color: #00d1ff; }
        """)
        
        load_layout.addWidget(loading_lbl)
        load_layout.addSpacing(20)
        load_layout.addWidget(self.progress_bar)
        self.stack.addWidget(self.page_loading)
        
        # PAGE 2: TABLE
        self.page_table = QWidget()
        table_layout = QVBoxLayout(self.page_table)
        table_layout.setContentsMargins(0, 0, 0, 0)
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels([
            self.parent_win.tr("opt_col_setting"), 
            self.parent_win.tr("opt_col_current"), 
            self.parent_win.tr("opt_col_optimized")
        ])
        
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: rgba(30, 41, 59, 0.5);
                border: none;
                gridline-color: #334155;
                color: #cbd5e1;
            }
            QHeaderView::section {
                background-color: #1e293b;
                color: #00d1ff;
                font-weight: bold;
                border: none;
                padding: 8px;
            }
        """)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False) 
        
        table_layout.addWidget(self.table)
        
        footer_lbl = QLabel("SYSTEM STATUS: ANALYSIS COMPLETE | REVERT OPTIONS SECURED")
        footer_lbl.setStyleSheet("color: #64748b; font-size: 10px; font-style: italic; margin-top: 10px;")
        footer_lbl.setAlignment(Qt.AlignCenter)
        table_layout.addWidget(footer_lbl)
        
        self.stack.addWidget(self.page_table)
        self.stack.setCurrentIndex(0) # Start with loading page

    # --- Window Drag Logic ---
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Only drag from header or empty container areas
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and hasattr(self, '_drag_pos'):
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def set_data(self, current, optimized):
        """Switches from loading to table view with data."""
        self.populate_table(current, optimized)
        self.stack.setCurrentIndex(1) 

    def populate_table(self, current, optimized):
        all_keys = set(current.keys()) | set(optimized.keys())
        sorted_keys = sorted(list(all_keys))
        self.table.setRowCount(len(sorted_keys))
        
        for row, key in enumerate(sorted_keys):
            val_cur = current.get(key, "N/A")
            val_opt = optimized.get(key, "N/A")
            
            # Setting Name
            item_key = QTableWidgetItem(str(key))
            item_key.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(row, 0, item_key)
            
            # Current Value
            item_cur = QTableWidgetItem(str(val_cur))
            item_cur.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(row, 1, item_cur)
            
            # Optimized Value (with highlight)
            opt_item = QTableWidgetItem(str(val_opt))
            opt_item.setFlags(Qt.ItemIsEnabled)
            if str(val_cur) != str(val_opt):
                opt_item.setForeground(QBrush(QColor("#00d1ff")))
                font = QFont(); font.setBold(True)
                opt_item.setFont(font)
            self.table.setItem(row, 2, opt_item)

    def resizeEvent(self, event):
        self.container.setGeometry(self.rect())
        super().resizeEvent(event)
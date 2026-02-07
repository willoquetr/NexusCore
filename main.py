import sys
import os

# Ensure the root directory is in python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon, QPixmap, QImage
from PySide6.QtCore import Qt, QTimer, QThread, QRect
import time
import os
import sys
from core.logger import logger
from app_ui.splash import NexusSplash, resource_path

def get_nexus_icon():
    """Charge l'icône personnalisée assets/icon.png."""
    icon_path = resource_path("assets/icon.png")
    if os.path.exists(icon_path):
        return QIcon(icon_path)
    # Fallback au logo si l'icône n'existe pas
    return QIcon(resource_path("assets/logonexuscore.png"))

def exception_hook(exctype, value, traceback):
    logger.critical("UNHANDLED EXCEPTION", exc_info=(exctype, value, traceback))
    sys.__excepthook__(exctype, value, traceback)

sys.excepthook = exception_hook

def main():
    # Sécurité pour PyInstaller
    if getattr(sys, 'frozen', False):
        os.chdir(os.path.dirname(sys.executable))
        
    logger.info("--- NEXUS CORE STARTING ---")
    
    app = QApplication(sys.argv)
    app.setApplicationName("Nexus Core")
    app.setOrganizationName("NexusCorp")
    app.setWindowIcon(get_nexus_icon()) # Application de l'icône globale
    
    # Vérifier si on doit afficher le splash
    show_splash = "--no-splash" not in sys.argv
    
    if show_splash:
        splash = NexusSplash()
        splash.show()
        splash.fade_in()
    
    # On laisse l'animation de fade-in se terminer proprement (800ms)
    start_time = time.time()
    while time.time() - start_time < 0.8:
        app.processEvents()
        time.sleep(0.01)

    # 2. Simulation réaliste du chargement initial
    for pct in range(1, 45):
        if pct == 10: msg = "LOADING KERNEL MODULES..."
        elif pct == 25: msg = "INITIALIZING NEURAL NETWORK..."
        else: msg = "SCANNING SYSTEM INTERFACES..."
        
        splash.update_progress(pct, msg)
        app.processEvents()
        time.sleep(0.02)

    # 3. Le gros morceau : Initialisation & Téléchargements réels (45% -> 90%)
    splash.update_progress(50, "MOUNTING CORE UI COMPONENTS...")
    app.processEvents()
    
    from app_ui.mainwindow import MainWindow
    from core.optimizers.universal_reader import UniversalConfigReader # Import direct
    
    # Étape réelle : Sync Database
    splash.update_progress(60, "SYNCING GAME DATABASE...")
    app.processEvents()
    
    reader = UniversalConfigReader()
    # On passe une fonction lambda pour mettre à jour le splash en temps réel
    reader._load_ludusavi(progress_callback=lambda msg: (splash.update_progress(70, msg), app.processEvents()))
    
    splash.update_progress(85, "ESTABLISHING DATABASE LINK...")
    app.processEvents()
    
    window = MainWindow() 
    splash.update_progress(95, "FINALIZING HUD...")
    app.processEvents()
    
    time.sleep(0.2)
    splash.update_progress(100, "SYSTEM READY.")
    app.processEvents()
    time.sleep(0.4) 
    
    # 4. Fade out and Launch
    def launch_app():
        window.show()
        splash.close()

    splash.fade_out(launch_app)
    else:
        # Lancement direct (via le Launcher)
        from app_ui.mainwindow import MainWindow
        window = MainWindow()
        window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
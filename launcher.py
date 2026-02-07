import sys
import os
import json
import time
import requests
import subprocess
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QThread, Signal
from app_ui.splash import NexusSplash

# Configuration
VERSION_LOCALE = "1.0.0"
GITHUB_VERSION_URL = "https://raw.githubusercontent.com/NexusCoreProtocol/Database/main/version.json"
CORE_EXE = "NexusCore.exe" # Nom de l'exe final
CORE_SCRIPT = "main.py"    # Nom du script en dev

class UpdateWorker(QThread):
    progress = Signal(int, str)
    finished = Signal(bool, str) # Succès, Message

    def run(self):
        self.progress.emit(10, "CONNECTING TO NEXUS CLOUD...")
        time.sleep(1) # Effet visuel
        
        try:
            # 1. Vérification de la version
            self.progress.emit(30, "CHECKING FOR UPDATES...")
            # On simule ou on tente le download
            # response = requests.get(GITHUB_VERSION_URL, timeout=5)
            # remote_version = response.json().get("version")
            remote_version = "1.0.0" # Pour le test
            
            if remote_version > VERSION_LOCALE:
                self.progress.emit(50, f"NEW UPDATE FOUND: v{remote_version}")
                time.sleep(1)
                self.progress.emit(70, "DOWNLOADING PATCH...")
                # Ici on ferait le download réel
                time.sleep(2)
                self.progress.emit(90, "APPLYING PATCH...")
                time.sleep(1)
                self.finished.emit(True, "Update installed successfully.")
            else:
                self.progress.emit(80, "SYSTEM UP TO DATE.")
                time.sleep(0.5)
                self.finished.emit(True, "No update needed.")
                
        except Exception as e:
            self.finished.emit(False, f"Cloud sync failed: {str(e)}")

def main():
    app = QApplication(sys.argv)
    
    splash = NexusSplash()
    splash.show()
    splash.fade_in()
    
    # On attend que le fade-in finisse
    time.sleep(0.8)
    
    worker = UpdateWorker()
    worker.progress.connect(splash.update_progress)
    
    def on_finished(success, msg):
        splash.update_progress(100, "LAUNCHING SYSTEM...")
        
        def start_core():
            # Si on est en version compilée (EXE)
            if os.path.exists(CORE_EXE):
                subprocess.Popen([CORE_EXE, "--no-splash"])
            # Sinon en mode Python
            else:
                subprocess.Popen([sys.executable, CORE_SCRIPT, "--no-splash"])
            
            splash.close()
            sys.exit()

        # On attend un peu pour montrer le 100%
        splash.fade_out(start_core)

    worker.finished.connect(on_finished)
    worker.start()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

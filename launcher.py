import sys
import os
import json
import time
import requests
import subprocess
import zipfile
import shutil
import tempfile
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt, QThread, Signal
from app_ui.splash import NexusSplash

# --- CONFIGURATION ---
# Pour l'instant, on pointe vers le repo public (à créer)
REPO_USER = "TON_PSEUDO" # À remplacer
REPO_NAME = "NexusCore"  # Le repo public
VERSION_FILE_URL = f"https://raw.githubusercontent.com/{REPO_USER}/{REPO_NAME}/main/version.json"
# L'URL du ZIP sera construite dynamiquement ou lue dans le version.json distant

CORE_EXE = "NexusCore.exe"
LOCAL_VERSION_FILE = "data/version.json"

def get_local_version():
    if os.path.exists(LOCAL_VERSION_FILE):
        try:
            with open(LOCAL_VERSION_FILE, "r") as f:
                return json.load(f).get("version", "0.0.0")
        except: pass
    return "0.0.0"

def update_local_version(new_version):
    data = {"version": new_version, "last_update": time.strftime("%Y-%m-%d")}
    os.makedirs("data", exist_ok=True)
    with open(LOCAL_VERSION_FILE, "w") as f:
        json.dump(data, f, indent=4)

class UpdateWorker(QThread):
    progress = Signal(int, str)
    finished = Signal(bool, str)

    def run(self):
        self.progress.emit(10, "CONNECTING TO NEXUS CLOUD...")
        time.sleep(0.5)
        
        try:
            # 1. Vérification
            self.progress.emit(20, "CHECKING FOR UPDATES...")
            try:
                response = requests.get(VERSION_FILE_URL, timeout=5)
                if response.status_code != 200:
                    raise Exception("Server unreachable")
                remote_data = response.json()
                remote_version = remote_data.get("version")
                download_url = remote_data.get("download_url") # L'URL du ZIP doit être dans le JSON distant
            except Exception as e:
                # En mode dev/offline, on continue
                print(f"Update check failed: {e}")
                self.finished.emit(True, "Offline Mode")
                return

            local_version = get_local_version()
            
            if remote_version > local_version and download_url:
                self.progress.emit(30, f"NEW UPDATE FOUND: v{remote_version}")
                time.sleep(1)
                
                # 2. Téléchargement
                self.progress.emit(40, "DOWNLOADING PATCH PACKAGE...")
                r = requests.get(download_url, stream=True)
                total_size = int(r.headers.get('content-length', 0))
                block_size = 1024
                wrote = 0
                
                temp_zip = os.path.join(tempfile.gettempdir(), "nexus_update.zip")
                with open(temp_zip, 'wb') as f:
                    for data in r.iter_content(block_size):
                        wrote = wrote + len(data)
                        f.write(data)
                        # Calculer progression entre 40% et 80%
                        if total_size > 0:
                            percent = 40 + int((wrote / total_size) * 40)
                            self.progress.emit(percent, "DOWNLOADING PATCH PACKAGE...")
                
                # 3. Installation
                self.progress.emit(85, "EXTRACTING CORE FILES...")
                try:
                    with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                        # On extrait dans le dossier courant (remplace les fichiers)
                        # Attention: Le launcher ne peut pas s'écraser lui-même s'il tourne
                        # On suppose que le ZIP contient le dossier 'NexusCore' ou les fichiers direct
                        zip_ref.extractall(".")
                except Exception as e:
                    raise Exception(f"Extraction failed: {e}")
                
                update_local_version(remote_version)
                self.progress.emit(95, "UPDATE COMPLETE.")
                time.sleep(1)
                self.finished.emit(True, "Updated")
                
            else:
                self.progress.emit(80, "SYSTEM IS UP TO DATE.")
                time.sleep(0.5)
                self.finished.emit(True, "No update")
                
        except Exception as e:
            # On ne bloque pas le lancement si l'update échoue (sauf erreur critique)
            print(f"Update process error: {e}")
            self.finished.emit(True, "Update Skipped")

def main():
    # Sécurité PyInstaller
    if getattr(sys, 'frozen', False):
        os.chdir(os.path.dirname(sys.executable))

    app = QApplication(sys.argv)
    
    splash = NexusSplash()
    splash.show()
    splash.fade_in()
    
    # Attente fin animation fade-in
    start_t = time.time()
    while time.time() - start_t < 0.8:
        app.processEvents()
        time.sleep(0.01)
    
    worker = UpdateWorker()
    worker.progress.connect(splash.update_progress)
    
    def on_finished(success, msg):
        splash.update_progress(100, "INITIALIZING CORE SYSTEM...")
        app.processEvents()
        time.sleep(0.5)
        
        # Lancement du Core
        if os.path.exists(CORE_EXE):
            subprocess.Popen([CORE_EXE, "--no-splash"])
        elif os.path.exists("main.py"):
            # Mode Dev
            subprocess.Popen([sys.executable, "main.py", "--no-splash"])
        else:
            # Cas critique : ni exe ni script
            QMessageBox.critical(None, "Error", "Core system not found!")
            
        splash.close()
        sys.exit()

    worker.finished.connect(on_finished)
    worker.start()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
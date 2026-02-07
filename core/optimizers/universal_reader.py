import os
import json
import configparser
import xml.etree.ElementTree as ET
import winreg
import requests
import yaml
import sqlite3
from core.logger import logger
import sys

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# URLs
CLOUD_PROFILES_URL = "https://raw.githubusercontent.com/NexusCoreProtocol/Database/main/game_profiles.json"
LUDUSAVI_MANIFEST_URL = "https://raw.githubusercontent.com/mtkennerly/ludusavi-manifest/master/data/manifest.yaml"

class UniversalConfigReader:
    def __init__(self):
        self.profiles = self._load_profiles()
        self.db_path = "data/ludusavi.db"
        self._sync_with_cloud()
        logger.info("Optimizer: UniversalConfigReader initialized.")

    def _load_profiles(self):
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
        ext_path = os.path.join(base_dir, "data", "game_profiles.json")
        if os.path.exists(ext_path):
            try:
                with open(ext_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except: pass
        return {}

    def _sync_with_cloud(self):
        try:
            response = requests.get(CLOUD_PROFILES_URL, timeout=3)
            if response.status_code == 200:
                cloud_data = response.json()
                self.profiles.update(cloud_data)
                save_dir = "data"
                os.makedirs(save_dir, exist_ok=True)
                save_path = os.path.join(save_dir, "game_profiles.json")
                with open(save_path, "w", encoding="utf-8") as f:
                    json.dump(self.profiles, f, indent=4)
        except: pass

    def _convert_yaml_to_sqlite(self, yaml_path):
        """Convertit le lourd YAML en base SQLite performante."""
        logger.info("Optimizer: Converting YAML manifest to SQLite...")
        try:
            with open(yaml_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            os.makedirs("data", exist_ok=True)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DROP TABLE IF EXISTS games")
            cursor.execute("CREATE TABLE games (title TEXT PRIMARY KEY, files TEXT)")
            
            games = data.get("games", {})
            batch = []
            for title, g_data in games.items():
                batch.append((title, json.dumps(g_data.get("files", {}))))
                if len(batch) >= 500:
                    cursor.executemany("INSERT INTO games VALUES (?, ?)", batch)
                    batch = []
            if batch:
                cursor.executemany("INSERT INTO games VALUES (?, ?)", batch)
            
            cursor.execute("CREATE INDEX idx_title ON games(title)")
            conn.commit()
            conn.close()
            logger.info("Optimizer: SQLite conversion complete.")
            return True
        except Exception as e:
            logger.error(f"Optimizer: Conversion failed: {e}")
            return False

    def _load_ludusavi(self, progress_callback=None):
        """Gère le téléchargement et la conversion si nécessaire."""
        yaml_path = "data/ludusavi_manifest.yaml"
        
        # 1. Téléchargement si absent
        if not os.path.exists(yaml_path):
            try:
                if progress_callback: progress_callback("DOWNLOADING GLOBAL MANIFEST...")
                logger.info("Optimizer: Downloading Ludusavi manifest...")
                response = requests.get(LUDUSAVI_MANIFEST_URL, timeout=15)
                if response.status_code == 200:
                    os.makedirs("data", exist_ok=True)
                    with open(yaml_path, "wb") as f:
                        f.write(response.content)
            except Exception as e:
                logger.error(f"Optimizer: Download failed: {e}")
                return False

        # 2. Conversion en SQLite si absent
        if not os.path.exists(self.db_path):
            if progress_callback: progress_callback("OPTIMIZING DATABASE (SQLITE)...")
            return self._convert_yaml_to_sqlite(yaml_path)
            
        return True

    def get_settings(self, game_name, install_dir=None):
        game_name_clean = game_name.lower()
        logger.info(f"Optimizer: Searching config for -> {game_name_clean}")
        
        # 1. JSON Profiles Match
        profile = None
        for key in self.profiles:
            if key in game_name_clean:
                profile = self.profiles[key]
                break
        
        path = None
        if profile:
            path = self._resolve_path(profile, install_dir)
        
        # 2. Heuristics
        if not path or not os.path.exists(path):
            path, h_fmt = self._resolve_path_heuristically(game_name, install_dir)
            if path: profile = {"format": h_fmt}

        # 3. Deep Search SQLite
        if not path or not os.path.exists(path):
            path, d_fmt = self._deep_search_ludusavi(game_name)
            if path: profile = {"format": d_fmt}

        if not path or not os.path.exists(path):
            return None

        # 4. Parsing
        try:
            settings = None
            fmt = profile.get("format", "ini")
            if fmt == "json":
                with open(path, "r", encoding="utf-8") as f: settings = json.load(f)
            elif fmt in ["ini", "yaml", "cfg"]:
                config = configparser.ConfigParser(strict=False, allow_no_value=True)
                config.read(path)
                settings = {s: dict(config.items(s)) for s in config.sections()}
                if not settings: settings = {"raw_content": open(path, "r").read()[:1000]}
            elif fmt == "xml":
                tree = ET.parse(path)
                settings = {elem.tag: elem.text for elem in tree.getroot().iter() if elem.text}
            elif fmt == "key_value_space":
                settings = {}
                with open(path, "r", encoding="utf-8") as f:
                    for line in f:
                        parts = line.strip().split(None, 1)
                        if len(parts) == 2: settings[parts[0]] = parts[1].replace('"', '')
            else:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    settings = {"raw_config_preview": f.read(1000)}
            return settings
        except Exception as e:
            logger.error(f"Optimizer: Parsing error: {e}")
        return None

    def _deep_search_ludusavi(self, game_name):
        """Recherche SQL ultra-rapide."""
        if not os.path.exists(self.db_path):
            self._load_ludusavi()
            
        if not os.path.exists(self.db_path): return None, None

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # Recherche avec LIKE pour matcher le titre
            cursor.execute("SELECT files FROM games WHERE title LIKE ? LIMIT 1", (f"%{game_name}%",))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                files = json.loads(row[0])
                for f_path in files.keys():
                    if any(ext in f_path.lower() for ext in [".ini", ".cfg", ".json", ".xml", "settings", "prefs"]):
                        real_path = self._expand_ludusavi_path(f_path)
                        if real_path and os.path.exists(real_path):
                            fmt = "ini"
                            if ".json" in real_path.lower(): fmt = "json"
                            if ".xml" in real_path.lower(): fmt = "xml"
                            return real_path, fmt
        except Exception as e:
            logger.error(f"Optimizer: SQLite Search error: {e}")
        return None, None

    def _expand_ludusavi_path(self, path):
        path = path.replace("<home>", os.environ.get("USERPROFILE", ""))
        path = path.replace("<winAppData>", os.environ.get("APPDATA", ""))
        path = path.replace("<winLocalAppData>", os.environ.get("LOCALAPPDATA", ""))
        path = path.replace("<winDocuments>", os.path.join(os.environ.get("USERPROFILE", ""), "Documents"))
        path = path.replace("<xdgConfig>", os.environ.get("APPDATA", "")) 
        return os.path.normpath(path)

    def _resolve_path(self, profile, install_dir):
        base_dir = ""
        loc = profile.get("search_in", "")
        if loc == "install_dir" and install_dir: base_dir = install_dir
        elif loc == "local_appdata": base_dir = os.environ.get("LOCALAPPDATA", "")
        elif loc == "appdata": base_dir = os.environ.get("APPDATA", "")
        elif loc == "documents": base_dir = os.path.join(os.environ.get("USERPROFILE", ""), "Documents")
        elif loc == "saved_games": base_dir = os.path.join(os.environ.get("USERPROFILE", ""), "Saved Games")
        
        if base_dir:
            return os.path.join(base_dir, profile.get("relative_path", ""), profile.get("config_file", ""))
        return None

    def _resolve_path_heuristically(self, game_name, install_dir):
        if not install_dir or not os.path.exists(install_dir): return None, None
        
        # Unreal Engine
        if os.path.exists(os.path.join(install_dir, "Engine")):
            local_appdata = os.environ.get("LOCALAPPDATA", "")
            for folder in os.listdir(local_appdata):
                if game_name.replace(" ", "").lower() in folder.lower():
                    p = os.path.join(local_appdata, folder, "Saved", "Config", "WindowsNoEditor", "GameUserSettings.ini")
                    if os.path.exists(p): return p, "ini"
        
        # Unity
        if any(f.endswith("_Data") for f in os.listdir(install_dir)):
            local_low = os.path.join(os.environ.get("USERPROFILE", ""), "AppData", "LocalLow")
            if os.path.exists(local_low):
                for company in os.listdir(local_low):
                    cp = os.path.join(local_low, company)
                    for folder in os.listdir(cp):
                        if game_name.replace(" ", "").lower() in folder.lower():
                            fp = os.path.join(cp, folder)
                            for f in os.listdir(fp):
                                if "settings" in f.lower(): return os.path.join(fp, f), "xml"
        return None, None

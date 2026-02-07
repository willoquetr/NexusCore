import os
import winreg

def scan_battlenet_games():
    """Scanne les jeux Blizzard Battle.net via le registre Uninstall."""
    games = []
    try:
        # Battle.net utilise les clés Uninstall standard
        reg_path = r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
            i = 0
            while True:
                try:
                    subkey_name = winreg.EnumKey(key, i)
                    # Les jeux Blizzard commencent souvent par leur ID interne
                    if subkey_name.startswith("Battle.net") or any(x in subkey_name for x in ["World of Warcraft", "Overwatch", "Diablo", "StarCraft"]):
                        with winreg.OpenKey(key, subkey_name) as subkey:
                            try:
                                title, _ = winreg.QueryValueEx(subkey, "DisplayName")
                                install_dir, _ = winreg.QueryValueEx(subkey, "InstallLocation")
                                
                                # Chercher un exe probable
                                exe_path = None
                                if os.path.exists(install_dir):
                                    # On cherche dans le dossier racine
                                    for f in os.listdir(install_dir):
                                        if f.endswith(".exe") and not any(x in f.lower() for x in ["launcher", "setup", "update", "browser"]):
                                            exe_path = os.path.join(install_dir, f)
                                            break
                                
                                if title and install_dir:
                                    games.append({
                                        "id": f"bnet:{subkey_name}",
                                        "title": title,
                                        "launcher": "Battle.net",
                                        "exe": exe_path,
                                        "install_dir": install_dir
                                    })
                            except: pass
                    i += 1
                except OSError: break
    except Exception:
        pass
        
    return games

import os
import winreg

def scan_riot_games():
    """Scanne les jeux Riot (Valorant, LoL) via le registre ou chemins standard."""
    games = []
    
    # Riot stocke les infos dans HKCU
    reg_path = r"Software\Microsoft\Windows\CurrentVersion\Uninstall"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path) as key:
            i = 0
            while True:
                try:
                    subkey_name = winreg.EnumKey(key, i)
                    if subkey_name.startswith("Riot Game"):
                        with winreg.OpenKey(key, subkey_name) as subkey:
                            try:
                                title, _ = winreg.QueryValueEx(subkey, "DisplayName")
                                install_dir, _ = winreg.QueryValueEx(subkey, "InstallLocation")
                                
                                # Chercher l'exe (Riot utilise souvent des raccourcis, mais on cherche le vrai exe)
                                exe_path = None
                                if os.path.exists(install_dir):
                                    for root, dirs, files in os.walk(install_dir):
                                        for f in files:
                                            if f.endswith(".exe") and not any(x in f.lower() for x in ["crash", "bug", "redist", "port"]):
                                                exe_path = os.path.join(root, f)
                                                break
                                        if exe_path: break
                                
                                games.append({
                                    "id": f"riot:{subkey_name}",
                                    "title": title,
                                    "launcher": "Riot",
                                    "exe": exe_path,
                                    "install_dir": install_dir
                                })
                            except: pass
                    i += 1
                except OSError: break
    except: pass
    
    return games

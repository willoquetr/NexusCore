import os
import winreg

def scan_ea_games():
    """Scanne les jeux EA Desktop (EA App) via le registre."""
    games = []
    try:
        reg_path = r"SOFTWARE\Electronic Arts\EA Desktop\Installations"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
            i = 0
            while True:
                try:
                    game_code = winreg.EnumKey(key, i)
                    with winreg.OpenKey(key, game_code) as subkey:
                        try:
                            install_dir, _ = winreg.QueryValueEx(subkey, "installLocation")
                            # Le nom est souvent dans un dossier parent ou via une autre clé
                            title = os.path.basename(install_dir.rstrip("\\/"))
                            
                            exe_path = None
                            if os.path.exists(install_dir):
                                # On cherche l\'exe dans le dossier racine d\'abord
                                for f in os.listdir(install_dir):
                                    if f.endswith(".exe") and not any(x in f.lower() for x in ["cleanup", "touchup", "ea", "installer"]):
                                        exe_path = os.path.join(install_dir, f)
                                        break

                            games.append({
                                "id": f"ea:{game_code}",
                                "title": title,
                                "launcher": "EA",
                                "exe": exe_path,
                                "install_dir": install_dir
                            })
                        except:
                            pass
                    i += 1
                except OSError:
                    break
    except Exception as e:
        # Erreur silencieuse si le launcher n'est pas installé
        pass
        
    return games

import os
import winreg
import yaml # Si besoin, mais souvent c'est binaire ou registry

def scan_ubisoft_games():
    """Scanne les jeux Ubisoft Connect via le registre."""
    games = []
    try:
        # Ubisoft stocke les installations ici
        reg_path = r"SOFTWARE\WOW6432Node\Ubisoft\Launcher\Installs"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
            i = 0
            while True:
                try:
                    # Chaque sous-clé est un ID de jeu
                    game_id = winreg.EnumKey(key, i)
                    with winreg.OpenKey(key, game_id) as subkey:
                        try:
                            install_dir, _ = winreg.QueryValueEx(subkey, "InstallDir")
                            # Pour Ubisoft, le nom n'est pas toujours dans la clé d'install
                            # On prend le nom du dossier par défaut
                            title = os.path.basename(install_dir.rstrip("\\/"))
                            
                            # Chercher un exe probable
                            exe_path = None
                            if os.path.exists(install_dir):
                                for root, dirs, files in os.walk(install_dir):
                                    for f in files:
                                        if f.endswith(".exe") and not any(x in f.lower() for x in ["ubi", "crash", "version", "overlay", "plugin"]):
                                            exe_path = os.path.join(root, f)
                                            break
                                    if exe_path: break

                            games.append({
                                "id": f"ubisoft:{game_id}",
                                "title": title,
                                "launcher": "Ubisoft",
                                "exe": exe_path,
                                "install_dir": install_dir
                            })
                        except:
                            pass
                    i += 1
                except OSError: break
    except Exception as e:
        # Erreur silencieuse si le launcher n'est pas installé
        pass
        
    return games

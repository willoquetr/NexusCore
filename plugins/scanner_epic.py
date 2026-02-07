import os
import json

def scan_epic_games():
    """Scanne les jeux Epic Games via les fichiers manifest (.item)."""
    # Chemin standard des manifests Epic sur Windows
    manifest_path = r"C:\ProgramData\Epic\EpicGamesLauncher\Data\Manifests"
    games = []
    
    if not os.path.exists(manifest_path):
        return []

    try:
        for file in os.listdir(manifest_path):
            if file.endswith(".item"):
                with open(os.path.join(manifest_path, file), "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # On récupère le nom et le chemin de l\'exe
                    title = data.get("DisplayName")
                    install_dir = data.get("InstallLocation")
                    launch_exe = data.get("LaunchExecutable")
                    
                    if title and install_dir and launch_exe:
                        exe_full_path = os.path.join(install_dir, launch_exe).replace("/", "\\")
                        games.append({
                            "id": f"epic:{data.get('AppName')}",
                            "title": title,
                            "launcher": "Epic",
                            "exe": exe_full_path,
                            "install_dir": install_dir
                        })
    except Exception as e:
        print(f"Erreur scan Epic: {e}")
        
    return games

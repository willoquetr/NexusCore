import os
import winreg
import re

def get_steam_install_path():
    """Trouve le chemin d'installation de Steam via le registre Windows."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam")
        path, _ = winreg.QueryValueEx(key, "SteamPath")
        return path.replace("/", "\\")
    except Exception:
        return None

def parse_vdf(content):
    """Un parser VDF très simplifié pour extraire les chemins de bibliothèque."""
    paths = []
    # On cherche "path" "C:\\SteamLibrary"
    matches = re.findall(r'"path"\s+"([^\"]+)"', content)
    for m in matches:
        paths.append(m.replace("\\\\", "\\"))
    return paths

def scan_steam_games():
    """Scanne les jeux Steam installés."""
    steam_path = get_steam_install_path()
    if not steam_path:
        return []

    library_folders = [os.path.join(steam_path, "steamapps")]
    
    # Chercher d'autres bibliothèques
    lib_vdf_path = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
    if os.path.exists(lib_vdf_path):
        with open(lib_vdf_path, "r", encoding="utf-8") as f:
            content = f.read()
            additional_paths = parse_vdf(content)
            for p in additional_paths:
                lib_app_path = os.path.join(p, "steamapps")
                if lib_app_path not in library_folders and os.path.exists(lib_app_path):
                    library_folders.append(lib_app_path)

    games = []
    for folder in library_folders:
        if not os.path.exists(folder):
            continue
            
        for file in os.listdir(folder):
            if file.startswith("appmanifest_") and file.endswith(".acf"):
                manifest_path = os.path.join(folder, file)
                try:
                    with open(manifest_path, "r", encoding="utf-8") as f:
                        m_content = f.read()
                        name_match = re.search(r'"name"\s+"([^\"]+)"', m_content)
                        appid_match = re.search(r'"appid"\s+"([^\"]+)"', m_content)
                        folder_match = re.search(r'"installdir"\s+"([^\"]+)"', m_content)
                        
                        if name_match and appid_match:
                            game_id = f"steam:{appid_match.group(1)}"
                            games.append({
                                "id": game_id,
                                "title": name_match.group(1),
                                "launcher": "Steam",
                                "install_dir": os.path.join(folder, "common", folder_match.group(1)) if folder_match else "",
                                "appid": appid_match.group(1)
                            })
                except Exception as e:
                    print(f"Erreur lecture manifest {file}: {e}")
                    
    return games

if __name__ == "__main__":
    # Petit test rapide
    found = scan_steam_games()
    for g in found:
        print(f"Trouvé: {g['title']} ({g['id']})")

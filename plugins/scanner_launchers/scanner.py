import os
import winreg

def get_launcher_path(reg_key, val_name="InstallLocation"):
    """Cherche un chemin dans le registre Windows."""
    for root in [winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE]:
        try:
            key = winreg.OpenKey(root, reg_key)
            path, _ = winreg.QueryValueEx(key, val_name)
            return path
        except:
            continue
    return None

def scan_launchers():
    """Détecte les launchers installés."""
    launchers = []
    
    # 1. STEAM
    steam_path = get_launcher_path(r"Software\Valve\Steam", "SteamPath")
    if steam_path:
        launchers.append({
            "id": "launcher:steam",
            "title": "Steam",
            "exe": os.path.join(steam_path, "steam.exe").replace("/", "\\").replace("\\", "\\"),
            "type": "launcher"
        })

    # 2. EPIC GAMES
    epic_path = get_launcher_path(r"Software\Epic Games\EpicGamesLauncher", "AppDataPath")
    # Souvent InstallLocation est mieux, mais Epic est capricieux
    if epic_path:
        # On remonte d'un cran si c'est AppData
        exe = os.path.join(os.path.dirname(epic_path), "Portal", "Binaries", "Win64", "EpicGamesLauncher.exe")
        launchers.append({
            "id": "launcher:epic",
            "title": "Epic Games",
            "exe": exe,
            "type": "launcher"
        })

    # 3. UBISOFT CONNECT
    ubi_path = get_launcher_path(r"Software\Ubisoft\Launcher", "InstallDir")
    if ubi_path:
        launchers.append({
            "id": "launcher:ubisoft",
            "title": "Ubisoft Connect",
            "exe": os.path.join(ubi_path, "UbisoftConnect.exe"),
            "type": "launcher"
        })

    # 4. EA APP
    ea_path = get_launcher_path(r"Software\Electronic Arts\EA Desktop", "InstallDir")
    if ea_path:
        launchers.append({
            "id": "launcher:ea",
            "title": "EA App",
            "exe": os.path.join(ea_path, "EADesktop.exe"),
            "type": "launcher"
        })

    # 5. BATTLE.NET
    bnet_path = get_launcher_path(r"Software\WOW6432Node\Blizzard Entertainment\Battle.net\Capabilities", "ApplicationIcon")
    if bnet_path:
        # ApplicationIcon contient le chemin de l'exe (souvent Battle.net.exe,0)
        exe = bnet_path.split(",")[0].strip('"')
        launchers.append({
            "id": "launcher:battlenet",
            "title": "Battle.net",
            "exe": exe,
            "type": "launcher"
        })

    # 6. RIOT CLIENT
    riot_path = get_launcher_path(r"Software\Microsoft\Windows\CurrentVersion\Uninstall\Riot Game valorant.live", "InstallLocation")
    if not riot_path:
        riot_path = get_launcher_path(r"Software\Microsoft\Windows\CurrentVersion\Uninstall\Riot Game league_of_legends.live", "InstallLocation")
    
    if riot_path:
        # On remonte au dossier Riot Games puis Riot Client
        # Souvent: C:\Riot Games\Riot Client\RiotClientServices.exe
        base_riot = os.path.dirname(riot_path.rstrip("\\/"))
        exe = os.path.join(base_riot, "Riot Client", "RiotClientServices.exe")
        if os.path.exists(exe):
            launchers.append({
                "id": "launcher:riot",
                "title": "Riot Client",
                "exe": exe,
                "type": "launcher"
            })

    # 7. DISCORD
    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        discord_dir = os.path.join(local_appdata, "Discord")
        if os.path.exists(discord_dir):
            # Discord utilise des dossiers 'app-1.0.9001', on cherche le plus récent
            apps = [d for d in os.listdir(discord_dir) if d.startswith("app-")]
            if apps:
                apps.sort(reverse=True)
                exe = os.path.join(discord_dir, apps[0], "Discord.exe")
                if os.path.exists(exe):
                    launchers.append({
                        "id": "launcher:discord",
                        "title": "Discord",
                        "exe": exe,
                        "type": "launcher"
                    })

    return launchers

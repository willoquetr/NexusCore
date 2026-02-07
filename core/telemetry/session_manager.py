import psutil
import os
from core.database import get_session, GameSession, HardwareSnapshot
import datetime
from core.logger import logger

class SessionManager:
    def __init__(self):
        self.current_session = None
        self.monitored_executables = {} # {exe_name: game_id}
        # Liste des executables à ignorer (Launchers)
        self.ignored_executables = [
            "steam.exe", "epicgameslauncher.exe", "ubisoftconnect.exe", 
            "eadesktop.exe", "battle.net.exe", "riotclientux.exe", "discord.exe"
        ]
        logger.info("SessionMgr: Initialized.")

    def update_games_list(self, games):
        """Met à jour la liste des exe à surveiller."""
        count = 0
        for g in games:
            if g.get('exe'):
                exe_name = os.path.basename(g['exe']).lower()
                if exe_name not in self.ignored_executables:
                    self.monitored_executables[exe_name] = g['title']
                    count += 1
        logger.info(f"SessionMgr: Monitoring {count} unique game executables.")

    def check_running_games(self):
        """Vérifie si un jeu surveillé tourne (Exclut les launchers)."""
        for proc in psutil.process_iter(['name']):
            try:
                name = proc.info['name'].lower()
                
                # Si c'est un launcher, on ignore
                if name in self.ignored_executables:
                    continue
                    
                # Si c'est un jeu qu'on surveille
                if name in self.monitored_executables:
                    if not self.current_session:
                        self.start_session(name, self.monitored_executables[name])
                    return True
                
                # Fallback : détection basique pour Rust/Cyberpunk si pas en liste
                if name == "rust.exe" or name == "cyberpunk2077.exe":
                    if not self.current_session:
                        self.start_session(name, name.replace(".exe", ""))
                    return True
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        if self.current_session:
            self.end_session()
        return False

    def start_session(self, game_id, game_title):
        try:
            db = get_session()
            new_session = GameSession(game_id=game_id, game_title=game_title)
            db.add(new_session)
            db.commit()
            self.current_session = {
                "id": new_session.id,
                "game_id": game_id,
                "title": game_title
            }
            logger.info(f"SessionMgr: STARTED session for {game_title} (ID: {new_session.id})")
            db.close()
        except Exception as e:
            logger.error(f"SessionMgr: Error starting session for {game_title}: {e}", exc_info=True)

    def end_session(self):
        if not self.current_session:
            return
        try:
            title = self.current_session['title']
            db = get_session()
            sess = db.query(GameSession).filter(GameSession.id == self.current_session['id']).first()
            if sess:
                sess.end_time = datetime.datetime.utcnow()
                db.commit()
            logger.info(f"SessionMgr: ENDED session for {title}")
            self.current_session = None
            db.close()
        except Exception as e:
            logger.error(f"SessionMgr: Error ending session: {e}", exc_info=True)

    def get_current_session_id(self):
        return self.current_session['id'] if self.current_session else None
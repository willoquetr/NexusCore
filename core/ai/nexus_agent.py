from groq import Groq
import json
import os
from core.database import get_session, GameSession, HardwareSnapshot
from sqlalchemy import desc
from core.optimizers.universal_reader import UniversalConfigReader
from core.logger import logger

class NexusAgent:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.client = None
        self.model_id = "llama-3.3-70b-versatile"
        self.chat_history = [] 
        self.config_reader = UniversalConfigReader() # New Universal system
        logger.info("AI: NexusAgent initialized.")
        
        self.system_instruction = (
            "Tu es Nexus, l'intelligence artificielle de Nexus Core. "
            "Ton but est d'aider les joueurs à optimiser leurs jeux et à diagnostiquer les problèmes matériels. "
            "Tu es expert en hardware PC (CPU, GPU, RAM, Thermals). "
            "IMPORTANT: Lorsqu'on te pose une question sur un jeu ou un lag, tu as accès à la DERNIÈRE SESSION de l'utilisateur. "
            "Analyse les chiffres fournis (pics de temp, saturation RAM) pour expliquer les stutterings ou autres problèmes. "
            "Tu as aussi accès à l'historique récent de vos discussions. Si tu as déjà donné un conseil (ex: changer SMAA en FXAA), "
            "n'hésite pas à demander si l'utilisateur l'a appliqué et si ça a aidé. "
            "Sois direct, technique mais accessible. Ne parle que si on te sollicite. " 
            "IMPORTANT: Ne suppose JAMAIS qu'un jeu est en cours si le contexte indique '[SESSION ACTIVE]: NON'. "
            "Si la RAM est élevée alors qu'aucune session n'est active, suggère plutôt des causes liées au système ou au multitâche. "
            "Analyse les chiffres fournis avec rigueur. Ne parle que si on te sollicite."
        )

        if api_key:
            self.setup_model(api_key)

    def setup_model(self, api_key):
        try:
            self.client = Groq(api_key=api_key)
            logger.info("AI: Groq client setup successful.")
        except Exception as e:
            logger.error(f"AI: Error setting up Groq client: {e}", exc_info=True)

    def analyze_last_session(self, game_name):
        """Cherche et analyse les stats de la dernière session pour un jeu."""
        db = get_session()
        session = db.query(GameSession).filter(GameSession.game_title.ilike(f"%{game_name}%")).order_by(desc(GameSession.start_time)).first()
        
        if not session:
            db.close()
            return None

        snapshots = db.query(HardwareSnapshot).filter(HardwareSnapshot.session_id == session.id).all()
        if not snapshots:
            db.close()
            return None

        cpu_avg = sum(s.cpu_usage for s in snapshots) / len(snapshots)
        cpu_max = max(s.cpu_usage for s in snapshots)
        gpu_temp_max = max((s.gpu_temp for s in snapshots if s.gpu_temp), default=0)
        gpu_load_max = max((s.gpu_usage for s in snapshots if s.gpu_usage), default=0)
        ram_max = max(s.ram_usage for s in snapshots)

        db.close()
        return {
            "title": session.game_title,
            "duration_mins": (session.end_time - session.start_time).seconds // 60 if (session.start_time and session.end_time) else "En cours",
            "cpu_avg": cpu_avg,
            "cpu_max": cpu_max,
            "gpu_temp_max": gpu_temp_max,
            "gpu_load_max": gpu_load_max,
            "ram_max": ram_max,
            "snapshot_count": len(snapshots)
        }

    def get_response(self, user_input, hardware_stats=None, is_gaming=False):
        if not self.client:
            logger.warning("AI: Client not configured when requested for response.")
            return "IA non configurée. Vérifiez votre clé API."

        # Detection dynamique de jeu (mots de plus de 3 lettres)
        potential_games = [word for word in user_input.split() if len(word) > 3]
        historical_context = ""
        game_settings_context = ""
        
        for word in potential_games:
            game_lower = word.lower()
            stats = self.analyze_last_session(game_lower)
            if stats:
                historical_context = (
                    f"\n\n[ANALYSE DERNIÈRE SESSION {stats['title'].upper()}]: "
                    f"Durée: {stats['duration_mins']} min | "
                    f"CPU Max: {stats['cpu_max']:.1f}% | "
                    f"GPU Temp Max: {stats['gpu_temp_max']}°C | "
                    f"RAM Max: {stats['ram_max']}% | "
                    f"Données: {stats['snapshot_count']} relevés. "
                )
                
                # Universal Settings Reading
                settings = self.config_reader.get_settings(word)
                if settings:
                    game_settings_context = f"\n[RÉGLAGES ACTUELS DU JEU]: {json.dumps(settings)}"
                break

        stats_str = ""
        if hardware_stats:
            active_game_str = "OUI" if is_gaming else "NON"
            stats_str = (
                f"\n\n[STATUS TEMPS RÉEL]: "
                f"SESSION JEU ACTIVE: {active_game_str} | "
                f"CPU: {hardware_stats.get('cpu')}% | RAM: {hardware_stats.get('ram')}%"
            )

        messages = [{"role": "system", "content": self.system_instruction}]
        for msg in self.chat_history[-6:]:
            messages.append(msg)
        
        user_msg = f"Contexte:{historical_context}{game_settings_context}{stats_str}\n\nQuestion: {user_input}"
        messages.append({"role": "user", "content": user_msg})

        logger.debug(f"AI: Sending Prompt -> {user_msg}")

        try:
            completion = self.client.chat.completions.create(
                model=self.model_id,
                messages=messages
            )
            response = completion.choices[0].message.content
            logger.info(f"AI: Received Response -> {response[:100]}...")
            
            # Save history
            self.chat_history.append({"role": "user", "content": user_input})
            self.chat_history.append({"role": "assistant", "content": response})
            
            return response
        except Exception as e:
            return f"Erreur Nexus Core: {str(e)}"

    def generate_optimization_config(self, game_title, current_config, hardware_info):
        """Génère une config optimisée via l'IA."""
        if not self.client:
            return None
            
        system_prompt = (
            "You are a PC Optimization Expert AI. "
            "Your goal is to analyze a game configuration file and propose optimized values based on the user's hardware. "
            "You MUST return ONLY a valid JSON object with the exact same keys as the input, but with optimized values. "
            "Do not add comments, do not add markdown code blocks (```json). Just the raw JSON string. "
            "Focus on Stability and FPS."
        )
        
        user_prompt = (
            f"Game: {game_title}\n"
            f"Hardware: {json.dumps(hardware_info)}\n"
            f"Current Config: {json.dumps(current_config)}\n\n"
            "Provide the optimized JSON configuration."
        )
        
        try:
            completion = self.client.chat.completions.create(
                model=self.model_id,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3 # Low temperature for more deterministic/technical output
            )
            content = completion.choices[0].message.content.strip()
            # Cleanup potential markdown
            if content.startswith("```json"): content = content[7:]
            if content.endswith("```"): content = content[:-3]
            
            return json.loads(content)
        except Exception as e:
            logger.error(f"AI Optimization Error: {e}")
            return None

def load_key():
    config_path = "data/config.json"
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                return json.load(f).get("api_key")
        except:
            return None
    return None

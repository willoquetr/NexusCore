import logging
import json
import os
from datetime import datetime

# Dossier des logs
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Fichiers de sortie
TXT_LOG_FILE = os.path.join(LOG_DIR, "nexus_core.log")
JSONL_LOG_FILE = os.path.join(LOG_DIR, "nexus_events.jsonl")

class JsonlFormatter(logging.Formatter):
    """Formateur pour exporter en JSONL (JSON Lines)."""
    def format(self, record):
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "module": record.module,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)

def setup_logger():
    """Initialise le système de logging bi-format."""
    logger = logging.getLogger("NexusCore")
    logger.setLevel(logging.DEBUG)
    
    # Supprimer les handlers existants si déjà initialisé
    if logger.hasHandlers():
        logger.handlers.clear()

    # 1. Handler pour le fichier texte (.log) - Plus lisible
    txt_handler = logging.FileHandler(TXT_LOG_FILE, encoding="utf-8")
    txt_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(module)s] - %(message)s')
    txt_handler.setFormatter(txt_formatter)
    txt_handler.setLevel(logging.INFO)

    # 2. Handler pour le fichier JSONL (.jsonl) - Pour analyse automatique
    jsonl_handler = logging.FileHandler(JSONL_LOG_FILE, encoding="utf-8")
    jsonl_handler.setFormatter(JsonlFormatter())
    jsonl_handler.setLevel(logging.DEBUG)

    # 3. Console (optionnel, pour le dev)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(txt_formatter)
    console_handler.setLevel(logging.DEBUG)

    logger.addHandler(txt_handler)
    logger.addHandler(jsonl_handler)
    logger.addHandler(console_handler)

    return logger

# Instance globale
logger = setup_logger()

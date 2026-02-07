import google.generativeai as genai
import json
import os

def list_available_models():
    config_path = "data/config.json"
    if not os.path.exists(config_path):
        print("Erreur: data/config.json non trouvé")
        return

    with open(config_path, "r") as f:
        api_key = json.load(f).get("api_key")

    if not api_key:
        print("Erreur: Pas de clé API dans config.json")
        return

    genai.configure(api_key=api_key)
    
    print("Liste des modèles accessibles avec votre clé :")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")
    except Exception as e:
        print(f"Erreur lors de la récupération des modèles : {e}")

if __name__ == "__main__":
    list_available_models()

import json
import re
import os
from typing import Dict
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

load_dotenv()

# Liste officielle TMDB pour le contexte
TMDB_GENRES = """
Action=28, Aventure=12, Animation=16, Comédie=35, Crime=80, Documentaire=99, 
Drame=18, Famille=10751, Fantastique=14, Histoire=36, Horreur=27, Musique=10402, 
Mystère=9648, Romance=10749, Science-Fiction=878, Téléfilm=10770, Thriller=53, 
Guerre=10752, Western=37.
"""

# Prompt formaté spécifiquement pour Mistral Instruct
SYSTEM_INSTRUCTIONS = f"""
Tu es un moteur JSON pour API TMDB.
CONTEXTE :
{TMDB_GENRES}

RÈGLES JSON (Strictes):
- 'with_genres': IDs séparés par , (AND) ou | (OR).
- 'without_genres': IDs à exclure.
- 'sort_by': 'popularity.desc', 'vote_average.desc', 'primary_release_date.desc'.
- 'primary_release_date.gte': YYYY-MM-DD.

EXEMPLE:
User: "Western des années 60"
JSON: {{"with_genres": "37", "primary_release_date.gte": "1960-01-01", "primary_release_date.lte": "1969-12-31"}}

Réponds UNIQUEMENT le JSON. Rien d'autre.
"""

def get_tmdb_filters_from_mood(mood_text: str) -> Dict:
    token = os.getenv("HUGGINGFACE_API_TOKEN")
    if not token:
        print("[WARN] Pas de token HF.")
        return {}

    try:
        # On utilise Mistral v0.2 qui est très stable en gratuit
        client = InferenceClient(model="google/flan-t5-base", token=token)
        
        # Construction manuelle du prompt Mistral [INST]
        # Cela évite l'erreur "model not supported for chat"
        full_prompt = f"[INST] {SYSTEM_INSTRUCTIONS}\n\nRequete User: {mood_text} [/INST]"
        
        response_text = client.text_generation(
            full_prompt,
            max_new_tokens=200,
            temperature=0.1,
            return_full_text=False
        )
        
        # Nettoyage et Extraction JSON
        # On cherche le premier bloc qui ressemble à { ... }
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            clean_json = json_match.group(0)
            return json.loads(clean_json)
        
        print(f"[DEBUG IA] Réponse brute non JSON: {response_text}")
        return {}
        
    except Exception as e:
        print(f"[ERREUR IA] : {e}")
        return {}

if __name__ == "__main__":
    test_mood = "Un film de science-fiction psychologique des années 2000"
    print(f"Test: '{test_mood}'")
    result = get_tmdb_filters_from_mood(test_mood)
    print(f"Résultat JSON: {result}")
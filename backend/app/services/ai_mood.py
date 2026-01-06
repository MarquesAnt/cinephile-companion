import json
import re
import os
from typing import Dict
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION DU FALLBACK (Synonymes) ---
TMDB_KEYWORDS = {
    28: ['action', 'bagarre', 'combat', 'violent', 'guerre', 'bataille', 'arme', 'explosion', 'se batte'],
    35: ['drôle', 'rire', 'comédie', 'fun', 'léger', 'humoristique', 'comique', 'marrant'],
    27: ['peur', 'horreur', 'effrayant', 'sang', 'zombie', 'monstre', 'tueur', 'terrifiant', 'angoissant'],
    878: ['sf', 'science-fiction', 'espace', 'alien', 'futur', 'robot', 'vaisseau', 'planète'],
    18: ['triste', 'pleurer', 'émouvant', 'drame', 'sombre', 'dramatique', 'tragique'],
    10749: ['amour', 'romance', 'love', 'couple', 'romantique', 'sentimental'],
    16: ['dessin animé', 'animation', 'manga', 'pixar', 'disney', 'animé'],
    53: ['thriller', 'suspense', 'tension', 'mystère', 'policier', 'psychologique'],
    37: ['western', 'cowboy', 'far west'],
}

SYSTEM_INSTRUCTIONS = """
Tu es un expert API TMDB. Réponds UNIQUEMENT le JSON.
Règles : 'with_genres' (ids), 'primary_release_date.gte' (YYYY-MM-DD), 'sort_by'.
Genre IDs: Action=28, Horror=27, Comedy=35, Drama=18, Sci-Fi=878, Romance=10749.
Exemple: "Action 2022" -> {"with_genres": "28", "primary_release_date.gte": "2022-01-01"}
"""

def local_rule_based_analysis(text: str) -> Dict:
    """Fallback robuste : Analyse par mots-clés sans IA."""
    print(f"[FALLBACK] Analyse de : '{text}'")
    text_lower = text.lower()
    filters = {}
    genre_ids = []
    
    # 1. Recherche des genres via synonymes
    for genre_id, keywords in TMDB_KEYWORDS.items():
        if any(k in text_lower for k in keywords):
            genre_ids.append(str(genre_id))
    
    if genre_ids:
        filters['with_genres'] = ','.join(genre_ids)
    
    # 2. Gestion des dates (Années ou Décennies)
    # Ex: "2000" ou "années 80"
    year_match = re.search(r'\b(19|20)(\d{2})\b', text)
    if year_match:
        full_year = int(year_match.group(0))
        # Si c'est une année ronde (ex: 1980), on suppose une décennie par défaut ? 
        # Pour le MVP, on prend l'année exacte sauf si "années" est précisé avant.
        if "années" in text_lower:
            filters['primary_release_date.gte'] = f'{full_year}-01-01'
            filters['primary_release_date.lte'] = f'{full_year+9}-12-31'
        else:
            filters['primary_release_date.gte'] = f'{full_year}-01-01'
            filters['primary_release_date.lte'] = f'{full_year}-12-31'

    # Toujours un tri par défaut
    filters['sort_by'] = 'popularity.desc'
    return filters

def get_tmdb_filters_from_mood(mood_text: str) -> Dict:
    token = os.getenv("HUGGINGFACE_API_TOKEN")
    
    # Tentative IA (Mistral)
    if token:
        try:
            # ON UTILISE MISTRAL-v0.2 (Le plus fiable en gratuit)
            client = InferenceClient(model="mistralai/Mistral-7B-Instruct-v0.2", token=token)
            full_prompt = f"[INST] {SYSTEM_INSTRUCTIONS}\n\nRequete: {mood_text} [/INST]"
            
            # Utilisation de text_generation pour éviter les erreurs de type "Chat"
            response_text = client.text_generation(
                full_prompt, max_new_tokens=150, temperature=0.1, return_full_text=False
            )
            
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
                
        except Exception as e:
            print(f"[IA ERROR] : {e}")

    # Fallback si pas de token ou erreur IA
    return local_rule_based_analysis(mood_text)
import json
import re
import os
from typing import Dict, List
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

load_dotenv()

# Liste officielle TMDB pour le contexte IA
TMDB_GENRES = """
Action=28, Aventure=12, Animation=16, Comédie=35, Crime=80, Documentaire=99, 
Drame=18, Famille=10751, Fantastique=14, Histoire=36, Horreur=27, Musique=10402, 
Mystère=9648, Romance=10749, Science-Fiction=878, Téléfilm=10770, Thriller=53, 
Guerre=10752, Western=37.
"""

# Dictionnaire de synonymes pour le fallback (analyse locale)
TMDB_KEYWORDS = {
    28: ['action', 'bagarre', 'combat', 'violent', 'guerre', 'bataille', 'arme', 'explosion'],
    35: ['drôle', 'rire', 'comédie', 'fun', 'léger', 'humoristique', 'comique'],
    27: ['peur', 'horreur', 'effrayant', 'sang', 'zombie', 'monstre', 'tueur', 'terrifiant', 'angoissant'],
    878: ['sf', 'science-fiction', 'espace', 'alien', 'futur', 'robot', 'vaisseau', 'planète', 'extraterrestre'],
    18: ['triste', 'pleurer', 'émouvant', 'drame', 'sombre', 'dramatique', 'tragique'],
    10749: ['amour', 'romance', 'love', 'couple', 'romantique', 'sentimental'],
    16: ['dessin animé', 'animation', 'manga', 'pixar', 'disney', 'animé', 'cartoon'],
    12: ['aventure', 'expédition', 'quête', 'voyage', 'exploration'],
    53: ['thriller', 'suspense', 'tension', 'mystère', 'policier'],
    14: ['fantastique', 'magie', 'fantasy', 'sorcellerie', 'légende'],
    10752: ['guerre', 'militaire', 'soldat', 'conflit', 'bataille'],
    37: ['western', 'cowboy', 'far west', 'indien', 'désert'],
    80: ['crime', 'gangster', 'mafia', 'vol', 'braquage'],
    9648: ['mystère', 'énigme', 'secret', 'puzzle', 'détective'],
    10751: ['famille', 'enfant', 'jeunesse', 'parent'],
}

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


def local_rule_based_analysis(text: str) -> Dict:
    """
    Analyse locale basée sur des règles (fallback si l'IA échoue).
    Détecte les genres via mots-clés et les années/décennies via regex.
    
    Args:
        text: Texte de la requête utilisateur
    
    Returns:
        Dictionnaire de filtres TMDB
    """
    text_lower = text.lower()
    filters = {}
    genre_ids = []
    
    # Détection des genres par mots-clés
    for genre_id, keywords in TMDB_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                if genre_id not in genre_ids:
                    genre_ids.append(genre_id)
                break
    
    if genre_ids:
        filters['with_genres'] = ','.join(str(gid) for gid in genre_ids)
    
    # Détection des années
    # Pattern 1: Année simple (ex: 1990, 2010)
    year_match = re.search(r'\b(19|20)\d{2}\b', text)
    if year_match:
        year = int(year_match.group())
        filters['primary_release_date.gte'] = f'{year}-01-01'
        filters['primary_release_date.lte'] = f'{year}-12-31'
    else:
        # Pattern 2: Décennie (ex: "années 80", "années 90", "2000")
        # "années 90" = 1990, "années 80" = 1980, etc.
        decade_match = re.search(r'années?\s*(20|30|40|50|60|70|80|90)\b', text_lower)
        if decade_match:
            decade_num = int(decade_match.group(1))
            # Décennie dans les années 1900 ou 2000
            if decade_num < 50:  # 20-49 = 2000-2049 (on assume 2000)
                century = 2000
            else:  # 50-99 = 1950-1999
                century = 1900
            decade_start = century + decade_num
            decade_end = decade_start + 9
            filters['primary_release_date.gte'] = f'{decade_start}-01-01'
            filters['primary_release_date.lte'] = f'{decade_end}-12-31'
        else:
            # Pattern 3: "2000" ou "2010" comme décennie
            decade_year_match = re.search(r'\b(20\d{2})\b', text)
            if decade_year_match:
                year = int(decade_year_match.group(1))
                if year % 10 == 0:  # Année qui se termine par 0 = décennie
                    filters['primary_release_date.gte'] = f'{year}-01-01'
                    filters['primary_release_date.lte'] = f'{year+9}-12-31'
    
    # Tri par défaut
    filters['sort_by'] = 'popularity.desc'
    
    return filters


def get_tmdb_filters_from_mood(mood_text: str) -> Dict:
    """
    Traduit une description d'humeur utilisateur en filtres techniques TMDB.
    Essaie d'abord l'API Hugging Face, puis utilise le fallback local si échec.
    
    Args:
        mood_text: Description textuelle de l'humeur/recherche
    
    Returns:
        Dictionnaire de filtres TMDB (toujours au moins sort_by)
    """
    token = os.getenv("HUGGINGFACE_API_TOKEN")
    
    # Tentative avec l'IA si token disponible
    if token:
        try:
            print("[IA] Tentative de génération via Hugging Face...")
            client = InferenceClient(model="google/flan-t5-base", token=token)
            
            full_prompt = f"[INST] {SYSTEM_INSTRUCTIONS}\n\nRequete User: {mood_text} [/INST]"
            
            response_text = client.text_generation(
                full_prompt,
                max_new_tokens=200,
                temperature=0.1,
                return_full_text=False
            )
            
            # Extraction JSON
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                clean_json = json_match.group(0)
                filters = json.loads(clean_json)
                print("[IA] ✅ Filtres générés avec succès via IA")
                if 'sort_by' not in filters:
                    filters['sort_by'] = 'popularity.desc'
                return filters
            
            print("[IA] ⚠️ Réponse non-JSON reçue, passage au fallback")
            
        except Exception as e:
            print(f"[IA] ❌ Erreur API Hugging Face: {e}")
            print("[FALLBACK] Activation de l'analyse locale...")
    
    # Fallback: Analyse locale
    print("[FALLBACK] Analyse basée sur règles locales...")
    filters = local_rule_based_analysis(mood_text)
    print(f"[FALLBACK] ✅ Filtres générés: {filters}")
    
    # Garantie: Toujours retourner au moins un tri
    if not filters:
        filters = {'sort_by': 'popularity.desc'}
    
    return filters


if __name__ == "__main__":
    test_cases = [
        "Un film de science-fiction psychologique des années 2000",
        "Un film d'horreur drôle",
        "Comédie romantique",
        "Action des années 90",
    ]
    
    for test_mood in test_cases:
        print(f"\n{'='*60}")
        print(f"Test: '{test_mood}'")
        result = get_tmdb_filters_from_mood(test_mood)
        print(f"Résultat JSON: {result}")

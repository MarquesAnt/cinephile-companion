import os
import time
import requests
import google.generativeai as genai
from sqlmodel import Session, select
from dotenv import load_dotenv
from app.database import engine
from app.models.movie import Movie
from pathlib import Path

# --- CONFIGURATION & ENVIRONNEMENT ---
# Utilisation de pathlib pour être robuste quel que soit le dossier d'exécution
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

GENAI_KEY = os.getenv("GOOGLE_API_KEY")
TMDB_KEY = os.getenv("TMDB_API_KEY")

if not GENAI_KEY or not TMDB_KEY:
    raise ValueError("❌ CRITIQUE : Clés API manquantes dans le .env")

genai.configure(api_key=GENAI_KEY)

# --- PARAMÈTRES DE CURATION ---
SLEEP_TIME = 0.1       # Vitesse d'ingestion (ajuster si erreur 429)
MOVIES_PER_SLOT = 20   # Films par créneau (Genre x Époque)
WORLD_CINEMA_PAGES = 5 # Nombre de pages de films internationaux à récupérer (20 films/page)

# 1. Matrice des Genres (COMPLÈTE - 19 Genres)
GENRES = {
    "Action": 28,
    "Aventure": 12,
    "Animation": 16,
    "Comédie": 35,
    "Crime": 80,
    "Documentaire": 99,
    "Drame": 18,
    "Famille": 10751,
    "Fantastique": 14,
    "Histoire": 36,
    "Horreur": 27,
    "Musique": 10402,
    "Mystère": 9648,
    "Romance": 10749,
    "Science Fiction": 878,
    "Téléfilm": 10770,
    "Thriller": 53,
    "Guerre": 10752,
    "Western": 37
}

# 2. Matrice Temporelle (De l'âge d'or à aujourd'hui)
ERAS = [
    ("1950-01-01", "1959-12-31"), # Kurosawa, Hitchcock
    ("1960-01-01", "1969-12-31"), # Nouvelle Vague
    ("1970-01-01", "1979-12-31"), # New Hollywood
    ("1980-01-01", "1989-12-31"), # Blockbusters
    ("1990-01-01", "1999-12-31"), 
    ("2000-01-01", "2009-12-31"), 
    ("2010-01-01", "2019-12-31"), 
    ("2020-01-01", "2025-12-31"), 
]

def get_embedding(text: str):
    """Récupère l'embedding avec gestion d'erreur basique."""
    try:
        return genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type="retrieval_document"
        )['embedding']
    except Exception as e:
        print(f"   ⚠️ Erreur Embedding: {e}")
        return None

def process_and_save_movies(session, movies_list, source_tag="General"):
    """Fonction helper pour traiter une liste de films TMDB."""
    count = 0
    for m_data in movies_list:
        # A. Check doublon (Optimisation : Check DB avant tout traitement)
        if session.exec(select(Movie).where(Movie.tmdb_id == m_data['id'])).first():
            continue
        
        # B. Filtre Qualité Données
        if not m_data.get('overview'): 
            continue

        # C. Construction du texte sémantique enrichi
        year = m_data.get('release_date', 'Inconnue')[:4]
        # On inclut l'année et le titre dans le texte pour le RAG
        text_to_embed = f"Film de {year}. Titre: {m_data['title']}. Synopsis: {m_data['overview']}"
        
        vector = get_embedding(text_to_embed)
        
        if vector:
            movie = Movie(
                tmdb_id=m_data['id'],
                title=m_data['title'],
                overview=m_data['overview'],
                release_date=m_data.get('release_date'),
                poster_path=m_data.get('poster_path'),
                vote_average=m_data.get('vote_average'),
                vote_count=m_data.get('vote_count'),
                embedding=vector,
                is_ready=True
            )
            session.add(movie)
            count += 1
            print(f"   ✅ [{source_tag}] {year} - {m_data['title']}")
            time.sleep(SLEEP_TIME)
    
    # Commit par batch pour éviter de perdre trop de données si crash
    session.commit()
    return count

def fetch_and_vectorize():
    print("🚀 Démarrage de l'Ingestion 'Cinéphile Pro'...")
    
    with Session(engine) as session:
        total_ingested = 0
        
        # --- PHASE 1 : MATRICE GENRE X TEMPS ---
        for genre_name, genre_id in GENRES.items():
            for start_date, end_date in ERAS:
                era_label = start_date[:4]
                print(f"\n📅 Phase 1 : {genre_name} ({era_label}s)")
                
                url = (f"https://api.themoviedb.org/3/discover/movie?api_key={TMDB_KEY}"
                       f"&language=fr-FR&sort_by=popularity.desc"
                       f"&with_genres={genre_id}"
                       f"&primary_release_date.gte={start_date}"
                       f"&primary_release_date.lte={end_date}"
                       f"&vote_count.gte=200"     # Filtre popularité min
                       f"&vote_average.gte=6.0"   # Filtre qualité min
                       f"&page=1")
                
                try:
                    res = requests.get(url)
                    if res.status_code == 200:
                        movies = res.json().get('results', [])[:MOVIES_PER_SLOT]
                        total_ingested += process_and_save_movies(session, movies, source_tag=f"{genre_name} {era_label}")
                    else:
                        print(f"❌ Erreur API TMDB: {res.status_code}")
                except Exception as e:
                    print(f"❌ Exception réseau: {e}")

        # --- PHASE 2 : WORLD CINEMA (INTERNATIONAL GEMS) ---
        print("\n🌍 Phase 2 : World Cinema (Les pépites non-anglophones)")
        for page in range(1, WORLD_CINEMA_PAGES + 1):
            print(f"   extracting page {page}...")
            # Stratégie : On exclut l'anglais ('en') et on demande une note très élevée (>= 7.5)
            # Cela fait remonter Parasite, Spirited Away, Intouchables, City of God, etc.
            url = (f"https://api.themoviedb.org/3/discover/movie?api_key={TMDB_KEY}"
                   f"&language=fr-FR&sort_by=vote_count.desc" # Les plus connus d'abord (pour avoir les classiques)
                   f"&without_original_language=en"            # PAS d'anglais
                   f"&vote_average.gte=7.5"                    # Crème de la crème
                   f"&vote_count.gte=500"                      # Films validés par la critique mondiale
                   f"&page={page}")
            
            try:
                res = requests.get(url)
                if res.status_code == 200:
                    movies = res.json().get('results', [])
                    total_ingested += process_and_save_movies(session, movies, source_tag="World")
                else:
                    print(f"❌ Erreur API TMDB (World): {res.status_code}")
            except Exception as e:
                print(f"❌ Exception réseau (World): {e}")

        print(f"\n🏁 Terminé ! {total_ingested} nouveaux films ajoutés à la collection.")

if __name__ == "__main__":
    # Petit check de sécurité
    if not os.path.exists("cinephile.db") and not os.getenv("DATABASE_URL"):
        print("⚠️ Attention : cinephile.db introuvable. Une nouvelle DB sera créée.")
    
    fetch_and_vectorize()
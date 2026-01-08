import os
import time
import requests
import google.generativeai as genai
from sqlmodel import Session, select
from dotenv import load_dotenv
from app.database import engine
from app.models.movie import Movie
from pathlib import Path

# 1. Chargement des clés depuis le fichier .env
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

GENAI_KEY = os.getenv("GOOGLE_API_KEY")
TMDB_KEY = os.getenv("TMDB_API_KEY")

# Sécurité : On vérifie que les clés sont là
if not GENAI_KEY or not TMDB_KEY:
    raise ValueError("❌ CRITIQUE : Clés API manquantes dans le .env")

# Configuration de Gemini avec ta clé
genai.configure(api_key=GENAI_KEY)

# Paramètres
TARGET_MOVIES = 50   # On ne prend que 50 films pour le test
SLEEP_TIME = 4.5     # Pause de 4.5s entre chaque film (pour ne pas être bloqué par Google)
TMDB_BASE_URL = "https://api.themoviedb.org/3"

def get_embedding(text: str):
    """Envoie le texte à Google et récupère le vecteur"""
    try:
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type="retrieval_document"
        )
        return result['embedding']
    except Exception as e:
        print(f"⚠️ Erreur Embedding: {e}")
        return None

def fetch_and_vectorize():
    print("🚀 Démarrage de l'ingestion...")
    
    # On ouvre la connexion à la base de données
    with Session(engine) as session:
        count = 0
        page = 1
        
        while count < TARGET_MOVIES:
            # A. Téléchargement depuis TMDB
            print(f"📥 Téléchargement Page {page}...")
            url = f"{TMDB_BASE_URL}/movie/popular?api_key={TMDB_KEY}&language=fr-FR&page={page}"
            response = requests.get(url)
            
            if response.status_code != 200:
                print(f"❌ Erreur TMDB: {response.text}")
                break
                
            movies_data = response.json().get('results', [])
            
            for m_data in movies_data:
                if count >= TARGET_MOVIES: break
                
                # B. Vérification doublon (pour ne pas l'ajouter 2 fois)
                existing = session.exec(select(Movie).where(Movie.tmdb_id == m_data['id'])).first()
                if existing:
                    print(f"⏭️  Déjà en base : {m_data['title']}")
                    continue

                # C. Préparation du texte (Titre + Résumé)
                text_to_embed = f"Titre: {m_data['title']}. Synopsis: {m_data['overview']}"
                
                if not m_data['overview']:
                    continue # On saute les films sans résumé

                # D. Appel à l'IA (Vectorisation)
                print(f"🧠 Vectorisation : {m_data['title']}...")
                vector = get_embedding(text_to_embed)
                
                if vector:
                    # E. Enregistrement dans la DB
                    movie = Movie(
                        tmdb_id=m_data['id'],
                        title=m_data['title'],
                        overview=m_data['overview'],
                        release_date=m_data.get('release_date'),
                        poster_path=m_data.get('poster_path'),
                        vote_average=m_data.get('vote_average', 0),
                        vote_count=m_data.get('vote_count', 0),
                        embedding=vector, # <-- C'est ici qu'on stocke le vecteur
                        is_ready=True
                    )
                    session.add(movie)
                    session.commit()
                    count += 1
                    
                    # F. La Pause de sécurité
                    print(f"✅ Sauvegardé ({count}/{TARGET_MOVIES}). Pause de {SLEEP_TIME}s...")
                    time.sleep(SLEEP_TIME)
                else:
                    print("❌ Échec vectorisation.")
            
            page += 1

    print("🏁 Ingestion terminée avec succès.")

if __name__ == "__main__":
    fetch_and_vectorize()
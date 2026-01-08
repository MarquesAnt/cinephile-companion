import os
import asyncio
from typing import List, Set, Optional
import google.generativeai as genai
from sqlmodel import Session, select
from dotenv import load_dotenv

# --- Architecture Async ---
from app.services import tmdb
from app.core.constants import PROVIDER_MAPPING

# --- RAG ---
from app.database import engine
from app.models.movie import Movie

load_dotenv()
GENAI_KEY = os.getenv("GOOGLE_API_KEY")

if GENAI_KEY:
    genai.configure(api_key=GENAI_KEY)

# ==========================================
# PARTIE 1 : FILTRE PAR PLATEFORME 
# ==========================================

def get_common_providers(user_providers: List[List[str]]) -> Set[str]:
    """Calcule l'union des providers de tous les utilisateurs."""
    if not user_providers:
        return set()
    
    union_providers = set()
    for providers_list in user_providers:
        union_providers.update(providers_list)
    
    return union_providers

async def filter_movies_by_availability(movies: List[dict], user_providers: List[List[str]], country_code: str = "FR") -> List[dict]:
    """Filtre les films selon leur disponibilité (Async)."""
    common_providers = get_common_providers(user_providers)
    
    if not common_providers:
        return []
    
    tasks = [
        tmdb.get_movie_providers(movie["id"], country_code)
        for movie in movies
    ]
    
    movie_providers_list = await asyncio.gather(*tasks, return_exceptions=True)
    
    available_movies = []
    for movie, movie_providers in zip(movies, movie_providers_list):
        if isinstance(movie_providers, Exception):
            continue
        
        movie_providers_set = set(movie_providers)
        intersection = movie_providers_set.intersection(common_providers)
        
        if intersection:
            movie_copy = movie.copy()
            movie_copy["available_on"] = sorted(list(intersection))
            available_movies.append(movie_copy)
    
    return available_movies

# ==========================================
# PARTIE 2 : MOTEUR DE RECHERCHE IA (RAG) 
# ==========================================

def _get_embedding_sync(text: str) -> Optional[List[float]]:
    """Version bloquante interne de l'appel Gemini."""
    if not GENAI_KEY:
        print("⚠️ Erreur : Pas de clé API Google configurée.")
        return None
    try:
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type="retrieval_query"
        )
        return result['embedding']
    except Exception as e:
        print(f"⚠️ Erreur Embedding: {e}")
        return None

def _search_db_sync(vector: List[float], limit: int) -> List[Movie]:
    """Version bloquante interne de la requête DB."""
    with Session(engine) as session:
        statement = (
            select(Movie)
            .order_by(Movie.embedding.cosine_distance(vector))
            .limit(limit)
        )
        return session.exec(statement).all()

async def find_similar_movies(user_query: str, limit: int = 5) -> List[Movie]:
    """
    Wrapper ASYNC : Rend les opérations lourdes (IA + DB) non-bloquantes
    pour ne pas figer l'API FastAPI.
    """
    print(f"🧠 Analyse de la requête (Async) : '{user_query}'...")
    
    # 1. On déporte l'appel Gemini dans un thread séparé
    query_vector = await asyncio.to_thread(_get_embedding_sync, user_query)
    
    if not query_vector:
        return []

    # 2. On déporte la requête SQL dans un thread séparé
    # (Solution temporaire propre avant de passer à asyncpg)
    results = await asyncio.to_thread(_search_db_sync, query_vector, limit)
    
    return results

# ==========================================
# TEST UNITAIRE ASYNC
# ==========================================
if __name__ == "__main__":
    async def main_test():
        print("--- TEST DU MOTEUR RAG (ASYNC) ---")
        try:
            phrase_test = "Un film de science fiction avec des robots tueurs"
            # Note le 'await' ici
            films = await find_similar_movies(phrase_test, limit=3)
            
            print(f"\nRésultats pour : '{phrase_test}'")
            if films:
                for film in films:
                    print(f"🎬 {film.title}")
            else:
                print("Aucun film trouvé.")

        except Exception as e:
            print(f"❌ Erreur critique : {e}")

    asyncio.run(main_test())
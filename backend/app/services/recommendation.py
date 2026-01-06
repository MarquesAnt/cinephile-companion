import asyncio
from typing import List, Set
from app.services import tmdb
from app.core.constants import PROVIDER_MAPPING


def get_common_providers(user_providers: List[List[str]]) -> Set[str]:
    """
    Calcule l'union des providers de tous les utilisateurs.
    Logique: Si l'un de nous a le compte, on peut regarder ce catalogue.
    
    Args:
        user_providers: Liste de listes de providers (ex: [['Netflix'], ['Netflix', 'Prime']])
    
    Returns:
        Set des providers disponibles (union de tous les providers)
    """
    if not user_providers:
        return set()
    
    union_providers = set()
    for providers_list in user_providers:
        union_providers.update(providers_list)
    
    return union_providers


async def filter_movies_by_availability(movies: List[dict], user_providers: List[List[str]], country_code: str = "FR") -> List[dict]:
    """
    Filtre les films selon leur disponibilité sur les providers des utilisateurs.
    
    Args:
        movies: Liste de dictionnaires de films avec au moins 'id'
        user_providers: Liste de listes de providers par utilisateur
        country_code: Code pays pour la recherche de providers (défaut: "FR")
    
    Returns:
        Liste de films disponibles, enrichis avec 'available_on'
    """
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


if __name__ == "__main__":
    async def test():
        try:
            user_a_providers = ["Netflix"]
            user_b_providers = ["Amazon Prime Video"]
            user_providers = [user_a_providers, user_b_providers]
            
            print(f"User A: {user_a_providers}")
            print(f"User B: {user_b_providers}")
            
            common_providers = get_common_providers(user_providers)
            print(f"Union des providers: {common_providers}")
            
            provider_ids = [
                PROVIDER_MAPPING[provider]
                for provider in common_providers
                if provider in PROVIDER_MAPPING
            ]
            
            print(f"Provider IDs: {provider_ids}")
            
            movies = await tmdb.discover_movies_by_providers(provider_ids, page=1)
            print(f"\nFilms disponibles (filtrés côté serveur): {len(movies)}")
            
            for movie in movies:
                print(f"{movie['title']} (ID: {movie['id']})")
        except Exception as e:
            print(f"Erreur: {e}")
    
    asyncio.run(test())


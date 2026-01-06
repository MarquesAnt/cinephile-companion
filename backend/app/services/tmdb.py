import os
import asyncio
from typing import List
import httpx
from dotenv import load_dotenv

load_dotenv()

TMDB_BASE_URL = "https://api.themoviedb.org/3"


def _get_access_token() -> str:
    """Récupère et valide le token d'accès TMDB depuis les variables d'environnement."""
    token = os.getenv("TMDB_ACCESS_TOKEN")
    if not token:
        raise ValueError(
            "TMDB_ACCESS_TOKEN est manquant. "
            "Définissez la variable d'environnement avec votre Read Access Token TMDB."
        )
    return token


async def get_movie_providers(movie_id: int, country_code: str = "FR") -> List[str]:
    """
    Récupère la liste des providers de streaming (flatrate) pour un film donné.
    
    Args:
        movie_id: L'ID du film dans TMDB
        country_code: Code pays ISO 3166-1 (défaut: "FR")
    
    Returns:
        Liste des noms de providers (ex: ["Netflix", "Disney Plus"])
    
    Raises:
        ValueError: Si TMDB_ACCESS_TOKEN est manquant
        httpx.HTTPStatusError: Si la requête échoue (404, etc.)
        httpx.RequestError: En cas d'erreur réseau
    """
    access_token = _get_access_token()
    url = f"{TMDB_BASE_URL}/movie/{movie_id}/watch/providers"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            results = data.get("results", {})
            country_data = results.get(country_code.upper(), {})
            flatrate = country_data.get("flatrate", [])
            
            providers = [provider.get("provider_name") for provider in flatrate if provider.get("provider_name")]
            return providers
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise httpx.HTTPStatusError(
                    f"Film avec l'ID {movie_id} non trouvé dans TMDB",
                    request=e.request,
                    response=e.response
                )
            raise
        except httpx.RequestError as e:
            raise httpx.RequestError(f"Erreur réseau lors de l'appel à l'API TMDB: {e}") from e


async def search_movies(query: str) -> List[dict]:
    """
    Recherche des films via l'API TMDB.
    
    Args:
        query: Terme de recherche
    
    Returns:
        Liste de dictionnaires avec les champs: id, title, release_date, poster_path
    
    Raises:
        ValueError: Si TMDB_ACCESS_TOKEN est manquant
        httpx.HTTPStatusError: Si la requête échoue
        httpx.RequestError: En cas d'erreur réseau
    """
    access_token = _get_access_token()
    url = f"{TMDB_BASE_URL}/search/movie"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    
    params = {
        "query": query,
        "language": "fr-FR"
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            results = data.get("results", [])
            
            movies = [
                {
                    "id": movie.get("id"),
                    "title": movie.get("title", ""),
                    "release_date": movie.get("release_date", ""),
                    "poster_path": movie.get("poster_path", "")
                }
                for movie in results
                if movie.get("id")
            ]
            
            return movies
            
        except httpx.HTTPStatusError as e:
            raise httpx.HTTPStatusError(
                f"Erreur lors de la recherche de films: {e}",
                request=e.request,
                response=e.response
            ) from e
        except httpx.RequestError as e:
            raise httpx.RequestError(f"Erreur réseau lors de l'appel à l'API TMDB: {e}") from e


async def get_popular_movies(page: int = 1) -> List[dict]:
    """
    Récupère les films populaires via l'API TMDB.
    
    Args:
        page: Numéro de page (défaut: 1)
    
    Returns:
        Liste de dictionnaires avec les champs: id, title, release_date, poster_path
    
    Raises:
        ValueError: Si TMDB_ACCESS_TOKEN est manquant
        httpx.HTTPStatusError: Si la requête échoue
        httpx.RequestError: En cas d'erreur réseau
    """
    access_token = _get_access_token()
    url = f"{TMDB_BASE_URL}/movie/popular"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    
    params = {
        "page": page,
        "language": "fr-FR"
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            results = data.get("results", [])
            
            movies = [
                {
                    "id": movie.get("id"),
                    "title": movie.get("title", ""),
                    "release_date": movie.get("release_date", ""),
                    "poster_path": movie.get("poster_path", "")
                }
                for movie in results
                if movie.get("id")
            ]
            
            return movies
            
        except httpx.HTTPStatusError as e:
            raise httpx.HTTPStatusError(
                f"Erreur lors de la récupération des films populaires: {e}",
                request=e.request,
                response=e.response
            ) from e
        except httpx.RequestError as e:
            raise httpx.RequestError(f"Erreur réseau lors de l'appel à l'API TMDB: {e}") from e


async def discover_movies_by_providers(provider_ids: List[int], page: int = 1) -> List[dict]:
    """
    Découvre des films filtrés par providers via l'API TMDB (Server-Side Filtering).
    
    Args:
        provider_ids: Liste des IDs de providers (ex: [8, 119] pour Netflix et Prime)
        page: Numéro de page (défaut: 1)
    
    Returns:
        Liste de dictionnaires avec les champs: id, title, release_date, poster_path
    
    Raises:
        ValueError: Si TMDB_ACCESS_TOKEN est manquant ou si provider_ids est vide
        httpx.HTTPStatusError: Si la requête échoue
        httpx.RequestError: En cas d'erreur réseau
    """
    if not provider_ids:
        raise ValueError("provider_ids ne peut pas être vide")
    
    access_token = _get_access_token()
    url = f"{TMDB_BASE_URL}/discover/movie"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    
    providers_string = "|".join(str(pid) for pid in provider_ids)
    
    params = {
        "language": "fr-FR",
        "sort_by": "popularity.desc",
        "watch_region": "FR",
        "with_watch_providers": providers_string,
        "page": page
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            results = data.get("results", [])
            
            seen_ids = set()
            movies = []
            for movie in results:
                movie_id = movie.get("id")
                if movie_id and movie_id not in seen_ids:
                    seen_ids.add(movie_id)
                    movies.append({
                        "id": movie_id,
                        "title": movie.get("title", ""),
                        "release_date": movie.get("release_date", ""),
                        "poster_path": movie.get("poster_path", "")
                    })
            
            return movies
            
        except httpx.HTTPStatusError as e:
            raise httpx.HTTPStatusError(
                f"Erreur lors de la découverte de films par providers: {e}",
                request=e.request,
                response=e.response
            ) from e
        except httpx.RequestError as e:
            raise httpx.RequestError(f"Erreur réseau lors de l'appel à l'API TMDB: {e}") from e


if __name__ == "__main__":
    async def test():
        try:
            query = "Interstellar"
            movies = await search_movies(query)
            print(f"Résultats de recherche pour '{query}': {len(movies)} films trouvés")
            
            if movies:
                first_movie = movies[0]
                print(f"\nPremier résultat: {first_movie['title']} (ID: {first_movie['id']})")
                
                providers = await get_movie_providers(first_movie['id'], "FR")
                print(f"Providers disponibles: {providers}")
            else:
                print("Aucun film trouvé")
        except Exception as e:
            print(f"Erreur: {e}")
    
    asyncio.run(test())


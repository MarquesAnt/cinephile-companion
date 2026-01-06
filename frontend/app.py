import sys
import os
import asyncio
import httpx
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from backend.app.services import tmdb
from backend.app.services import ai_mood
from backend.app.core.constants import PROVIDER_MAPPING

st.set_page_config(
    page_title="Ciné-Compagnon",
    page_icon="🎬",
    layout="wide"
)

TMDB_LOGO_URL = "https://www.themoviedb.org/assets/2/v4/logos/v2/blue_short.svg"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"


def run_async(coro):
    """Helper pour exécuter des fonctions async dans Streamlit."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


def display_movies(movies):
    """Affiche une grille de films."""
    if not movies:
        st.info("Aucun film trouvé.")
        return
    
    cols = st.columns(4)
    for idx, movie in enumerate(movies):
        col = cols[idx % 4]
        
        with col:
            poster_path = movie.get("poster_path", "")
            title = movie.get("title", "Sans titre")
            release_date = movie.get("release_date", "")
            year = release_date[:4] if release_date else "N/A"
            
            if poster_path:
                image_url = f"{TMDB_IMAGE_BASE_URL}{poster_path}"
                st.image(image_url, use_container_width=True)
            else:
                st.image("https://via.placeholder.com/500x750?text=No+Poster", use_container_width=True)
            
            st.markdown(f"**{title}**")
            if year != "N/A":
                st.caption(f"Année: {year}")


async def discover_with_ai_filters(provider_ids, ai_filters):
    """Combine les filtres IA avec les providers pour découvrir des films."""
    import os
    from backend.app.services.tmdb import TMDB_BASE_URL
    
    access_token = os.getenv("TMDB_ACCESS_TOKEN")
    if not access_token:
        raise ValueError("TMDB_ACCESS_TOKEN manquant")
    
    url = f"{TMDB_BASE_URL}/discover/movie"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    
    providers_string = "|".join(str(pid) for pid in provider_ids)
    
    params = {
        "language": "fr-FR",
        "watch_region": "FR",
        "with_watch_providers": providers_string,
        "page": 1
    }
    
    params.update(ai_filters)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
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


st.title("🎬 Ciné-Compagnon")
st.markdown("### Trouvez le film parfait pour votre soirée")

with st.sidebar:
    st.header("Mes Plateformes")
    
    provider_names = list(PROVIDER_MAPPING.keys())
    selected_providers = st.multiselect(
        "Sélectionnez vos plateformes de streaming",
        provider_names,
        default=["Netflix", "Amazon Prime Video"]
    )
    
    provider_ids = [PROVIDER_MAPPING[p] for p in selected_providers if p in PROVIDER_MAPPING]

tab1, tab2 = st.tabs(["🔮 Recherche Magique (IA)", "🔍 Par Titre"])

with tab1:
    st.subheader("Laissez l'IA trouver votre film")
    
    mood_text = st.text_input(
        "Quelle est votre envie ce soir ?",
        placeholder="Ex: Un film d'horreur spatial"
    )
    
    if st.button("Trouver", type="primary"):
        if not mood_text:
            st.warning("Veuillez saisir votre envie.")
        elif not provider_ids:
            st.warning("Veuillez sélectionner au moins une plateforme.")
        else:
            with st.spinner("L'IA analyse votre demande..."):
                ai_filters = ai_mood.get_tmdb_filters_from_mood(mood_text)
                
                if not ai_filters:
                    st.error("Erreur lors de l'analyse par l'IA. Veuillez réessayer.")
                else:
                    st.success("Filtres générés par l'IA:")
                    st.json(ai_filters)
                    
                    with st.spinner("Recherche des films..."):
                        try:
                            movies = run_async(discover_with_ai_filters(provider_ids, ai_filters))
                            st.subheader(f"🎯 {len(movies)} films trouvés")
                            display_movies(movies)
                        except Exception as e:
                            st.error(f"Erreur lors de la recherche: {e}")

with tab2:
    st.subheader("Recherche par titre")
    
    search_query = st.text_input(
        "Titre du film",
        placeholder="Ex: Inception"
    )
    
    if st.button("Chercher", type="primary"):
        if not search_query:
            st.warning("Veuillez saisir un titre.")
        else:
            with st.spinner("Recherche en cours..."):
                try:
                    movies = run_async(tmdb.search_movies(search_query))
                    st.subheader(f"🔍 {len(movies)} résultats")
                    display_movies(movies)
                except Exception as e:
                    st.error(f"Erreur lors de la recherche: {e}")

st.markdown("---")

footer_col1, footer_col2 = st.columns([1, 4])

with footer_col1:
    st.image(TMDB_LOGO_URL, width=150)

with footer_col2:
    st.markdown(
        """
        <p style='margin-top: 20px; font-size: 12px; color: #666;'>
        This product uses the TMDB API but is not endorsed or certified by TMDB.
        </p>
        """,
        unsafe_allow_html=True
    )


import sys
import asyncio
import httpx
from pathlib import Path

# Ajout du chemin parent pour importer backend
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from backend.app.services import tmdb
from backend.app.services import ai_mood
from backend.app.core.constants import PROVIDER_MAPPING

st.set_page_config(page_title="Ciné-Compagnon", page_icon="🎬", layout="wide")

# URL de base TMDB
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"

def run_async(coro):
    """Helper async pour Streamlit"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

def display_movies(movies):
    """Affiche la grille de films avec gestion d'erreurs d'image."""
    if not movies:
        st.info("Aucun film trouvé pour ces critères.")
        return
    
    cols = st.columns(5) # 5 colonnes pour plus de densité
    for idx, movie in enumerate(movies):
        col = cols[idx % 5]
        with col:
            # Gestion sécurisée de l'image
            poster_path = movie.get("poster_path") # Peut être None
            
            if poster_path and poster_path.startswith("/"):
                image_url = f"{TMDB_IMAGE_BASE_URL}{poster_path}"
                st.image(image_url, use_container_width=True)
            else:
                # Placeholder si pas d'image
                st.image("https://via.placeholder.com/500x750?text=No+Image", use_container_width=True)
            
            st.write(f"**{movie.get('title', 'Sans titre')}**")
            
            date = movie.get('release_date', '')
            if date:
                st.caption(f"📅 {date[:4]}")

async def discover_with_ai_filters(provider_ids, ai_filters):
    # (Le code de cette fonction reste identique à ta version précédente, 
    # assure-toi juste d'avoir les imports corrects si tu as copié partiellement)
    from backend.app.services.tmdb import TMDB_BASE_URL
    import os
    
    token = os.getenv("TMDB_ACCESS_TOKEN")
    url = f"{TMDB_BASE_URL}/discover/movie"
    
    providers_string = "|".join(str(pid) for pid in provider_ids)
    params = {
        "language": "fr-FR",
        "watch_region": "FR",
        "with_watch_providers": providers_string,
        "page": 1,
        # On fusionne les filtres IA ici
        **ai_filters 
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers={"Authorization": f"Bearer {token}"}, params=params)
        resp.raise_for_status()
        return resp.json().get("results", [])

# --- INTERFACE ---

st.title("🎬 Ciné-Compagnon")

with st.sidebar:
    st.header("1. Vos Plateformes")
    selected_providers = st.multiselect(
        "Abonnements disponibles :",
        list(PROVIDER_MAPPING.keys()),
        default=["Netflix", "Amazon Prime Video"]
    )
    # Conversion en IDs
    user_provider_ids = [PROVIDER_MAPPING[p] for p in selected_providers]

st.header("2. Qu'est-ce qu'on regarde ?")

mood_text = st.text_input("Décrivez votre envie (ex: 'Un film de guerre qui fait pleurer', 'Comédie années 90')")

if st.button("Trouver le film parfait", type="primary"):
    if not mood_text:
        st.warning("Écrivez quelque chose d'abord !")
    else:
        with st.spinner("L'IA analyse votre demande..."):
            # 1. Appel du service IA (ou Fallback)
            ai_filters = ai_mood.get_tmdb_filters_from_mood(mood_text)
            
            # --- DEBUG BOX (Pour voir si le fallback marche) ---
            with st.expander("🕵️ Debug - Voir ce que l'IA a compris"):
                st.json(ai_filters)
            # ---------------------------------------------------

            # 2. Recherche TMDB
            if user_provider_ids:
                try:
                    raw_movies = run_async(discover_with_ai_filters(user_provider_ids, ai_filters))
                    st.success(f"Top résultats trouvés : {len(raw_movies)}")
                    display_movies(raw_movies)
                except Exception as e:
                    st.error(f"Erreur technique TMDB : {e}")
            else:
                st.error("Sélectionnez au moins une plateforme !")
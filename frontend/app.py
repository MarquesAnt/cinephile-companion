import streamlit as st
import requests

# --- CONFIGURATION ---
API_URL = "http://127.0.0.1:8000"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"

st.set_page_config(
    page_title="Cinéphile Companion",
    page_icon="🎬",
    layout="wide"
)

# --- CSS CUSTOM ---
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        background-color: #E50914; 
        color: white;
        border: none;
        font-weight: bold;
    }
    .provider-badge {
        background-color: #46d369;
        color: black;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.8em;
        font-weight: bold;
        margin-right: 4px;
        display: inline-block;
        margin-bottom: 4px;
    }
</style>
""", unsafe_allow_html=True)

# --- FONCTIONS ---
def search_movies_api(query, providers):
    """Appelle l'API avec query ET providers"""
    try:
        payload = {
            "query": query,
            "providers": providers
        }
        response = requests.post(
            f"{API_URL}/search",
            json=payload, # On envoie le payload complet
            timeout=15 # Timeout un peu plus long car TMDB fetch en temps réel
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Erreur API ({response.status_code})")
            return []
    except Exception as e:
        st.error(f"Erreur technique : {e}")
        return []

# --- SIDEBAR ---
with st.sidebar:
    st.title("Cinéphile Companion")
    st.write("### Vos Préférences")
    
    # Liste de providers statique pour le MVP
    # Idéalement, cette liste viendrait du backend aussi
    selected_providers = st.multiselect(
        "Vos abonnements :",
        ["Netflix", "Amazon Prime Video", "Disney+", "Canal+", "Apple TV+"],
        default=["Netflix", "Amazon Prime Video"]
    )
    
    st.info(f"Filtre actif : {len(selected_providers)} plateformes")

# --- MAIN PAGE ---
st.markdown("## Que voulez-vous regarder ce soir ?")
query = st.text_input("Recherche", placeholder="Ex: Un film de SF psychologique...")

if st.button("Trouver le film parfait"):
    if not query:
        st.warning("Décrivez vos envies !")
    else:
        with st.spinner("Recherche sémantique & vérification des disponibilités..."):
            results = search_movies_api(query, selected_providers)
            
            if results:
                st.success(f"{len(results)} films trouvés !")
                cols = st.columns(3)
                
                for idx, movie in enumerate(results):
                    with cols[idx % 3]:
                        with st.container():
                            # Poster
                            img_url = f"{TMDB_IMAGE_BASE_URL}{movie['poster_path']}" if movie.get('poster_path') else "https://via.placeholder.com/500x750?text=No+Poster"
                            st.image(img_url, use_container_width=True)
                            
                            # Titre
                            st.subheader(movie["title"])
                            
                            # Badges de disponibilité
                            if movie.get("available_on"):
                                badges_html = ""
                                for p in movie["available_on"]:
                                    badges_html += f'<span class="provider-badge">{p}</span>'
                                st.markdown(badges_html, unsafe_allow_html=True)
                            else:
                                st.caption("Non disponible sur vos plateformes (ou info manquante)")

                            # Note et Synthèse
                            st.caption(f"⭐ {movie['vote_average']}/10")
                            with st.expander("Synopsis"):
                                st.write(movie["overview"])
            else:
                st.warning("Aucun film correspondant trouvé sur vos plateformes.")
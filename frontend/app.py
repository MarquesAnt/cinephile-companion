import streamlit as st
import requests

# --- CONFIGURATION ---
API_URL = "http://127.0.0.1:8000"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"
TMDB_LOGO_URL = "https://www.themoviedb.org/assets/2/v4/logos/v2/blue_short-8e7b30f73a4020692ccca9c88bafe5dcb6f8a62a4c6bc55cd9ba82bb2cd95f6c.svg"

st.set_page_config(
    page_title="Cinéphile Companion",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
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
    .stButton>button:hover {
        background-color: #B20710;
        color: white;
    }
    .footer-text {
        font-size: 12px;
        color: #888;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# --- FONCTIONS ---
def search_movies_api(query):
    """Appelle notre API FastAPI Backend"""
    try:
        response = requests.post(
            f"{API_URL}/search",
            json={"query": query},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Erreur API ({response.status_code}) : {response.text}")
            return []
    except requests.exceptions.ConnectionError:
        st.error("Impossible de contacter le Backend. Vérifiez que le serveur tourne sur le port 8000.")
        return []
    except Exception as e:
        st.error(f"Erreur technique : {e}")
        return []

# --- SIDEBAR ---
with st.sidebar:
    st.title("Cinéphile Companion")
    st.markdown("---")
    
    st.write("### Vos Préférences")
    providers = st.multiselect(
        "Vos plateformes :",
        ["Netflix", "Amazon Prime", "Disney+", "Canal+"],
        default=["Netflix", "Amazon Prime"]
    )
    
    st.caption("Mode MVP : Recherche IA active. Le filtre plateforme sera activé prochainement.")

# --- MAIN PAGE ---
st.markdown("## Que voulez-vous regarder ce soir ?")
st.markdown("Décrivez votre **envie du moment**.")

# Zone de recherche
query = st.text_input(
    label="Recherche",
    placeholder="Ex: Un film de science-fiction psychologique avec une fin tordue...",
    label_visibility="collapsed"
)

if st.button("Trouver le film parfait"):
    if not query:
        st.warning("Décrivez d'abord vos envies !")
    else:
        with st.spinner("Analyse de la demande..."):
            results = search_movies_api(query)
            
            if results:
                st.success(f"{len(results)} recommandations trouvées :")
                st.markdown("---")
                
                # Affichage en grille (3 colonnes)
                cols = st.columns(3)
                
                for idx, movie in enumerate(results):
                    with cols[idx % 3]:
                        with st.container():
                            # Image
                            if movie.get("poster_path"):
                                st.image(
                                    f"{TMDB_IMAGE_BASE_URL}{movie['poster_path']}", 
                                    use_container_width=True
                                )
                            else:
                                st.image("https://via.placeholder.com/500x750?text=No+Poster", use_container_width=True)
                            
                            # Titre et Note
                            st.subheader(movie["title"])
                            st.caption(f"Note : {movie['vote_average']}/10")
                            
                            # Synopsis
                            with st.expander("Lire le synopsis"):
                                st.write(movie["overview"])
                                
            else:
                st.warning("Aucun film ne correspond assez à votre demande dans notre base actuelle.")

# --- FOOTER ---
st.markdown("---")
st.markdown(f"""
<div style="text-align: center;">
    <img src="{TMDB_LOGO_URL}" width="100">
    <p class="footer-text">
        This product uses the TMDB API but is not endorsed or certified by TMDB.<br>
        Propulsé par FastAPI, PostgreSQL pgvector & Google Gemini
    </p>
</div>
""", unsafe_allow_html=True)
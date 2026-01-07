# 🎬 Ciné-Compagnon (Cinephile Companion)

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://TON-URL-STREAMLIT-ICI)
[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)

**Fini la paralysie du choix.** Ciné-Compagnon transforme la consommation passive de streaming en une expérience active et sociale. L'application croise vos envies (Mood) avec la réalité de vos abonnements (Netflix, Prime, etc.) en temps réel.

---

## ⚡ Features Clés

### 1. Disponibilité Croisée (Core Feature)
Ne perdez plus 20 minutes à chercher un film pour réaliser qu'il n'est pas disponible.
* **Filtrage temps réel :** L'app n'affiche QUE les films disponibles sur VOS plateformes combinées.
* **Check "Qui est là ?" :** (En cours) Gère les intersections d'abonnements entre amis présents.

### 2. Recherche Hybride
* **🧠 Mode Mood (IA) :** "Je veux un film de guerre des années 90 qui fait pleurer". Notre moteur traduit le langage naturel en filtres techniques TMDB.
* **🔎 Mode Pragmatique :** Recherche par titre avec vérification immédiate de la disponibilité dans *vos* abonnements vs le reste du marché.

### 3. Gamification (Roadmap)
* Défis cinéphiles ("Voir 5 Westerns").
* Sortie de la zone de confort via des suggestions curatées.

---

## 🛠️ Stack Technique

Architecture modulaire orientée micro-services (MVP).

* **Backend :** FastAPI (Python) - Validation stricte via Pydantic.
* **Frontend :** Streamlit - Itération rapide UI/UX.
* **Data Source :** TMDB API (The Movie Database).
* **Infrastructure :** Docker & DevContainers.

---

## 🚀 Installation & Démarrage Local

Pré-requis : Docker Desktop installé.

1.  **Cloner le repo**
    ```bash
    git clone [https://github.com/TON-USER/cinephile-companion.git](https://github.com/TON-USER/cinephile-companion.git)
    cd cinephile-companion
    ```

2.  **Configuration**
    Créez un fichier `.env` à la racine (basé sur `.env.example`) :
    ```env
    TMDB_API_KEY=votre_api_key_ici
    TMDB_ACCESS_TOKEN=votre_read_token_ici
    ```

3.  **Lancer avec Docker**
    ```bash
    docker-compose up --build
    ```
    * Frontend : `http://localhost:8501`
    * Backend Docs : `http://localhost:8000/docs`

---

## 🔮 Roadmap RAG (Prochaine étape)

Migration vers une recherche sémantique complète ("Vibe Search").
* [ ] **Vector Database :** Intégration de `pgvector` (PostgreSQL).
* [ ] **Embeddings :** Vectorisation des synopsis et critiques.
* [ ] **RAG Génératif :** Le LLM expliquera *pourquoi* ce film correspond à votre requête, au lieu de juste lister des titres.

---

## ⚖️ Legal & Attribution

<img src="https://www.themoviedb.org/assets/2/v4/logos/v2/blue_short-8e7b30f73a4020692ccca9c88bafe5dcb6f8a62a4c6bc55cd9ba82bb2cd95f6c.svg" width="100" alt="TMDB Logo">

This product uses the TMDB API but is not endorsed or certified by TMDB.
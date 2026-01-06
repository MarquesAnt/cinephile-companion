# PROJECT CONTEXT: Ciné-Compagnon

## 1. VISION & OBJECTIF
Application web de gestion de films qui résout la "paralysie du choix" en groupe.
Elle croise deux contraintes strictes :
1. **Faisabilité Technique (Availability)** : Le film DOIT être disponible sur les abonnements communs des personnes présentes (Netflix, Prime, etc.).
2. **Gamification (Engagement)** : Le visionnage sert des objectifs ludiques ("Défis") ou émotionnels ("Mood").

## 2. STACK TECHNIQUE & CONVENTIONS
### Backend
- **Langage** : Python 3.11+
- **Framework** : FastAPI (Async)
- **Validation** : Pydantic (Strict typing, pas de `Any` si possible).
- **Data** : Firestore (NoSQL).
- **Infra** : Docker -> Google Cloud Run.

### Frontend (Cible)
- **Framework** : Next.js ou React (Vite).
- **UX** : Type "Dashboard de joueur" (Progression, Badges) et non "Mur d'affiches" classique.

### Règles de Code
- **Modularité** : Architecture Clean/Hexagonale simplifiée. Séparation stricte : Routes / Services / Modèles.
- **Typage** : Tout doit être typé. Utilisation intensive des `Enum` pour les statuts et catégories.
- **Erreurs** : Fail fast. Renvoyer des `HTTPException` claires.

## 3. DOMAINE & DATA MODEL (Cible MVP)
Le modèle de données doit supporter la gamification dès le jour 1.

### Entities
#### A. User & Session
- **User** : `id`, `username`, `providers` (list[str]), `active_challenges`.
- **Session** : Gère l'état éphémère "Qui est là ?". Calcule l'intersection des providers en temps réel.

#### B. Movie (Enrichi)
- Données TMDB statiques + Disponibilité dynamique.
- **Availability** : Doit être stockée par région (ex: FR) pour limiter les appels API externes.

#### C. Challenge (Core Feature)
Structure flexible pour définir des objectifs sans coder en dur.
- **Structure** :
  - `target_count` (int) : Nombre de films à voir.
  - `rules` (list[Rule]) : Liste de conditions (AND).
  - `xp_reward` (int).
- **Rule Object** :
  - `field` (ex: "genre", "year").
  - `operator` (ex: "eq", "gte", "in").
  - `value` (ex: "Western", 1960).

#### D. UserProgress
- Table de liaison : User <-> Challenge.
- Stocke : `movies_watched` (IDs validés), `current_count`, `is_completed`.

## 4. ROADMAP & PHASE ACTUELLE
**PHASE : MVP / SETUP BACKEND**
Nous sommes au début du développement.

**Priorités Immédiates :**
1. Setup du repo FastAPI + Docker.
2. Implémentation des modèles Pydantic (User, Movie, Challenge).
3. Création du service "Availability" (Mock ou TMDB API) pour filtrer par provider.
4. Création du service "Challenge Validator" (Vérifier si un film remplit une Rule).

**Features Futures (Hors Scope immédiat mais à prévoir) :**
- Intégration IA (Hugging Face) pour générer des défis sémantiques.
- UI Frontend complète.
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
# On importe la nouvelle fonction de filtrage
from app.services.recommendation import find_similar_movies, filter_movies_by_availability

app = FastAPI(title="Cinéphile Companion API")

# --- Modèles de données ---
class SearchRequest(BaseModel):
    query: str
    providers: Optional[List[str]] = []  # Default à liste vide pour éviter le None

class MovieResponse(BaseModel):
    id: int
    title: str
    overview: str
    vote_average: float
    poster_path: Optional[str] = None
    available_on: List[str] = []  # <--- Nouveau champ

# --- Routes ---
@app.get("/")
def read_root():
    return {"message": "Cinéphile Companion API is running 🚀"}

@app.post("/search", response_model=List[MovieResponse])
async def search_movies(request: SearchRequest):
    """
    Endpoint principal : RAG + Filtrage Disponibilité.
    """
    if not request.query:
        raise HTTPException(status_code=400, detail="La requête ne peut pas être vide.")

    print(f"🔎 Recherche : '{request.query}' | Providers : {request.providers}")
    
    # 1. RAG : On récupère plus de candidats (ex: 10) pour avoir du rab après filtrage
    # Note : Augmenter la limit ici est crucial car le filtrage va réduire la liste
    raw_results = await find_similar_movies(request.query, limit=10)
    
    if not raw_results:
        return []

    # 2. Conversion SQLModel -> Dict pour le traitement
    movies_dicts = [m.model_dump() for m in raw_results]

    # 3. Filtrage par disponibilité
    # Si l'user n'a pas sélectionné de providers, on renvoie tout (ou rien, selon ta logique produit. Ici : tout).
    if request.providers:
        final_movies_dicts = await filter_movies_by_availability(
            movies_dicts, 
            user_providers=[request.providers],
            country_code="FR"
        )
    else:
        # Pas de filtre demandé = on renvoie les résultats bruts sans info de streaming spécifique
        final_movies_dicts = movies_dicts
        
    # --- AJOUT POUR DEBUG CONSOLE ---
    found_titles = [m["title"] for m in final_movies_dicts]
    print(f"📤 Résultats ({len(found_titles)}) : {found_titles}")
    # --------------------------------

    # 4. Construction de la réponse typée
    response = [
        MovieResponse(
            id=m["id"],
            title=m["title"],
            overview=m["overview"],
            vote_average=m["vote_average"],
            poster_path=m["poster_path"],
            available_on=m.get("available_on", []) # Récupère la liste ou vide par défaut
        )
        for m in final_movies_dicts
    ]
    
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
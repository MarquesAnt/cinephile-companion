from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.services.recommendation import find_similar_movies

app = FastAPI(title="Cinéphile Companion API")

# --- Modèles de données ---
class SearchRequest(BaseModel):
    query: str
    providers: Optional[List[str]] = None  # On prépare le terrain pour les filtres

class MovieResponse(BaseModel):
    id: int
    title: str
    overview: str
    vote_average: float
    poster_path: Optional[str] = None

# --- Routes ---
@app.get("/")
def read_root():
    return {"message": "Cinéphile Companion API is running 🚀"}

@app.post("/search", response_model=List[MovieResponse])
async def search_movies(request: SearchRequest):
    """
    Endpoint principal : Reçoit une description, renvoie des films.
    """
    if not request.query:
        raise HTTPException(status_code=400, detail="La requête ne peut pas être vide.")

    print(f"🔎 Recherche reçue : {request.query}")
    
    # 1. Appel au RAG
    # Note : find_similar_movies est async, on utilise 'await'
    results = await find_similar_movies(request.query, limit=5)
    
    if not results:
        return []

    # 2. Conversion des résultats (SQLModel -> JSON Pydantic)
    response = [
        MovieResponse(
            id=m.id, # type: ignore
            title=m.title,
            overview=m.overview,
            vote_average=m.vote_average,
            poster_path=m.poster_path
        )
        for m in results
    ]
    
    return response

# --- Lancement direct pour le debug ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
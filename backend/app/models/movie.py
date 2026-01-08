from typing import Optional, List
from sqlmodel import SQLModel, Field, Column
from pgvector.sqlalchemy import Vector
from sqlalchemy import ARRAY, String

class Movie(SQLModel, table=True):
    __tablename__ = "movies"

    id: Optional[int] = Field(default=None, primary_key=True)
    tmdb_id: int = Field(unique=True, index=True)
    title: str
    original_title: Optional[str] = None
    overview: Optional[str] = None
    release_date: Optional[str] = None
    poster_path: Optional[str] = None
    
    # Métriques pour le filtrage
    vote_average: float = 0.0
    vote_count: int = 0
    popularity: float = 0.0
    
    # Genres stockés en tableau de chaînes (ex: ["Action", "Sci-Fi"])
    genres: List[str] = Field(default=[], sa_column=Column(ARRAY(String)))
    
    # Le Cœur du réacteur : Le Vecteur (768 dimensions pour Google Gemini)
    embedding: List[float] = Field(default=None, sa_column=Column(Vector(768)))

    # Flags
    is_ready: bool = Field(default=False) # True quand vectorisé
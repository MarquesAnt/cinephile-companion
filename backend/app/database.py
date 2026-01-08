from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/cinephile"

# Création du moteur de connexion
engine = create_engine(DATABASE_URL)

# Création de la "Session" (l'outil qui permet de faire des requêtes)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency pour récupérer une session DB dans les endpoints FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
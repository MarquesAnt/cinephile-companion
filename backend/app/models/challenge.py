from enum import Enum
from typing import List, Union, Optional
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

# --- ENUMS (Pour éviter les "Magic Strings") ---

class ChallengeType(str, Enum):
    """Définit le type de mécanique du défi."""
    COUNT = "count"         # Ex: Voir 5 films
    SPECIFIC = "specific"   # Ex: Voir un film précis (ID)
    Streak = "streak"       # Ex: 3 jours de suite (Bonus)

class RuleOperator(str, Enum):
    """Opérateurs logiques pour valider les métadonnées."""
    EQ = "eq"           # Égal à
    NEQ = "neq"         # Différent de
    GT = "gt"           # Plus grand que (strict)
    GTE = "gte"         # Plus grand ou égal (ex: year >= 1980)
    LT = "lt"           # Plus petit que
    LTE = "lte"         # Plus petit ou égal
    IN = "in"           # Contenu dans une liste (ex: Genre IN [Horreur, Thriller])
    CONTAINS = "contains" # Contient une valeur (ex: Cast contains "Brad Pitt")

# --- SUB-MODELS ---

class ChallengeRule(BaseModel):
    """
    Une règle atomique. 
    Exemple : {field: "year", operator: "gte", value: 1990}
    """
    field: str = Field(
        ..., 
        description="Le champ TMDB à vérifier (ex: 'genres', 'release_date', 'runtime')."
    )
    operator: RuleOperator = Field(
        ..., 
        description="L'opérateur logique de comparaison."
    )
    # Union permet d'accepter un string, un entier ou une liste selon le besoin
    value: Union[str, int, float, List[str], List[int]] = Field(
        ..., 
        description="La valeur cible pour valider la règle."
    )

# --- CORE MODEL ---

class Challenge(BaseModel):
    """
    Représente un objectif ludique complet.
    Stocké dans Firestore collection 'challenges'.
    """
    id: Optional[str] = Field(None, description="Firestore Document ID (généré auto si vide)")
    title: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., max_length=500)
    
    challenge_type: ChallengeType = Field(
        default=ChallengeType.COUNT,
        description="Le type de défi."
    )
    
    target_count: int = Field(
        default=1, 
        ge=1, 
        description="Nombre d'actions requises pour compléter le défi."
    )
    
    rules: List[ChallengeRule] = Field(
        default_factory=list,
        description="Liste des conditions à remplir (Logique AND par défaut)."
    )
    
    xp_reward: int = Field(
        default=100, 
        ge=0, 
        description="Points d'expérience gagnés à la complétion."
    )
    
    is_active: bool = Field(True, description="Si faux, le défi est archivé.")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # --- VALIDATORS ---

    @field_validator('rules')
    @classmethod
    def validate_rules_not_empty(cls, v, info):
        """Vérifie qu'il y a au moins une règle si le type n'est pas 'SPECIFIC'."""
        # Note: On accède aux autres champs via info.data dans Pydantic V2 si besoin,
        # mais ici on fait une validation simple.
        if not v:
            # On pourrait autoriser une liste vide pour certains types, 
            # mais pour le MVP, un défi doit avoir des règles.
            raise ValueError("Un défi doit contenir au moins une règle de validation.")
        return v


def evaluate_rule(movie_data: dict, rule: ChallengeRule) -> bool:
    field_value = movie_data.get(rule.field)
    
    if field_value is None:
        return False
    
    match rule.operator:
        case RuleOperator.EQ:
            return field_value == rule.value
        case RuleOperator.NEQ:
            return field_value != rule.value
        case RuleOperator.GTE:
            return field_value >= rule.value
        case RuleOperator.LTE:
            return field_value <= rule.value
        case RuleOperator.GT:
            return field_value > rule.value
        case RuleOperator.LT:
            return field_value < rule.value
        case RuleOperator.IN:
            return field_value in rule.value if isinstance(rule.value, (list, tuple, set)) else False
        case RuleOperator.CONTAINS:
            if isinstance(field_value, (list, tuple, set)):
                return rule.value in field_value
            elif isinstance(field_value, str):
                return str(rule.value) in field_value
            return False
        case _:
            return False

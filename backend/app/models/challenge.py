from enum import StrEnum
from typing import Any
from pydantic import BaseModel, Field, field_validator


class RuleOperator(StrEnum):
    EQ = "eq"
    GTE = "gte"
    LTE = "lte"
    IN = "in"
    CONTAINS = "contains"
    GT = "gt"
    LT = "lt"


class Rule(BaseModel):
    field: str = Field(
        ...,
        description="Le champ du film à évaluer (ex: 'genre', 'year', 'director')",
        examples=["genre", "year", "director"]
    )
    operator: RuleOperator = Field(
        ...,
        description="Opérateur de comparaison à appliquer",
        examples=[RuleOperator.EQ, RuleOperator.GTE, RuleOperator.IN]
    )
    value: Any = Field(
        ...,
        description="Valeur de comparaison (type dépend du field)",
        examples=["Western", 1960, ["Action", "Thriller"]]
    )


class Challenge(BaseModel):
    target_count: int = Field(
        ...,
        description="Nombre de films à voir pour compléter le défi",
        examples=[5, 10, 20],
        gt=0
    )
    rules: list[Rule] = Field(
        ...,
        description="Liste de conditions (AND) que les films doivent satisfaire",
        examples=[
            [
                {"field": "genre", "operator": "eq", "value": "Western"},
                {"field": "year", "operator": "gte", "value": 1960}
            ]
        ],
        min_length=1
    )
    xp_reward: int = Field(
        ...,
        description="Points d'expérience accordés à la complétion du défi",
        examples=[100, 250, 500],
        ge=0
    )

    @field_validator("rules")
    @classmethod
    def validate_rules_not_empty(cls, v: list[Rule]) -> list[Rule]:
        if not v:
            raise ValueError("La liste rules ne peut pas être vide")
        return v


def evaluate_rule(movie_data: dict, rule: Rule) -> bool:
    field_value = movie_data.get(rule.field)
    
    if field_value is None:
        return False
    
    match rule.operator:
        case RuleOperator.EQ:
            return field_value == rule.value
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


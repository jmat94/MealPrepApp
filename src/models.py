from pydantic import BaseModel, Field
from typing import List, Optional

class IngredientInput(BaseModel):
    """
    Data structure for individual ingredients during recipe creation.
    Nutrients are provided as base values (per 100g).
    """
    name: str = Field(..., example="Atlantic Salmon")
    weight_in_grams: float = Field(..., gt=0, example=200.0)
    calories: float = Field(..., ge=0, example=208.0)
    protein: float = Field(..., ge=0, example=20.0)
    carbs: float = Field(..., ge=0, example=0.0)
    fat: float = Field(..., ge=0, example=13.0)

class RecipeCreate(BaseModel):
    """
    The main payload for creating a new recipe record.
    """
    title: str = Field(..., min_length=1, example="Honey Garlic Salmon")
    instructions: str = Field(..., example="Pan-sear salmon and glaze with honey.")
    base_servings: int = Field(default=2, gt=0)
    ingredients: List[IngredientInput]
    is_premium_only: Optional[bool] = False

class UserCreate(BaseModel):
    """
    Class to handle the creation of a new user
    """
    pass
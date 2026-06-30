from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

MealType = Literal["breakfast", "lunch", "dinner", "snack"]


class UserBase(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    full_name: str = Field(min_length=2, max_length=120)


class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=128)


class UserLogin(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=6, max_length=128)


class UserRead(UserBase):
    id: int

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class IngredientBase(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    category: str = Field(default="Other", max_length=60)
    description: str = Field(default="", max_length=500)
    quantity: float = Field(default=1, ge=0)
    unit: str = Field(default="pcs", max_length=30)
    expires_on: date | None = None


class IngredientCreate(IngredientBase):
    pass


class IngredientRead(IngredientBase):
    id: int
    user_id: int | None = None

    class Config:
        from_attributes = True


class RecipeIngredientBase(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    quantity: float = Field(default=1, ge=0)
    unit: str = Field(default="pcs", max_length=30)
    is_optional: bool = False


class RecipeIngredientCreate(RecipeIngredientBase):
    pass


class RecipeIngredientRead(RecipeIngredientBase):
    id: int

    class Config:
        from_attributes = True


class RecipeBase(BaseModel):
    title: str = Field(min_length=3, max_length=150)
    description: str
    instructions: str
    cooking_time_minutes: int = Field(gt=0, le=600)
    difficulty: str = Field(default="Easy", max_length=30)
    meal_type: MealType = "lunch"


class RecipeCreate(RecipeBase):
    required_ingredients: list[RecipeIngredientCreate]


class RecipeRead(RecipeBase):
    id: int
    owner_id: int | None = None
    is_public: bool = False
    required_ingredients: list[RecipeIngredientRead]

    class Config:
        from_attributes = True


class RecipeMatch(BaseModel):
    recipe: RecipeRead
    matched_ingredients: list[str]
    pantry_available_ingredients: list[str] = Field(default_factory=list)
    low_stock_ingredients: list[str] = Field(default_factory=list)
    missing_ingredients: list[str]
    match_percentage: int
    can_prepare: bool


class RecipeMatchRequest(BaseModel):
    ingredient_ids: list[int] = Field(default_factory=list)
    meal_type: MealType | None = None


class PreparationResult(BaseModel):
    recipe_id: int
    recipe_title: str
    consumed_ingredients: list[RecipeIngredientRead]
    remaining_ingredients: list[IngredientRead]

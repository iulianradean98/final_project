from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.api.dependencies import get_current_user, get_optional_user
from app.db.session import get_db
from app.models import Ingredient, Recipe, RecipeIngredient, User
from app.schemas import PreparationResult, RecipeCreate, RecipeMatch, RecipeMatchRequest, RecipeRead
from app.services.matching import build_recipe_matches, normalize_name

router = APIRouter()


def visible_recipes_statement(current_user: User | None):
    statement = select(Recipe).options(selectinload(Recipe.required_ingredients))
    if current_user is None:
        return statement.where(Recipe.is_public.is_(True))
    return statement.where((Recipe.is_public.is_(True)) | (Recipe.owner_id == current_user.id))


@router.get("", response_model=list[RecipeRead])
def list_recipes(
    meal_type: str | None = None,
    current_user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[Recipe]:
    statement = visible_recipes_statement(current_user).order_by(Recipe.title)
    if meal_type:
        statement = statement.where(Recipe.meal_type == meal_type)
    return list(db.scalars(statement))


@router.post("", response_model=RecipeRead, status_code=status.HTTP_201_CREATED)
def create_recipe(
    payload: RecipeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Recipe:
    recipe = Recipe(
        title=payload.title,
        description=payload.description,
        instructions=payload.instructions,
        cooking_time_minutes=payload.cooking_time_minutes,
        difficulty=payload.difficulty,
        meal_type=payload.meal_type,
        owner_id=current_user.id,
        is_public=False,
    )
    recipe.required_ingredients = [
        RecipeIngredient(**ingredient.model_dump()) for ingredient in payload.required_ingredients
    ]
    db.add(recipe)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Recipe already exists") from exc
    db.refresh(recipe)
    return recipe


@router.get("/matches", response_model=list[RecipeMatch])
def match_recipes(
    meal_type: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    statement = visible_recipes_statement(current_user).order_by(Recipe.title)
    if meal_type:
        statement = statement.where(Recipe.meal_type == meal_type)
    recipes = list(db.scalars(statement))
    pantry_ingredients = list(
        db.scalars(
            select(Ingredient)
            .where(Ingredient.user_id == current_user.id)
            .order_by(Ingredient.name)
        )
    )
    return build_recipe_matches(recipes, pantry_ingredients)


@router.post("/matches", response_model=list[RecipeMatch])
def match_recipes_from_selection(
    payload: RecipeMatchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    statement = visible_recipes_statement(current_user).order_by(Recipe.title)
    if payload.meal_type:
        statement = statement.where(Recipe.meal_type == payload.meal_type)
    recipes = list(db.scalars(statement))

    pantry_ingredients = list(
        db.scalars(
            select(Ingredient)
            .where(Ingredient.user_id == current_user.id)
            .order_by(Ingredient.name)
        )
    )
    return build_recipe_matches(recipes, pantry_ingredients, set(payload.ingredient_ids))


@router.get("/{recipe_id}", response_model=RecipeRead)
def get_recipe(
    recipe_id: int,
    current_user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> Recipe:
    recipe = db.scalar(
        visible_recipes_statement(current_user)
        .options(selectinload(Recipe.required_ingredients))
        .where(Recipe.id == recipe_id)
    )
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe


@router.post("/{recipe_id}/finish", response_model=PreparationResult)
def finish_recipe(
    recipe_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    recipe = db.scalar(
        visible_recipes_statement(current_user)
        .options(selectinload(Recipe.required_ingredients))
        .where(Recipe.id == recipe_id)
    )
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")

    pantry_items = {
        normalize_name(ingredient.name): ingredient
        for ingredient in db.scalars(select(Ingredient).where(Ingredient.user_id == current_user.id))
    }
    required = [ingredient for ingredient in recipe.required_ingredients if not ingredient.is_optional]
    missing: list[str] = []

    for ingredient in required:
        pantry_item = pantry_items.get(normalize_name(ingredient.name))
        if pantry_item is None:
            missing.append(ingredient.name)
        elif pantry_item.unit != ingredient.unit:
            missing.append(f"{ingredient.name} ({ingredient.unit} required)")
        elif pantry_item.quantity < ingredient.quantity:
            missing.append(f"{ingredient.name} ({ingredient.quantity} {ingredient.unit} required)")

    if missing:
        raise HTTPException(
            status_code=409,
            detail=f"Not enough pantry stock to prepare this recipe: {', '.join(missing)}",
        )

    for ingredient in required:
        pantry_items[normalize_name(ingredient.name)].quantity -= ingredient.quantity

    db.commit()

    remaining = list(
        db.scalars(
            select(Ingredient)
            .where(Ingredient.user_id == current_user.id)
            .where(Ingredient.name.in_([ingredient.name for ingredient in required]))
            .order_by(Ingredient.name)
        )
    )
    return {
        "recipe_id": recipe.id,
        "recipe_title": recipe.title,
        "consumed_ingredients": required,
        "remaining_ingredients": remaining,
    }


@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recipe(
    recipe_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    recipe = db.scalar(
        select(Recipe)
        .where(Recipe.id == recipe_id)
        .where(Recipe.owner_id == current_user.id)
    )
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    db.delete(recipe)
    db.commit()

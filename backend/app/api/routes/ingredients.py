from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models import Ingredient, User
from app.schemas import IngredientCreate, IngredientRead

router = APIRouter()


@router.get("", response_model=list[IngredientRead])
def list_ingredients(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Ingredient]:
    return list(
        db.scalars(
            select(Ingredient)
            .where(Ingredient.user_id == current_user.id)
            .order_by(Ingredient.name)
        )
    )


@router.post("", response_model=IngredientRead, status_code=status.HTTP_201_CREATED)
def create_ingredient(
    payload: IngredientCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Ingredient:
    ingredient_data = payload.model_dump()
    ingredient_data["name"] = payload.name.strip().lower()
    ingredient = Ingredient(**ingredient_data, user_id=current_user.id)
    db.add(ingredient)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Ingredient already exists") from exc
    db.refresh(ingredient)
    return ingredient


@router.delete("/{ingredient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ingredient(
    ingredient_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    ingredient = db.scalar(
        select(Ingredient)
        .where(Ingredient.id == ingredient_id)
        .where(Ingredient.user_id == current_user.id)
    )
    if ingredient is None:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    db.delete(ingredient)
    db.commit()

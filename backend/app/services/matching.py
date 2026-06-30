from app.models import Ingredient, Recipe


def normalize_name(value: str) -> str:
    return value.strip().lower()


def build_recipe_matches(
    recipes: list[Recipe],
    pantry_ingredients: list[Ingredient],
    selected_ingredient_ids: set[int] | None = None,
) -> list[dict]:
    available = {normalize_name(ingredient.name): ingredient for ingredient in pantry_ingredients}
    selected_names = {
        normalize_name(ingredient.name)
        for ingredient in pantry_ingredients
        if selected_ingredient_ids is None or ingredient.id in selected_ingredient_ids
    }
    matches: list[dict] = []

    for recipe in recipes:
        required = [
            ingredient
            for ingredient in recipe.required_ingredients
            if not ingredient.is_optional
        ]
        matched: list[str] = []
        pantry_available: list[str] = []
        low_stock: list[str] = []
        missing: list[str] = []

        for ingredient in required:
            normalized_name = normalize_name(ingredient.name)
            pantry_item = available.get(normalize_name(ingredient.name))
            if pantry_item is None:
                missing.append(ingredient.name)
                continue

            has_matching_quantity = pantry_item.unit == ingredient.unit and pantry_item.quantity >= ingredient.quantity
            if not has_matching_quantity:
                low_stock.append(f"{ingredient.name} ({ingredient.quantity} {ingredient.unit} needed)")
            elif selected_ingredient_ids is None or normalized_name in selected_names:
                matched.append(ingredient.name)
            else:
                pantry_available.append(ingredient.name)

        total_required = len(required)
        percentage = 100 if total_required == 0 else round(len(matched) / total_required * 100)

        matches.append(
            {
                "recipe": recipe,
                "matched_ingredients": matched,
                "pantry_available_ingredients": pantry_available,
                "low_stock_ingredients": low_stock,
                "missing_ingredients": missing,
                "match_percentage": percentage,
                "can_prepare": len(missing) == 0 and len(low_stock) == 0,
            }
        )

    return sorted(matches, key=lambda item: item["match_percentage"], reverse=True)

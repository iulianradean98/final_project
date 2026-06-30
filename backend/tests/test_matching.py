from app.services.matching import normalize_name


class PantryItem:
    def __init__(self, name: str, quantity: float, unit: str, item_id: int = 1) -> None:
        self.id = item_id
        self.name = name
        self.quantity = quantity
        self.unit = unit


class RecipeItem:
    def __init__(self, name: str, quantity: float, unit: str, is_optional: bool = False) -> None:
        self.name = name
        self.quantity = quantity
        self.unit = unit
        self.is_optional = is_optional


class Recipe:
    def __init__(self) -> None:
        self.required_ingredients = [
            RecipeItem("eggs", 2, "pcs"),
            RecipeItem("cheese", 40, "g"),
        ]


def test_normalize_name_trims_and_lowercases_values() -> None:
    assert normalize_name("  Tomatoes ") == "tomatoes"


def test_recipe_match_requires_enough_quantity() -> None:
    from app.services.matching import build_recipe_matches

    matches = build_recipe_matches(
        [Recipe()],
        [PantryItem("eggs", 1, "pcs"), PantryItem("cheese", 60, "g")],
    )

    assert matches[0]["match_percentage"] == 50
    assert matches[0]["can_prepare"] is False
    assert matches[0]["low_stock_ingredients"] == ["eggs (2 pcs needed)"]
    assert matches[0]["missing_ingredients"] == []


def test_selected_matching_distinguishes_unselected_pantry_items_from_missing() -> None:
    from app.services.matching import build_recipe_matches

    matches = build_recipe_matches(
        [Recipe()],
        [PantryItem("eggs", 4, "pcs", item_id=1), PantryItem("cheese", 60, "g", item_id=2)],
        selected_ingredient_ids={1},
    )

    assert matches[0]["matched_ingredients"] == ["eggs"]
    assert matches[0]["pantry_available_ingredients"] == ["cheese"]
    assert matches[0]["missing_ingredients"] == []

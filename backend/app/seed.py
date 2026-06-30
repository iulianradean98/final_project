from datetime import date, timedelta

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import Ingredient, Recipe, RecipeIngredient, User


DEMO_USER_EMAIL = "demo@reciperescue.local"
DEMO_USER_PASSWORD = "demo123"


DEMO_INGREDIENTS = [
    {"name": "eggs", "category": "Protein", "description": "Fresh eggs for breakfast and baking.", "quantity": 12, "unit": "pcs", "expires_on_days": 10},
    {"name": "tomatoes", "category": "Vegetables", "description": "Ripe tomatoes for sauces and salads.", "quantity": 8, "unit": "pcs", "expires_on_days": 4},
    {"name": "pasta", "category": "Pantry", "description": "Dry pasta for quick dinners.", "quantity": 1000, "unit": "g"},
    {"name": "garlic", "category": "Vegetables", "description": "Garlic bulbs for seasoning.", "quantity": 8, "unit": "pcs"},
    {"name": "cheese", "category": "Dairy", "description": "Grated cheese for pasta, eggs, and snacks.", "quantity": 400, "unit": "g", "expires_on_days": 8},
    {"name": "oats", "category": "Pantry", "description": "Rolled oats for breakfast bowls.", "quantity": 500, "unit": "g"},
    {"name": "milk", "category": "Dairy", "description": "Milk for breakfast and sauces.", "quantity": 1000, "unit": "ml", "expires_on_days": 5},
    {"name": "banana", "category": "Fruit", "description": "Bananas for snacks and breakfast.", "quantity": 6, "unit": "pcs", "expires_on_days": 3},
    {"name": "chicken breast", "category": "Protein", "description": "Lean chicken breast.", "quantity": 800, "unit": "g", "expires_on_days": 3},
    {"name": "rice", "category": "Pantry", "description": "Long grain rice.", "quantity": 1000, "unit": "g"},
    {"name": "broccoli", "category": "Vegetables", "description": "Fresh broccoli florets.", "quantity": 500, "unit": "g", "expires_on_days": 4},
    {"name": "tortilla", "category": "Bakery", "description": "Soft tortillas for wraps.", "quantity": 8, "unit": "pcs", "expires_on_days": 7},
    {"name": "beans", "category": "Pantry", "description": "Cooked beans for bowls and wraps.", "quantity": 600, "unit": "g"},
    {"name": "lettuce", "category": "Vegetables", "description": "Crisp lettuce for salads and wraps.", "quantity": 300, "unit": "g", "expires_on_days": 3},
    {"name": "yogurt", "category": "Dairy", "description": "Plain yogurt for snacks and breakfast.", "quantity": 500, "unit": "g", "expires_on_days": 6},
    {"name": "berries", "category": "Fruit", "description": "Mixed berries.", "quantity": 250, "unit": "g", "expires_on_days": 2},
    {"name": "bread", "category": "Bakery", "description": "Sliced bread.", "quantity": 10, "unit": "slices", "expires_on_days": 4},
    {"name": "avocado", "category": "Fruit", "description": "Avocado for toast and salads.", "quantity": 3, "unit": "pcs", "expires_on_days": 3},
    {"name": "salmon", "category": "Protein", "description": "Salmon fillet for dinner.", "quantity": 500, "unit": "g", "expires_on_days": 2},
    {"name": "potatoes", "category": "Vegetables", "description": "Potatoes for roasting.", "quantity": 1000, "unit": "g"},
    {"name": "peanut butter", "category": "Pantry", "description": "Peanut butter for quick snacks.", "quantity": 300, "unit": "g"},
    {"name": "apple", "category": "Fruit", "description": "Apples for snacks.", "quantity": 6, "unit": "pcs", "expires_on_days": 10},
    {"name": "spinach", "category": "Vegetables", "description": "Baby spinach.", "quantity": 250, "unit": "g", "expires_on_days": 3},
    {"name": "mushrooms", "category": "Vegetables", "description": "Button mushrooms.", "quantity": 300, "unit": "g", "expires_on_days": 4},
    {"name": "flour", "category": "Pantry", "description": "All-purpose flour.", "quantity": 1000, "unit": "g"},
]


def steps(*items: str) -> str:
    return "\n".join(f"{index}. {item}" for index, item in enumerate(items, start=1))


DEMO_RECIPES = [
    {
        "title": "Cheesy Omelette",
        "meal_type": "breakfast",
        "description": "A soft breakfast omelette with melted cheese, ideal when you need something fast but filling.",
        "instructions": steps(
            "Crack the eggs into a bowl and whisk until the yolks and whites are fully combined.",
            "Heat a non-stick pan over medium-low heat and pour in the eggs.",
            "When the edges begin to set, sprinkle cheese over one half of the omelette.",
            "Fold the omelette, cook for one more minute, and serve while the cheese is melted.",
        ),
        "cooking_time_minutes": 10,
        "difficulty": "Easy",
        "ingredients": [("eggs", 2, "pcs"), ("cheese", 40, "g")],
    },
    {
        "title": "Banana Oat Bowl",
        "meal_type": "breakfast",
        "description": "A warm, creamy oat bowl with banana for natural sweetness and slow-release energy.",
        "instructions": steps(
            "Add oats and milk to a small saucepan and bring to a gentle simmer.",
            "Stir frequently for 5 to 7 minutes until the oats become creamy.",
            "Slice the banana and place it over the cooked oats.",
            "Let the bowl rest for one minute before serving so the banana softens slightly.",
        ),
        "cooking_time_minutes": 12,
        "difficulty": "Easy",
        "ingredients": [("oats", 80, "g"), ("milk", 200, "ml"), ("banana", 1, "pcs")],
    },
    {
        "title": "Avocado Egg Toast",
        "meal_type": "breakfast",
        "description": "Crisp toast topped with mashed avocado and egg, a compact breakfast with healthy fats and protein.",
        "instructions": steps(
            "Toast the bread slices until crisp and golden.",
            "Mash the avocado with a fork and spread it evenly over the toast.",
            "Cook the egg to your preference in a small pan.",
            "Place the egg on top of the avocado toast and serve immediately.",
        ),
        "cooking_time_minutes": 15,
        "difficulty": "Easy",
        "ingredients": [("bread", 2, "slices"), ("avocado", 1, "pcs"), ("eggs", 1, "pcs")],
    },
    {
        "title": "Tomato Garlic Pasta",
        "meal_type": "dinner",
        "description": "A quick pasta dinner with fresh tomatoes, garlic, and optional cheese for a richer finish.",
        "instructions": steps(
            "Boil the pasta in salted water until al dente, then reserve a little cooking water.",
            "Chop the tomatoes and garlic while the pasta cooks.",
            "Saute garlic for 30 seconds, add tomatoes, and cook until they become saucy.",
            "Toss pasta with the sauce, loosen with cooking water if needed, and finish with cheese if available.",
        ),
        "cooking_time_minutes": 20,
        "difficulty": "Easy",
        "ingredients": [("pasta", 200, "g"), ("tomatoes", 2, "pcs"), ("garlic", 1, "pcs"), ("cheese", 30, "g", True)],
    },
    {
        "title": "Fresh Tomato Shakshuka",
        "meal_type": "breakfast",
        "description": "Eggs gently cooked in a tomato and garlic base, useful for a hearty breakfast or brunch.",
        "instructions": steps(
            "Chop tomatoes and garlic, then cook them in a pan until the tomatoes release their juices.",
            "Simmer the sauce for a few minutes so it thickens slightly.",
            "Make small wells in the sauce and crack the eggs into them.",
            "Cover the pan and cook until the egg whites are set but the yolks are still soft.",
        ),
        "cooking_time_minutes": 25,
        "difficulty": "Medium",
        "ingredients": [("eggs", 3, "pcs"), ("tomatoes", 4, "pcs"), ("garlic", 1, "pcs")],
    },
    {
        "title": "Chicken Rice Bowl",
        "meal_type": "lunch",
        "description": "A balanced lunch bowl with rice, chicken, and broccoli that works well for meal prep.",
        "instructions": steps(
            "Cook rice until tender and fluff it with a fork.",
            "Season the chicken breast lightly and cook it in a pan until fully done.",
            "Steam or saute broccoli until bright green and tender.",
            "Slice the chicken, place it over rice, add broccoli, and serve warm.",
        ),
        "cooking_time_minutes": 35,
        "difficulty": "Medium",
        "ingredients": [("chicken breast", 200, "g"), ("rice", 120, "g"), ("broccoli", 150, "g")],
    },
    {
        "title": "Bean Lettuce Wrap",
        "meal_type": "lunch",
        "description": "A light vegetarian wrap with beans for protein and lettuce for crunch.",
        "instructions": steps(
            "Warm the tortilla briefly so it becomes flexible.",
            "Spread beans across the center, leaving the edges clear.",
            "Add lettuce and fold the sides inward.",
            "Roll tightly, slice in half, and serve right away.",
        ),
        "cooking_time_minutes": 10,
        "difficulty": "Easy",
        "ingredients": [("tortilla", 1, "pcs"), ("beans", 120, "g"), ("lettuce", 50, "g")],
    },
    {
        "title": "Spinach Mushroom Pasta",
        "meal_type": "dinner",
        "description": "A vegetable-forward pasta with mushrooms, spinach, and garlic for a comforting dinner.",
        "instructions": steps(
            "Boil pasta until al dente and save a splash of pasta water.",
            "Slice mushrooms and cook them in a pan until browned.",
            "Add garlic and spinach, then cook until the spinach wilts.",
            "Toss the vegetables with pasta and use pasta water to bring everything together.",
        ),
        "cooking_time_minutes": 25,
        "difficulty": "Easy",
        "ingredients": [("pasta", 180, "g"), ("spinach", 80, "g"), ("mushrooms", 100, "g"), ("garlic", 1, "pcs")],
    },
    {
        "title": "Salmon Potato Tray Bake",
        "meal_type": "dinner",
        "description": "A simple oven meal with roasted potatoes and salmon, good for a complete dinner with minimal cleanup.",
        "instructions": steps(
            "Cut potatoes into small chunks so they roast evenly.",
            "Place potatoes on a tray and roast until they begin to soften.",
            "Add salmon and garlic to the tray.",
            "Bake until the salmon flakes easily and the potatoes are golden.",
        ),
        "cooking_time_minutes": 40,
        "difficulty": "Medium",
        "ingredients": [("salmon", 180, "g"), ("potatoes", 300, "g"), ("garlic", 1, "pcs")],
    },
    {
        "title": "Yogurt Berry Cup",
        "meal_type": "snack",
        "description": "A refreshing snack with creamy yogurt and berries, ready in a few minutes.",
        "instructions": steps(
            "Spoon yogurt into a small bowl or cup.",
            "Rinse berries and gently pat them dry.",
            "Add berries over the yogurt.",
            "Serve chilled, or let it sit for two minutes so the berries soften slightly.",
        ),
        "cooking_time_minutes": 5,
        "difficulty": "Easy",
        "ingredients": [("yogurt", 150, "g"), ("berries", 80, "g")],
    },
    {
        "title": "Apple Peanut Butter Slices",
        "meal_type": "snack",
        "description": "A crisp, sweet snack with apple slices and peanut butter for quick energy.",
        "instructions": steps(
            "Wash the apple and cut it into even slices.",
            "Remove the core from each slice.",
            "Spread peanut butter over the slices.",
            "Serve immediately so the apple stays crisp.",
        ),
        "cooking_time_minutes": 5,
        "difficulty": "Easy",
        "ingredients": [("apple", 1, "pcs"), ("peanut butter", 25, "g")],
    },
    {
        "title": "Tomato Cheese Toast",
        "meal_type": "snack",
        "description": "A warm toast snack with juicy tomato and melted cheese.",
        "instructions": steps(
            "Place bread slices on a tray or toaster pan.",
            "Slice the tomato and arrange it over the bread.",
            "Add cheese on top.",
            "Toast until the bread is crisp and the cheese is melted.",
        ),
        "cooking_time_minutes": 8,
        "difficulty": "Easy",
        "ingredients": [("bread", 2, "slices"), ("tomatoes", 1, "pcs"), ("cheese", 40, "g")],
    },
    {
        "title": "Chicken Tortilla Melt",
        "meal_type": "lunch",
        "description": "A warm tortilla lunch with chicken and cheese, crisp outside and soft inside.",
        "instructions": steps(
            "Slice cooked chicken into small pieces.",
            "Place chicken and cheese on one half of the tortilla.",
            "Fold the tortilla and toast it in a dry pan.",
            "Cook both sides until golden and the cheese has melted.",
        ),
        "cooking_time_minutes": 18,
        "difficulty": "Easy",
        "ingredients": [("tortilla", 1, "pcs"), ("chicken breast", 120, "g"), ("cheese", 50, "g")],
    },
    {
        "title": "Broccoli Cheese Rice",
        "meal_type": "dinner",
        "description": "A creamy rice dinner with broccoli and cheese, simple enough for a busy evening.",
        "instructions": steps(
            "Cook rice until tender.",
            "Steam broccoli until it is bright green and soft enough to bite.",
            "Stir broccoli into the warm rice.",
            "Add cheese and mix until melted and creamy.",
        ),
        "cooking_time_minutes": 30,
        "difficulty": "Easy",
        "ingredients": [("rice", 150, "g"), ("broccoli", 180, "g"), ("cheese", 60, "g")],
    },
    {
        "title": "Simple Breakfast Pancakes",
        "meal_type": "breakfast",
        "description": "Soft breakfast pancakes made from basic staples, useful when the pantry is almost empty.",
        "instructions": steps(
            "Mix flour, milk, and egg until a smooth batter forms.",
            "Heat a pan over medium heat.",
            "Pour small circles of batter into the pan.",
            "Cook until bubbles appear, flip, and cook the other side until golden.",
        ),
        "cooking_time_minutes": 20,
        "difficulty": "Medium",
        "ingredients": [("flour", 120, "g"), ("milk", 200, "ml"), ("eggs", 1, "pcs")],
    },
    {
        "title": "Mediterranean Quinoa Bowl",
        "meal_type": "lunch",
        "description": "A fresh lunch bowl with quinoa, cucumber, tomatoes, and feta. It intentionally includes ingredients that may not be in the pantry yet.",
        "instructions": steps(
            "Cook quinoa until fluffy and let it cool slightly.",
            "Chop cucumber and tomatoes into bite-sized pieces.",
            "Combine quinoa with vegetables and crumble feta on top.",
            "Serve as a bright lunch bowl, adding dressing if available.",
        ),
        "cooking_time_minutes": 25,
        "difficulty": "Medium",
        "ingredients": [("quinoa", 120, "g"), ("cucumber", 1, "pcs"), ("tomatoes", 2, "pcs"), ("feta", 60, "g")],
    },
    {
        "title": "Coconut Chickpea Curry",
        "meal_type": "dinner",
        "description": "A cozy curry with chickpeas, coconut milk, and rice, useful for showing missing pantry products.",
        "instructions": steps(
            "Cook rice according to package instructions.",
            "Warm chickpeas with coconut milk in a pan.",
            "Add curry powder and simmer until the sauce thickens.",
            "Serve the curry over rice while hot.",
        ),
        "cooking_time_minutes": 30,
        "difficulty": "Medium",
        "ingredients": [("chickpeas", 250, "g"), ("coconut milk", 250, "ml"), ("curry powder", 10, "g"), ("rice", 150, "g")],
    },
    {
        "title": "Shrimp Noodle Stir Fry",
        "meal_type": "dinner",
        "description": "A fast stir fry with shrimp, noodles, bell pepper, and garlic.",
        "instructions": steps(
            "Cook noodles until just tender and drain them.",
            "Slice bell pepper into thin strips.",
            "Cook shrimp in a hot pan until pink.",
            "Add garlic, bell pepper, and noodles, then toss everything together.",
        ),
        "cooking_time_minutes": 22,
        "difficulty": "Medium",
        "ingredients": [("shrimp", 200, "g"), ("noodles", 180, "g"), ("bell pepper", 1, "pcs"), ("garlic", 1, "pcs")],
    },
    {
        "title": "Hummus Veggie Sandwich",
        "meal_type": "lunch",
        "description": "A quick sandwich with hummus, cucumber, lettuce, and bread.",
        "instructions": steps(
            "Toast bread lightly if you prefer a firmer sandwich.",
            "Spread hummus over the bread slices.",
            "Add cucumber slices and lettuce.",
            "Close the sandwich, press gently, and serve.",
        ),
        "cooking_time_minutes": 8,
        "difficulty": "Easy",
        "ingredients": [("bread", 2, "slices"), ("hummus", 60, "g"), ("cucumber", 1, "pcs"), ("lettuce", 40, "g")],
    },
    {
        "title": "Mango Yogurt Smoothie",
        "meal_type": "snack",
        "description": "A creamy smoothie with mango, yogurt, and milk, good for a missing-fruit example.",
        "instructions": steps(
            "Add mango, yogurt, and milk to a blender.",
            "Blend until completely smooth.",
            "Taste and adjust thickness with extra milk if needed.",
            "Serve cold in a tall glass.",
        ),
        "cooking_time_minutes": 5,
        "difficulty": "Easy",
        "ingredients": [("mango", 1, "pcs"), ("yogurt", 120, "g"), ("milk", 150, "ml")],
    },
]


def seed_demo_data() -> None:
    db = SessionLocal()
    try:
        demo_user = db.scalar(select(User).where(User.email == DEMO_USER_EMAIL))
        if demo_user is None:
            demo_user = User(
                email=DEMO_USER_EMAIL,
                full_name="Demo User",
                password_hash=hash_password(DEMO_USER_PASSWORD),
            )
            db.add(demo_user)
            db.flush()

        for existing_ingredient in db.scalars(select(Ingredient).where(Ingredient.user_id.is_(None))):
            existing_ingredient.user_id = demo_user.id
        db.flush()

        demo_ingredients = {
            ingredient.name: ingredient
            for ingredient in db.scalars(select(Ingredient).where(Ingredient.user_id == demo_user.id))
        }

        today = date.today()
        for item in DEMO_INGREDIENTS:
            ingredient = demo_ingredients.get(item["name"])
            expires_on = (
                today + timedelta(days=item["expires_on_days"])
                if "expires_on_days" in item
                else None
            )
            if ingredient is None:
                db.add(
                    Ingredient(
                        name=item["name"],
                        user_id=demo_user.id,
                        category=item["category"],
                        description=item["description"],
                        quantity=item["quantity"],
                        unit=item["unit"],
                        expires_on=expires_on,
                    )
                )
                demo_ingredients[item["name"]] = ingredient
            else:
                ingredient.category = item["category"]
                ingredient.description = item["description"]
                ingredient.expires_on = ingredient.expires_on or expires_on

        for item in DEMO_RECIPES:
            recipe = db.scalar(
                select(Recipe)
                .where(Recipe.title == item["title"])
                .where((Recipe.is_public.is_(True)) | (Recipe.owner_id.is_(None)))
            )
            if recipe is None:
                recipe = Recipe(
                    title=item["title"],
                    description=item["description"],
                    instructions=item["instructions"],
                    cooking_time_minutes=item["cooking_time_minutes"],
                    difficulty=item["difficulty"],
                    meal_type=item["meal_type"],
                    owner_id=None,
                    is_public=True,
                    required_ingredients=[
                        RecipeIngredient(
                            name=ingredient[0],
                            quantity=ingredient[1],
                            unit=ingredient[2],
                            is_optional=ingredient[3] if len(ingredient) > 3 else False,
                        )
                        for ingredient in item["ingredients"]
                    ],
                )
                db.add(recipe)
            else:
                recipe.description = item["description"]
                recipe.instructions = item["instructions"]
                recipe.cooking_time_minutes = item["cooking_time_minutes"]
                recipe.difficulty = item["difficulty"]
                recipe.meal_type = item["meal_type"]
                recipe.owner_id = None
                recipe.is_public = True

        db.commit()
    finally:
        db.close()

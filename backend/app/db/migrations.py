from sqlalchemy import text

from app.db.session import engine


def ensure_schema() -> None:
    statements = [
        "ALTER TABLE ingredients DROP CONSTRAINT IF EXISTS ingredients_name_key",
        "ALTER TABLE recipes DROP CONSTRAINT IF EXISTS recipes_title_key",
        "DROP INDEX IF EXISTS ix_ingredients_name",
        "DROP INDEX IF EXISTS ix_recipes_title",
        "ALTER TABLE ingredients ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE CASCADE",
        "ALTER TABLE ingredients ADD COLUMN IF NOT EXISTS description TEXT DEFAULT ''",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS meal_type VARCHAR(30) DEFAULT 'lunch'",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS owner_id INTEGER REFERENCES users(id) ON DELETE CASCADE",
        "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS is_public BOOLEAN DEFAULT FALSE",
        "UPDATE recipes SET is_public = TRUE WHERE owner_id IS NULL",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_user_ingredient_name ON ingredients (user_id, name)",
        "CREATE INDEX IF NOT EXISTS ix_recipes_meal_type ON recipes (meal_type)",
        "CREATE INDEX IF NOT EXISTS ix_recipes_owner_id ON recipes (owner_id)",
        "CREATE INDEX IF NOT EXISTS ix_recipes_is_public ON recipes (is_public)",
    ]

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))

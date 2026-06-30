import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Clock, Search } from 'lucide-react';

import { MEAL_TYPES } from '../constants';
import type { MealType, Recipe } from '../types';

type RecipesPageProps = {
  recipes: Recipe[];
};

function RecipesPage({ recipes }: RecipesPageProps) {
  const [query, setQuery] = useState('');
  const [mealType, setMealType] = useState<MealType | 'all'>('all');

  const filteredRecipes = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();

    return recipes.filter((recipe) => {
      const matchesMeal = mealType === 'all' || recipe.meal_type === mealType;
      const searchableText = [
        recipe.title,
        recipe.description,
        recipe.meal_type,
        recipe.required_ingredients.map((ingredient) => ingredient.name).join(' '),
      ]
        .join(' ')
        .toLowerCase();
      return matchesMeal && searchableText.includes(normalizedQuery);
    });
  }, [mealType, query, recipes]);

  return (
    <section className="recipes-catalog-page">
      <div className="panel catalog-hero">
        <p className="eyebrow">Recipe catalogue</p>
        <h1>Browse recipes before stocking your pantry.</h1>
        <p className="muted">
          New users can inspect every available recipe, see exact required ingredients, and decide what products they should add to their pantry.
        </p>

        <div className="catalog-controls">
          <label className="finder-search">
            Search recipes
            <span>
              <Search size={17} />
              <input
                placeholder="Search by recipe or ingredient..."
                value={query}
                onChange={(event) => setQuery(event.target.value)}
              />
            </span>
          </label>
          <label>
            Meal type
            <select value={mealType} onChange={(event) => setMealType(event.target.value as MealType | 'all')}>
              <option value="all">All meal types</option>
              {MEAL_TYPES.map((meal) => (
                <option key={meal} value={meal}>
                  {meal}
                </option>
              ))}
            </select>
          </label>
        </div>
      </div>

      <div className="catalog-grid">
        {filteredRecipes.map((recipe) => (
          <article className="recipe-card catalog-card" key={recipe.id}>
            <div className="recipe-card-header">
              <div>
                <span className="pill">{recipe.meal_type}</span>
                <h2>{recipe.title}</h2>
                <p>{recipe.description}</p>
              </div>
            </div>

            <div className="meta-row">
              <span>
                <Clock size={15} />
                {recipe.cooking_time_minutes} min
              </span>
              <span>{recipe.difficulty}</span>
              {!recipe.is_public && <span>Your recipe</span>}
            </div>

            <h3>Required ingredients</h3>
            <div className="ingredient-tags">
              {recipe.required_ingredients.map((ingredient) => (
                <span className="tag tag-info" key={ingredient.id}>
                  {ingredient.name}: {ingredient.quantity} {ingredient.unit}
                  {ingredient.is_optional ? ' optional' : ''}
                </span>
              ))}
            </div>

            <Link className="primary-link compact" to={`/recipes/${recipe.id}`}>
              View recipe
            </Link>
          </article>
        ))}
      </div>

      {filteredRecipes.length === 0 && (
        <div className="empty-state">
          <Search size={28} />
          <h2>No recipes found</h2>
          <p>Try another search term or meal type.</p>
        </div>
      )}
    </section>
  );
}

export default RecipesPage;

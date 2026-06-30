import { FormEvent, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Check, Clock, Search, X } from 'lucide-react';

import { findRecipeMatches, getRecipeMatches } from '../api';
import { MEAL_TYPES, PRODUCT_CATEGORIES } from '../constants';
import type { Ingredient, MealType, RecipeMatch } from '../types';

type RecipeFinderPageProps = {
  ingredients: Ingredient[];
};

const MAX_RECOMMENDATIONS_PER_SECTION = 3;

function getRandomSample<T>(items: T[], limit: number) {
  return [...items].sort(() => Math.random() - 0.5).slice(0, limit);
}

function RecipeCard({ match }: { match: RecipeMatch }) {
  return (
    <article className="recipe-card">
      <div className="recipe-card-header">
        <div>
          <span className="pill">{match.recipe.meal_type}</span>
          <h2>{match.recipe.title}</h2>
          <p>{match.recipe.description}</p>
        </div>
        <span className="score">{match.match_percentage}%</span>
      </div>
      <div className="meta-row">
        <span>
          <Clock size={15} />
          {match.recipe.cooking_time_minutes} min
        </span>
        <span>{match.recipe.difficulty}</span>
        <span>{match.can_prepare ? 'Ready to prepare' : 'Missing stock'}</span>
      </div>
      <div className="progress-track">
        <div style={{ width: `${match.match_percentage}%` }} />
      </div>
      <div className="ingredient-tags">
        {match.matched_ingredients.map((ingredient) => (
          <span className="tag tag-success" key={ingredient}>
            selected {ingredient}
          </span>
        ))}
        {match.pantry_available_ingredients.map((ingredient) => (
          <span className="tag tag-info" key={ingredient}>
            available in pantry {ingredient}
          </span>
        ))}
        {match.low_stock_ingredients.map((ingredient) => (
          <span className="tag tag-warning" key={ingredient}>
            low stock {ingredient}
          </span>
        ))}
        {match.missing_ingredients.map((ingredient) => (
          <span className="tag tag-missing" key={ingredient}>
            missing {ingredient}
          </span>
        ))}
      </div>
      <Link className="primary-link compact" to={`/recipes/${match.recipe.id}`}>
        Prepare
      </Link>
    </article>
  );
}

function RecipeFinderPage({ ingredients }: RecipeFinderPageProps) {
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [mealType, setMealType] = useState<MealType>('dinner');
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('All');
  const [selectedMatches, setSelectedMatches] = useState<RecipeMatch[]>([]);
  const [recommendedMatches, setRecommendedMatches] = useState<RecipeMatch[]>([]);
  const [hasSearched, setHasSearched] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectedIngredients = useMemo(
    () => ingredients.filter((ingredient) => selectedIds.includes(ingredient.id)),
    [ingredients, selectedIds],
  );

  const filteredIngredients = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();

    return ingredients.filter((ingredient) => {
      const matchesQuery = [ingredient.name, ingredient.category, ingredient.description]
        .join(' ')
        .toLowerCase()
        .includes(normalizedQuery);
      const matchesCategory = category === 'All' || ingredient.category === category;
      return matchesQuery && matchesCategory;
    });
  }, [category, ingredients, query]);

  const usefulSelectedMatches = useMemo(
    () => selectedMatches.filter((match) => match.match_percentage > 0),
    [selectedMatches],
  );
  const selectedRecommendations = useMemo(
    () => getRandomSample(usefulSelectedMatches, MAX_RECOMMENDATIONS_PER_SECTION),
    [usefulSelectedMatches],
  );

  const readyRecommendedMatches = useMemo(
    () => recommendedMatches.filter((match) => match.can_prepare),
    [recommendedMatches],
  );
  const readyRecommendations = useMemo(
    () => getRandomSample(readyRecommendedMatches, MAX_RECOMMENDATIONS_PER_SECTION),
    [readyRecommendedMatches],
  );

  const extraIngredientRecommendations = useMemo(
    () =>
      recommendedMatches.filter(
        (match) =>
          !match.can_prepare && (match.missing_ingredients.length > 0 || match.low_stock_ingredients.length > 0),
      ),
    [recommendedMatches],
  );
  const planningRecommendations = useMemo(
    () => getRandomSample(extraIngredientRecommendations, MAX_RECOMMENDATIONS_PER_SECTION),
    [extraIngredientRecommendations],
  );

  function toggleIngredient(id: number) {
    setSelectedIds((current) =>
      current.includes(id) ? current.filter((item) => item !== id) : [...current, id],
    );
  }

  async function handleFind(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setHasSearched(true);

    try {
      const [selectedData, recommendedData] = await Promise.all([
        selectedIds.length > 0
          ? findRecipeMatches({ ingredient_ids: selectedIds, meal_type: mealType })
          : Promise.resolve([]),
        getRecipeMatches(mealType),
      ]);
      setSelectedMatches(selectedData);
      setRecommendedMatches(recommendedData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not find recipes');
    }
  }

  return (
    <section className="finder-page">
      <div className="panel finder-control-panel">
        <p className="eyebrow">Recipe finder</p>
        <h1>Build a cooking basket</h1>
        <p className="muted">
          Search your pantry, select ingredients for a specific idea, then compare those results with pantry-wide recommendations.
        </p>

        {error && <div className="alert">{error}</div>}

        <form className="stack-form" onSubmit={handleFind}>
          <label>
            Meal type
            <select value={mealType} onChange={(event) => setMealType(event.target.value as MealType)}>
              {MEAL_TYPES.map((meal) => (
                <option key={meal} value={meal}>
                  {meal}
                </option>
              ))}
            </select>
          </label>

          <label className="finder-search">
            Search pantry
            <span>
              <Search size={17} />
              <input
                placeholder="Try pasta, cheese, vegetables..."
                value={query}
                onChange={(event) => setQuery(event.target.value)}
              />
            </span>
          </label>

          <label>
            Category
            <select value={category} onChange={(event) => setCategory(event.target.value)}>
              <option value="All">All categories</option>
              {PRODUCT_CATEGORIES.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </label>

          <div className="selected-tray">
            <div className="section-heading compact-heading">
              <h2>Selected ingredients</h2>
              <span className="pill">{selectedIds.length} selected</span>
            </div>
            {selectedIngredients.length === 0 ? (
              <p className="muted">No ingredients selected yet. Recommendations can still use your full pantry.</p>
            ) : (
              <div className="ingredient-tags tight-tags">
                {selectedIngredients.map((ingredient) => (
                  <button
                    className="selected-chip"
                    key={ingredient.id}
                    onClick={() => toggleIngredient(ingredient.id)}
                    type="button"
                  >
                    {ingredient.name}
                    <X size={14} />
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="ingredient-picker">
            {filteredIngredients.map((ingredient) => {
              const isSelected = selectedIds.includes(ingredient.id);
              return (
                <button
                  className={`ingredient-card-button ${isSelected ? 'selected' : ''}`}
                  key={ingredient.id}
                  onClick={() => toggleIngredient(ingredient.id)}
                  type="button"
                >
                  <span>
                    <strong>{ingredient.name}</strong>
                    <small>{ingredient.category}</small>
                  </span>
                  <span className="stock-badge">
                    {ingredient.quantity} {ingredient.unit}
                  </span>
                  {isSelected && (
                    <span className="selected-check">
                      <Check size={15} />
                    </span>
                  )}
                </button>
              );
            })}
          </div>

          <div className="finder-actions">
            <button className="secondary-button" onClick={() => setSelectedIds([])} type="button">
              Clear
            </button>
            <button
              className="secondary-button"
              onClick={() => setSelectedIds(filteredIngredients.map((ingredient) => ingredient.id))}
              type="button"
            >
              Select visible
            </button>
            <button className="primary-button" type="submit">
              <Search size={18} />
              Find recipes
            </button>
          </div>
        </form>
      </div>

      <div className="recipe-results split-results">
        <section>
          <div className="section-heading results-heading">
            <div>
              <p className="eyebrow">Selected basket</p>
              <h2>Recipes from selected ingredients</h2>
            </div>
            {usefulSelectedMatches.length > 0 && (
              <span className="pill">
                showing {selectedRecommendations.length} of {usefulSelectedMatches.length}
              </span>
            )}
          </div>

          {!hasSearched ? (
            <div className="empty-state compact-empty">
              <Search size={24} />
              <h2>No search yet</h2>
              <p>Select ingredients or search directly for pantry-wide recommendations.</p>
            </div>
          ) : usefulSelectedMatches.length === 0 ? (
            <div className="empty-state compact-empty">
              <Search size={24} />
              <h2>No selected-ingredient recipes found</h2>
              <p>Try selecting more ingredients or use the recommendations below based on your full pantry.</p>
            </div>
          ) : (
            <div className="recipe-grid">
              {selectedRecommendations.map((match) => (
                <RecipeCard key={match.recipe.id} match={match} />
              ))}
            </div>
          )}
        </section>

        <section>
          <div className="section-heading results-heading">
            <div>
              <p className="eyebrow">Pantry recommendations</p>
              <h2>Ready from available pantry stock</h2>
            </div>
            {readyRecommendedMatches.length > 0 && (
              <span className="pill">
                showing {readyRecommendations.length} of {readyRecommendedMatches.length}
              </span>
            )}
          </div>

          {!hasSearched ? (
            <div className="empty-state compact-empty">
              <Search size={24} />
              <h2>Recommendations waiting</h2>
              <p>Run a search to see recipes you can prepare from your pantry.</p>
            </div>
          ) : readyRecommendedMatches.length === 0 ? (
            <div className="empty-state compact-empty">
              <Search size={24} />
              <h2>No ready recipes yet</h2>
              <p>Your pantry does not currently contain enough stock for this meal type. Check the ideas below for what to add.</p>
            </div>
          ) : (
            <div className="recipe-grid">
              {readyRecommendations.map((match) => (
                <RecipeCard key={match.recipe.id} match={match} />
              ))}
            </div>
          )}
        </section>

        <section>
          <div className="section-heading results-heading">
            <div>
              <p className="eyebrow">Needs extra ingredients</p>
              <h2>Recommended recipes to plan for</h2>
            </div>
            {extraIngredientRecommendations.length > 0 && (
              <span className="pill">
                showing {planningRecommendations.length} of {extraIngredientRecommendations.length}
              </span>
            )}
          </div>

          {!hasSearched ? (
            <div className="empty-state compact-empty">
              <Search size={24} />
              <h2>Planning ideas waiting</h2>
              <p>Run a search to see recipes that need extra pantry products.</p>
            </div>
          ) : extraIngredientRecommendations.length === 0 ? (
            <div className="empty-state compact-empty">
              <Search size={24} />
              <h2>No missing-ingredient ideas</h2>
              <p>Nice, every recommendation for this meal type is already covered by your pantry.</p>
            </div>
          ) : (
            <div className="recipe-grid">
              {planningRecommendations.map((match) => (
                <RecipeCard key={match.recipe.id} match={match} />
              ))}
            </div>
          )}
        </section>
      </div>
    </section>
  );
}

export default RecipeFinderPage;

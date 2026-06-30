import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { CheckCircle2, Clock } from 'lucide-react';

import { finishRecipe, getRecipe } from '../api';
import type { PreparationResult, Recipe } from '../types';

type RecipeDetailPageProps = {
  onRefresh: () => Promise<void>;
};

function RecipeDetailPage({ onRefresh }: RecipeDetailPageProps) {
  const { id } = useParams();
  const recipeId = Number(id);
  const [recipe, setRecipe] = useState<Recipe | null>(null);
  const [result, setResult] = useState<PreparationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!recipeId) {
      return;
    }

    getRecipe(recipeId)
      .then(setRecipe)
      .catch((err: Error) => setError(err.message));
  }, [recipeId]);

  async function handleFinish() {
    setError(null);
    try {
      const data = await finishRecipe(recipeId);
      setResult(data);
      await onRefresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not finish recipe');
    }
  }

  if (!recipe) {
    return <div className="panel">Loading recipe...</div>;
  }

  const preparationSteps = recipe.instructions
    .split('\n')
    .map((step) => step.replace(/^\d+\.\s*/, '').trim())
    .filter(Boolean);

  return (
    <section className="detail-page">
      <div className="panel">
        <span className="pill">{recipe.meal_type}</span>
        <h1>{recipe.title}</h1>
        <p className="muted">{recipe.description}</p>
        <div className="meta-row">
          <span>
            <Clock size={15} />
            {recipe.cooking_time_minutes} min
          </span>
          <span>{recipe.difficulty}</span>
        </div>

        {error && <div className="alert">{error}</div>}
        {result && (
          <div className="success-box">
            <CheckCircle2 size={20} />
            Finished {result.recipe_title}. Pantry quantities were updated.
          </div>
        )}

        <div className="detail-actions">
          <button className="primary-button" onClick={handleFinish} type="button">
            Finish and update stock
          </button>
          <Link className="secondary-link" to="/find">
            Back to finder
          </Link>
        </div>
      </div>

      <div className="panel">
        <h2>Exact ingredients</h2>
        <div className="list-stack">
          {recipe.required_ingredients.map((ingredient) => (
            <article className="ingredient-row" key={ingredient.id}>
              <div>
                <strong>{ingredient.name}</strong>
                <p>
                  {ingredient.quantity} {ingredient.unit}
                  {ingredient.is_optional ? ' - optional' : ''}
                </p>
              </div>
            </article>
          ))}
        </div>

        <h2>Preparation steps</h2>
        <ol className="preparation-list">
          {preparationSteps.map((step) => (
            <li key={step}>{step}</li>
          ))}
        </ol>

        {result && (
          <>
            <h2>Remaining stock</h2>
            <div className="ingredient-tags">
              {result.remaining_ingredients.map((ingredient) => (
                <span className="tag tag-success" key={ingredient.id}>
                  {ingredient.name}: {ingredient.quantity} {ingredient.unit}
                </span>
              ))}
            </div>
          </>
        )}
      </div>
    </section>
  );
}

export default RecipeDetailPage;

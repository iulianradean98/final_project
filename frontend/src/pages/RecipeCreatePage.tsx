import { FormEvent, useState } from 'react';
import { Plus, Trash2 } from 'lucide-react';

import { createRecipe } from '../api';
import { MEAL_TYPES, MEASURE_UNITS } from '../constants';
import type { MealType, RecipeIngredientPayload } from '../types';

const emptyIngredient: RecipeIngredientPayload = {
  name: '',
  quantity: 1,
  unit: 'g',
  is_optional: false,
};

type RecipeCreatePageProps = {
  onCreated: () => Promise<void>;
};

function RecipeCreatePage({ onCreated }: RecipeCreatePageProps) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [instructions, setInstructions] = useState('');
  const [cookingTime, setCookingTime] = useState(20);
  const [difficulty, setDifficulty] = useState('Easy');
  const [mealType, setMealType] = useState<MealType>('dinner');
  const [ingredients, setIngredients] = useState<RecipeIngredientPayload[]>([{ ...emptyIngredient }]);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  function updateIngredient(index: number, update: Partial<RecipeIngredientPayload>) {
    setIngredients((current) =>
      current.map((ingredient, itemIndex) =>
        itemIndex === index ? { ...ingredient, ...update } : ingredient,
      ),
    );
  }

  function removeIngredient(index: number) {
    setIngredients((current) => current.filter((_, itemIndex) => itemIndex !== index));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setMessage(null);

    try {
      const recipe = await createRecipe({
        title,
        description,
        instructions,
        cooking_time_minutes: cookingTime,
        difficulty,
        meal_type: mealType,
        required_ingredients: ingredients.map((ingredient) => ({
          ...ingredient,
          name: ingredient.name.trim().toLowerCase(),
          quantity: Number(ingredient.quantity),
        })),
      });
      setMessage(`${recipe.title} was added successfully.`);
      setTitle('');
      setDescription('');
      setInstructions('');
      setIngredients([{ ...emptyIngredient }]);
      await onCreated();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not create recipe');
    }
  }

  return (
    <section className="panel wide-panel">
      <p className="eyebrow">Recipes</p>
      <h1>Add a new recipe</h1>
      <p className="muted">
        Custom recipes become part of the same REST API and PostgreSQL data model as the seeded recipes.
      </p>

      {error && <div className="alert">{error}</div>}
      {message && <div className="success-box">{message}</div>}

      <form className="stack-form" onSubmit={handleSubmit}>
        <div className="form-grid">
          <label>
            Title
            <input required value={title} onChange={(event) => setTitle(event.target.value)} />
          </label>
          <label>
            Best meal type
            <select value={mealType} onChange={(event) => setMealType(event.target.value as MealType)}>
              {MEAL_TYPES.map((meal) => (
                <option key={meal} value={meal}>
                  {meal}
                </option>
              ))}
            </select>
          </label>
        </div>
        <label>
          Description
          <textarea required rows={3} value={description} onChange={(event) => setDescription(event.target.value)} />
        </label>
        <label>
          Instructions
          <textarea required rows={5} value={instructions} onChange={(event) => setInstructions(event.target.value)} />
        </label>
        <div className="form-grid">
          <label>
            Cooking time
            <input
              min="1"
              required
              type="number"
              value={cookingTime}
              onChange={(event) => setCookingTime(Number(event.target.value))}
            />
          </label>
          <label>
            Difficulty
            <select value={difficulty} onChange={(event) => setDifficulty(event.target.value)}>
              <option>Easy</option>
              <option>Medium</option>
              <option>Hard</option>
            </select>
          </label>
        </div>

        <div className="section-heading">
          <h2>Ingredients</h2>
          <button
            className="secondary-button"
            onClick={() => setIngredients((current) => [...current, { ...emptyIngredient }])}
            type="button"
          >
            <Plus size={17} />
            Add row
          </button>
        </div>

        <div className="list-stack">
          {ingredients.map((ingredient, index) => (
            <div className="ingredient-editor" key={index}>
              <input
                required
                placeholder="Ingredient"
                value={ingredient.name}
                onChange={(event) => updateIngredient(index, { name: event.target.value })}
              />
              <input
                min="0"
                required
                step="0.1"
                type="number"
                value={ingredient.quantity}
                onChange={(event) => updateIngredient(index, { quantity: Number(event.target.value) })}
              />
              <select value={ingredient.unit} onChange={(event) => updateIngredient(index, { unit: event.target.value })}>
                {MEASURE_UNITS.map((unit) => (
                  <option key={unit.value} value={unit.value}>
                    {unit.label}
                  </option>
                ))}
              </select>
              <label className="inline-check">
                <input
                  checked={ingredient.is_optional}
                  onChange={(event) => updateIngredient(index, { is_optional: event.target.checked })}
                  type="checkbox"
                />
                Optional
              </label>
              <button className="icon-button" onClick={() => removeIngredient(index)} type="button">
                <Trash2 size={16} />
              </button>
            </div>
          ))}
        </div>

        <button className="primary-button" type="submit">
          Save recipe
        </button>
      </form>
    </section>
  );
}

export default RecipeCreatePage;

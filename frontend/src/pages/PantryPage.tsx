import { FormEvent, useState } from 'react';
import { Plus, Trash2 } from 'lucide-react';

import { createIngredient, deleteIngredient } from '../api';
import { DEFAULT_INGREDIENT_FORM, MEASURE_UNITS, PRODUCT_CATEGORIES } from '../constants';
import type { Ingredient } from '../types';

type PantryPageProps = {
  ingredients: Ingredient[];
  onRefresh: () => Promise<void>;
};

function PantryPage({ ingredients, onRefresh }: PantryPageProps) {
  const [form, setForm] = useState(DEFAULT_INGREDIENT_FORM);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    try {
      await createIngredient({
        name: form.name.trim().toLowerCase(),
        category: form.category,
        description: form.description,
        quantity: Number(form.quantity),
        unit: form.unit,
        expires_on: form.expires_on || null,
      });
      setForm(DEFAULT_INGREDIENT_FORM);
      await onRefresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not add ingredient');
    }
  }

  async function handleDelete(id: number) {
    setError(null);
    try {
      await deleteIngredient(id);
      await onRefresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not delete ingredient');
    }
  }

  return (
    <section className="page-grid">
      <div className="panel">
        <p className="eyebrow">Pantry</p>
        <h1>Ingredients inventory</h1>
        <p className="muted">
          Add food with quantity, measure unit, description, and expiry date. These quantities are used later when a recipe is prepared.
        </p>

        {error && <div className="alert">{error}</div>}

        <form className="stack-form" onSubmit={handleSubmit}>
          <label>
            Ingredient name
            <input
              required
              minLength={2}
              value={form.name}
              onChange={(event) => setForm({ ...form, name: event.target.value })}
            />
          </label>
          <div className="form-grid">
            <label>
              Quantity
              <input
                required
                min="0"
                step="0.1"
                type="number"
                value={form.quantity}
                onChange={(event) => setForm({ ...form, quantity: Number(event.target.value) })}
              />
            </label>
            <label>
              Measure unit
              <select
                value={form.unit}
                onChange={(event) => setForm({ ...form, unit: event.target.value })}
              >
                {MEASURE_UNITS.map((unit) => (
                  <option key={unit.value} value={unit.value}>
                    {unit.label}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <label>
            Category
            <select
              value={form.category}
              onChange={(event) => setForm({ ...form, category: event.target.value })}
            >
              {PRODUCT_CATEGORIES.map((category) => (
                <option key={category} value={category}>
                  {category}
                </option>
              ))}
            </select>
          </label>
          <label>
            Description
            <textarea
              rows={3}
              value={form.description}
              onChange={(event) => setForm({ ...form, description: event.target.value })}
            />
          </label>
          <label>
            Expiry date
            <input
              type="date"
              value={form.expires_on}
              onChange={(event) => setForm({ ...form, expires_on: event.target.value })}
            />
          </label>
          <button className="primary-button" type="submit">
            <Plus size={18} />
            Add ingredient
          </button>
        </form>
      </div>

      <div className="panel">
        <div className="section-heading">
          <h2>Current stock</h2>
          <span className="pill">{ingredients.length} items</span>
        </div>

        <div className="list-stack">
          {ingredients.map((ingredient) => (
            <article className="ingredient-row" key={ingredient.id}>
              <div>
                <strong>{ingredient.name}</strong>
                <p>
                  {ingredient.quantity} {ingredient.unit} - {ingredient.category}
                </p>
                {ingredient.description && <small>{ingredient.description}</small>}
                {ingredient.expires_on && <small>Expires on {ingredient.expires_on}</small>}
              </div>
              <button className="icon-button" onClick={() => handleDelete(ingredient.id)} type="button">
                <Trash2 size={17} />
              </button>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

export default PantryPage;

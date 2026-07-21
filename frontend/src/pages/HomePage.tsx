import { Link } from 'react-router-dom';
import { ArrowRight, ChefHat, ClipboardList, Search, Sparkles, Timer, Utensils } from 'lucide-react';

type HomePageProps = {
  isAuthenticated: boolean;
  pantryCount: number;
  recipeCount: number;
};

const workflowSteps = [
  {
    title: 'Stock your pantry',
    text: 'Add real ingredients with quantities, units, descriptions, and expiry dates.',
  },
  {
    title: 'Choose what to use',
    text: 'Search your pantry, select ingredients, and pick a meal type.',
  },
  {
    title: 'Prepare a recipe',
    text: 'Open a match, follow detailed steps, and finish it to update stock automatically.',
  },
];

const mealCards = [
  { label: 'Breakfast', text: 'Fast bowls, eggs, pancakes, and toast ideas.' },
  { label: 'Lunch', text: 'Balanced bowls, wraps, and warm midday meals.' },
  { label: 'Dinner', text: 'Comfort food and complete evening meals.' },
  { label: 'Snack', text: 'Small recipes for quick hunger fixes.' },
];

function HomePage({ isAuthenticated, pantryCount, recipeCount }: HomePageProps) {
  return (
    <section className="home-page">
      <div className="home-hero">
        <div className="hero-content">
          <p className="eyebrow">Recipe Rescue</p>
          <h1>Turn pantry stock into realistic meal choices.</h1>
          <p className="hero-copy">
            Track ingredients, filter recipes by meal type, prepare one recipe, and let the database automatically subtract the exact quantities used.
          </p>
          <div className="hero-actions">
            <Link className="primary-link" to={isAuthenticated ? '/find' : '/login'}>
              {isAuthenticated ? 'Start cooking' : 'Log in to start'}
              <ArrowRight size={18} />
            </Link>
            <Link className="secondary-link" to="/recipes">
              Browse recipes
            </Link>
          </div>
        </div>

        <aside className="hero-dashboard" aria-label="Application summary">
          <div className="dashboard-card highlight-card">
            <Sparkles size={20} />
            <span>Smart match engine</span>
            <strong>Quantity-aware</strong>
          </div>
          <div className="dashboard-grid">
            <div className="dashboard-card">
              <ClipboardList size={20} />
              <strong>{pantryCount}</strong>
              <span>pantry items</span>
            </div>
            <div className="dashboard-card">
              <ChefHat size={20} />
              <strong>{recipeCount}</strong>
              <span>recipes</span>
            </div>
          </div>
        </aside>
      </div>

      <section className="home-section">
        <div className="section-heading">
          <div>
            <p className="eyebrow">How it works</p>
            <h2>One simple flow from pantry to plate</h2>
          </div>
          <Link className="secondary-link compact" to={isAuthenticated ? '/recipes/new' : '/login'}>
            Add custom recipe
          </Link>
        </div>

        <div className="workflow-grid">
          {workflowSteps.map((step, index) => (
            <article key={step.title}>
              <span className="step-number">0{index + 1}</span>
              <h3>{step.title}</h3>
              <p>{step.text}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="home-section split-section">
        <div>
          <p className="eyebrow">Meal planning</p>
          <h2>Designed around the question people actually ask</h2>
          <p className="muted">
            The app does not just list recipes. It starts from the ingredients you choose and answers: what can I make now, and what am I missing?
          </p>
        </div>

        <div className="meal-grid">
          {mealCards.map((meal) => (
            <article key={meal.label}>
              <Utensils size={20} />
              <h3>{meal.label}</h3>
              <p>{meal.text}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="feature-grid">
        <article>
          <Search size={22} />
          <h2>Modern ingredient picker</h2>
          <p>Search, filter by category, select only what you want to use, and review your basket before matching.</p>
        </article>
        <article>
          <Timer size={22} />
          <h2>Detailed preparation</h2>
          <p>Recipe pages show exact quantities and step-by-step instructions before stock is deducted.</p>
        </article>
        <article>
          <ClipboardList size={22} />
          <h2>Pantry planning</h2>
          <p>See what you can cook today and which ingredients are worth adding before your next grocery trip.</p>
        </article>
      </section>
    </section>
  );
}

export default HomePage;

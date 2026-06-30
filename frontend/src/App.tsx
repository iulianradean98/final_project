import { ReactNode, useEffect, useState } from 'react';
import { Navigate, NavLink, Route, Routes } from 'react-router-dom';
import { ChefHat, LogOut } from 'lucide-react';

import { clearStoredToken, getCurrentUser, getIngredients, getRecipes, getStoredToken } from './api';
import AuthPage from './pages/AuthPage';
import HomePage from './pages/HomePage';
import PantryPage from './pages/PantryPage';
import RecipeCreatePage from './pages/RecipeCreatePage';
import RecipeDetailPage from './pages/RecipeDetailPage';
import RecipeFinderPage from './pages/RecipeFinderPage';
import RecipesPage from './pages/RecipesPage';
import type { Ingredient, Recipe, User } from './types';

function App() {
  const [user, setUser] = useState<User | null>(null);
  const [ingredients, setIngredients] = useState<Ingredient[]>([]);
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadData() {
    setError(null);
    const [ingredientData, recipeData] = await Promise.all([
      user ? getIngredients() : Promise.resolve([]),
      getRecipes(),
    ]);
    setIngredients(ingredientData);
    setRecipes(recipeData);
  }

  async function handleAuthenticated(authenticatedUser: User) {
    setUser(authenticatedUser);
    const [ingredientData, recipeData] = await Promise.all([getIngredients(), getRecipes()]);
    setIngredients(ingredientData);
    setRecipes(recipeData);
  }

  function handleLogout() {
    clearStoredToken();
    setUser(null);
    setIngredients([]);
  }

  useEffect(() => {
    async function initialize() {
      try {
        const token = getStoredToken();
        if (token) {
          const authenticatedUser = await getCurrentUser();
          setUser(authenticatedUser);
          const [ingredientData, recipeData] = await Promise.all([getIngredients(), getRecipes()]);
          setIngredients(ingredientData);
          setRecipes(recipeData);
        } else {
          setRecipes(await getRecipes());
        }
      } catch (err) {
        clearStoredToken();
        setUser(null);
        setIngredients([]);
        setRecipes(await getRecipes());
        setError(err instanceof Error ? err.message : 'Could not load application data');
      } finally {
        setIsLoading(false);
      }
    }

    initialize();
  }, []);

  function protectedPage(element: ReactNode) {
    return user ? element : <Navigate replace to="/login" />;
  }

  return (
    <div>
      <header className="app-header">
        <NavLink className="brand" to="/">
          <ChefHat size={24} />
          Recipe Rescue
        </NavLink>
        <nav>
          <NavLink to="/">Home</NavLink>
          <NavLink to="/recipes">Recipes</NavLink>
          {user && <NavLink to="/pantry">Pantry</NavLink>}
          {user && <NavLink to="/find">Find Recipes</NavLink>}
          {user && <NavLink to="/recipes/new">Add Recipe</NavLink>}
          {!user && <NavLink to="/login">Log In</NavLink>}
          {!user && <NavLink to="/signup">Sign Up</NavLink>}
        </nav>
        {user && (
          <div className="user-menu">
            <span>{user.full_name}</span>
            <button className="icon-text-button" onClick={handleLogout} type="button">
              <LogOut size={16} />
              Logout
            </button>
          </div>
        )}
      </header>

      <main className="app-shell">
        {error && <div className="alert">{error}</div>}
        {isLoading ? (
          <div className="panel">Loading Recipe Rescue...</div>
        ) : (
          <Routes>
            <Route
              path="/"
              element={
                <HomePage
                  isAuthenticated={Boolean(user)}
                  pantryCount={ingredients.length}
                  recipeCount={recipes.length}
                />
              }
            />
            <Route path="/login" element={<AuthPage mode="login" onAuthenticated={handleAuthenticated} />} />
            <Route path="/signup" element={<AuthPage mode="signup" onAuthenticated={handleAuthenticated} />} />
            <Route path="/recipes" element={<RecipesPage recipes={recipes} />} />
            <Route path="/pantry" element={protectedPage(<PantryPage ingredients={ingredients} onRefresh={loadData} />)} />
            <Route path="/find" element={protectedPage(<RecipeFinderPage ingredients={ingredients} />)} />
            <Route path="/recipes/new" element={protectedPage(<RecipeCreatePage onCreated={loadData} />)} />
            <Route path="/recipes/:id" element={<RecipeDetailPage onRefresh={loadData} />} />
          </Routes>
        )}
      </main>
    </div>
  );
}

export default App;

import type {
  Ingredient,
  IngredientPayload,
  AuthResponse,
  LoginPayload,
  MealType,
  PreparationResult,
  Recipe,
  RecipeMatch,
  RecipeMatchPayload,
  RecipePayload,
  SignupPayload,
  User,
} from './types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api';
const TOKEN_KEY = 'recipe-rescue-token';

export function getStoredToken(): string | null {
  return window.localStorage.getItem(TOKEN_KEY);
}

export function storeToken(token: string): void {
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearStoredToken(): void {
  window.localStorage.removeItem(TOKEN_KEY);
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const token = getStoredToken();
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const message = await response.text();
    let parsedDetail: string | undefined;
    try {
      const parsed = JSON.parse(message) as { detail?: string };
      parsedDetail = parsed.detail;
    } catch {
      parsedDetail = undefined;
    }
    throw new Error(parsedDetail || message || `Request failed with status ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export function getIngredients(): Promise<Ingredient[]> {
  return request<Ingredient[]>('/ingredients');
}

export function signup(payload: SignupPayload): Promise<AuthResponse> {
  return request<AuthResponse>('/auth/signup', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function login(payload: LoginPayload): Promise<AuthResponse> {
  return request<AuthResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function getCurrentUser(): Promise<User> {
  return request<User>('/auth/me');
}

export function createIngredient(payload: IngredientPayload): Promise<Ingredient> {
  return request<Ingredient>('/ingredients', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function deleteIngredient(id: number): Promise<void> {
  return request<void>(`/ingredients/${id}`, { method: 'DELETE' });
}

export function getRecipeMatches(mealType?: MealType): Promise<RecipeMatch[]> {
  const params = mealType ? `?meal_type=${mealType}` : '';
  return request<RecipeMatch[]>(`/recipes/matches${params}`);
}

export function findRecipeMatches(payload: RecipeMatchPayload): Promise<RecipeMatch[]> {
  return request<RecipeMatch[]>('/recipes/matches', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function getRecipes(mealType?: MealType): Promise<Recipe[]> {
  const params = mealType ? `?meal_type=${mealType}` : '';
  return request<Recipe[]>(`/recipes${params}`);
}

export function getRecipe(id: number): Promise<Recipe> {
  return request<Recipe>(`/recipes/${id}`);
}

export function createRecipe(payload: RecipePayload): Promise<Recipe> {
  return request<Recipe>('/recipes', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function finishRecipe(id: number): Promise<PreparationResult> {
  return request<PreparationResult>(`/recipes/${id}/finish`, { method: 'POST' });
}

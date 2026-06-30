export type Ingredient = {
  id: number;
  name: string;
  category: string;
  description: string;
  quantity: number;
  unit: string;
  expires_on: string | null;
};

export type RecipeIngredient = {
  id: number;
  name: string;
  quantity: number;
  unit: string;
  is_optional: boolean;
};

export type Recipe = {
  id: number;
  owner_id: number | null;
  is_public: boolean;
  title: string;
  description: string;
  instructions: string;
  cooking_time_minutes: number;
  difficulty: string;
  meal_type: MealType;
  required_ingredients: RecipeIngredient[];
};

export type RecipeMatch = {
  recipe: Recipe;
  matched_ingredients: string[];
  pantry_available_ingredients: string[];
  low_stock_ingredients: string[];
  missing_ingredients: string[];
  match_percentage: number;
  can_prepare: boolean;
};

export type MealType = 'breakfast' | 'lunch' | 'dinner' | 'snack';

export type IngredientPayload = Omit<Ingredient, 'id'>;

export type RecipeIngredientPayload = Omit<RecipeIngredient, 'id'>;

export type RecipePayload = Omit<Recipe, 'id' | 'owner_id' | 'is_public' | 'required_ingredients'> & {
  required_ingredients: RecipeIngredientPayload[];
};

export type RecipeMatchPayload = {
  ingredient_ids: number[];
  meal_type: MealType | null;
};

export type PreparationResult = {
  recipe_id: number;
  recipe_title: string;
  consumed_ingredients: RecipeIngredient[];
  remaining_ingredients: Ingredient[];
};

export type User = {
  id: number;
  email: string;
  full_name: string;
};

export type AuthResponse = {
  access_token: string;
  token_type: 'bearer';
  user: User;
};

export type LoginPayload = {
  email: string;
  password: string;
};

export type SignupPayload = LoginPayload & {
  full_name: string;
};

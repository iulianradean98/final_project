import type { MealType } from './types';

export const MEAL_TYPES: MealType[] = ['breakfast', 'lunch', 'dinner', 'snack'];

export const PRODUCT_CATEGORIES = [
  'Vegetables',
  'Fruit',
  'Dairy',
  'Protein',
  'Seafood',
  'Bakery',
  'Grains & Pasta',
  'Canned & Jarred',
  'Pantry',
  'Frozen',
  'Spices & Seasoning',
  'Condiments & Sauces',
  'Beverages',
  'Snacks',
  'Other',
] as const;

export const MEASURE_UNITS = [
  { value: 'g', label: 'grams (g)' },
  { value: 'kg', label: 'kilograms (kg)' },
  { value: 'ml', label: 'milliliters (ml)' },
  { value: 'l', label: 'liters (l)' },
  { value: 'pcs', label: 'pieces' },
  { value: 'slices', label: 'slices' },
] as const;

export const DEFAULT_INGREDIENT_FORM = {
  name: '',
  category: 'Other',
  description: '',
  quantity: 1,
  unit: 'g',
  expires_on: '',
};

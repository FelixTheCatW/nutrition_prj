from dataclasses import dataclass


@dataclass
class Food:
    id: int = 0
    name: str = ""
    locale: str = ""
    calories: int = ""
    protein_g: float = 0.0
    fat_g: float = 0.0
    carbs_g: float = 0.0


@dataclass
class FoodEntry:
    id: int = 0
    eaten_at: str = ""
    date: str = ""
    servings: float = 0.0
    meal_type: str = ""
    person_id: int = 0
    food_id: int = 0

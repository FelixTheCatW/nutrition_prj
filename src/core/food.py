from dataclasses import dataclass

@dataclass
class Food:
    id: int
    name: str
    locale: str
    calories: int
    protein_g: float
    fat_g: float
    carbs_g: float
    
@dataclass
class FoodEntry:
    id: int
    eaten_at: str
    date: str
    servings: float
    meal_type: str
    person_id: int
    food_id: int
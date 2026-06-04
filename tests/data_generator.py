import random
from datetime import date

from src.core.registries import MEAL_TYPE_RULES

MEALS_BY_TYPE = {k: [] for k in MEAL_TYPE_RULES.keys()}


def generate_meal_ext(meal_t: str, target_calories: float, user_goal: str) -> []:
    meals_list = MEALS_BY_TYPE[meal_t]

    # выберите 1-3 блюда с весами
    chosen_dishes = []
    remaining_kcal = target_calories * random.uniform(0.8, 1.2)

    while remaining_kcal > 50 and len(chosen_dishes) < 4:
        dish = random.choices(meals_list, weights=[w[3] for w in meals_list], k=1)[0]
        id = dish[0]
        kcal = dish[3]
        servings = get_servings(kcal, user_goal)
        kcal_total = kcal * servings

        chosen_dishes.append((id, servings))
        remaining_kcal -= kcal_total

    return chosen_dishes


def generate_time(meal_t: str) -> str:
    match meal_t:
        case "завтрак":
            hour = random.randint(7, 10)
        case "обед":
            hour = random.randint(12, 15)
        case "ужин":
            hour = random.randint(18, 21)
        case "перекус":
            hour = random.randint(0, 23)
        case _:
            hour = 12
            minute = 0

    return f"{hour:02d}:{random.choice([0, 15, 30, 45]):02d}"


def get_servings(calories_per_serving, goal):
    base = 1
    if goal == "похудение":
        base = random.choice([0.5, 0.8, 1.0])
    elif goal == "набор мышц":
        base = random.choice([1.0, 1.2, 1.5])
    # округлите до 0.5
    max_servings = 2 if calories_per_serving > 300 else 3
    servings = min(max_servings, base + random.uniform(-0.2, 0.3))
    return round(servings * 2) / 2  # кратно 0.5

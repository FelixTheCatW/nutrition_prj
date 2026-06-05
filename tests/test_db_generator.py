import csv
from datetime import date, timedelta
from pprint import pprint

from .data_generator import generate_meal_ext, generate_time, MEALS_BY_TYPE
from src.core.food import Food, FoodEntry
from src.core.person import Person, random_person
from src.db.database import Database
from src.db.db_config import DBConfig
from src.core.registries import (
    COUNTRIES_MEALS_BY_TYPE,
    GLOBAL_MEALS_BY_TYPE,
    LOCALES,
    REPORT_FIELDS,
    MEAL_TYPES,
    COUNTRIES_FOODS,
    LOCALE_MAP,
    classify_meal_type,
)


def test_generate_food():
    rows = []

    for country, foods in COUNTRIES_FOODS.items():
        for name, values in foods.items():
            rows.append((name, LOCALE_MAP[country], *values))
    pprint(rows)
    print(len(rows))


def test_registry():
    print("COUNTRIES_MEALS_BY_TYPE")
    pprint(COUNTRIES_MEALS_BY_TYPE, width=40, sort_dicts=False)
    print("*" * 40)
    print("GLOBAL_MEALS_BY_TYPE")
    pprint(GLOBAL_MEALS_BY_TYPE, width=40, sort_dicts=False)


def test_generate_persons():
    persons = [random_person() for _ in range(20)]
    pprint(persons, width=100)


def test_fill_db():

    DBConfig.load_from_env()
    Database.initialize(DBConfig.as_dict())

    meals = []

    for country, foods in COUNTRIES_FOODS.items():
        for name, values in foods.items():
            f = Food()
            f.name = name
            f.locale = LOCALE_MAP[country]
            f.calories = values[0]
            f.protein_g = values[1]
            f.fat_g = values[2]
            f.carbs_g = values[3]
            meals.append(f)

    Database.execute("DROP TABLE IF EXISTS food")
    Database.create_table_for_class(Food)
    Database.insert_batch(meals)
    meals = Database.select(Food)

    for meal in meals:
        meal_type = classify_meal_type(meal.name)
        MEALS_BY_TYPE[meal_type].append(meal)

    persons = [random_person() for _ in range(20)]

    Database.execute("DROP TABLE IF EXISTS person")
    Database.create_table_for_class(Person)
    Database.insert_batch(persons)
    persons = Database.select(Person)

    entries = []

    current_date = date(2025, 1, 1)
    end_date = date.today()
    while current_date <= end_date:
        for user in persons:
            for meal_t in MEAL_TYPES:
                one_day_meals = generate_meal_ext(meal_t, user.target_cal_per_day, user.goal)
                when = generate_time(meal_t)
                for meal in one_day_meals:
                    if meal_t == "перекус":
                        when = generate_time(meal_t)

                    entry = FoodEntry()
                    entry.eaten_at = when
                    entry.date = current_date.strftime("%Y-%m-%d")
                    entry.servings = meal[1]
                    entry.meal_type = meal_t
                    entry.person_id = user.id
                    entry.food_id = meal[0]

                    entries.append(entry)
        current_date += timedelta(days=1)

    Database.execute("DROP TABLE IF EXISTS food_entry")
    Database.create_table_for_class(FoodEntry)
    Database.insert_batch(entries)

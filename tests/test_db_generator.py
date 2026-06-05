import csv
from datetime import date, timedelta
from pprint import pprint

from .data_generator import generate_meal_ext, generate_time
from src.core.person import Person, random_person
from src.core.registries import (
    COUNTRIES_MEALS_BY_TYPE,
    GLOBAL_MEALS_BY_TYPE,
    LOCALES,
    REPORT_FIELDS,
    MEAL_TYPES,
    COUNTRIES_FOODS,
    LOCALE_MAP,
)

def test_generate_food():
    rows = []

    for country, foods in COUNTRIES_FOODS.items():
        for name, values in foods.items():
            rows.append((name, LOCALE_MAP[country], *values))
    pprint(rows)

def test_registry():
    print("COUNTRIES_MEALS_BY_TYPE")
    pprint(COUNTRIES_MEALS_BY_TYPE, width=40, sort_dicts=False)
    print("*" * 40)
    print("GLOBAL_MEALS_BY_TYPE")
    pprint(GLOBAL_MEALS_BY_TYPE, width=40, sort_dicts=False)
    

def test_generate_persons():
    persons = [random_person() for _ in range(20)]
    pprint(persons, width=100)


def generate_and_write_to_db(persons: list[Person], start_date: date, end_date: date):
    values_to_insert = []
    current_date = start_date
    while current_date <= end_date:
        for user in persons:      
            for meal_t in MEAL_TYPES:
                one_day_meals = generate_meal_ext(meal_t, user[2] , user[3])
                when = generate_time(meal_t)
                for m in one_day_meals:
                    if meal_t == "перекус":
                        when = generate_time(meal_t)
                    val = (date.today().strftime('%Y-%m-%d'), user[0], meal_t, when, m[0], m[1])
                    values_to_insert.append(val)

        # cursor.executemany("INSERT INTO food_entry (date, user_id, meal_type, eaten_at, product_id, servings) VALUES (?, ?, ?, ?, ?, ?)", values_to_insert)
        # connection.commit()

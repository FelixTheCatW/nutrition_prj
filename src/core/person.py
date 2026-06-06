import random
from dataclasses import dataclass, field

from faker import Faker

from src.core.registries import ACTIVITY_FACTORS, ACTIVITY_LEVELS, GOALS


@dataclass
class Person:
    id: int = 0
    name: str = ""
    activity_level: str = ""
    height_cm: int = 0
    age: int = 0
    gender: str = ""
    weight_kg: float = 0.0
    goal: str = ""
    city: str = ""
    loca: str = ""

    bmr: float = 0.0
    target_cal_per_day: float = 0.0
    target_protein_g: float = 0.0
    tdee: float = 0.0


def random_person(id: int = 0, locale: str = "ru_RU") -> Person:
    fake = Faker(locale)
    gender = random.choice(["мужской", "женский"])
    if gender == "мужской":
        weight = round(random.uniform(60, 120), 1)
        name = fake.name_male()
    else:
        weight = round(random.uniform(50, 100), 1)
        name = fake.name_female()
    person = Person()
    person.id = id
    person.name = name
    person.age = random.randint(18, 70)
    person.gender = gender
    person.height_cm = random.randint(150, 195)
    person.weight_kg = weight
    person.goal = random.choice(list(GOALS.values()))
    person.activity_level = random.choice(list(ACTIVITY_LEVELS.values()))
    person.loca = locale
    person.city = fake.city()

    person.bmr = calculate_bmr(person.weight_kg, person.height_cm, person.age, person.gender)
    person.tdee = calculate_tdee(person.bmr, person.activity_level)
    person.target_cal_per_day = get_target_calories(person.tdee, person.goal)
    person.target_protein_g = get_target_protein_g(
        person.weight_kg, person.goal, person.activity_level
    )

    return person


def calculate_bmr(weight_kg, height_cm, age, gender):
    """Harris-Benedict (пересмотренный)"""
    if gender == "мужской":
        out = 88.362 + (13.397 * weight_kg) + (4.799 * height_cm) - (5.677 * age)
    else:
        out = 447.593 + (9.247 * weight_kg) + (3.098 * height_cm) - (4.330 * age)
    return round(out, 2)


def calculate_tdee(bmr, activity_level):
    return round(bmr * ACTIVITY_FACTORS[activity_level], 2)


def get_target_protein_g(weight_kg, goal, activity_level):
    base = 1.2  # для поддержания
    if goal == "похудение":
        base = 1.6
    elif goal == "набор мышц":
        base = 2.0

    extra = 0
    if activity_level in ("высокий", "очень высокий"):
        extra = 0.3
    elif activity_level == "умеренный":
        extra = 0.1

    return round(weight_kg * (base + extra), 2)


def get_target_calories(tdee, goal):
    if goal == "похудение":
        return tdee - 500
    elif goal == "набор_мышц":
        return tdee + 300
    else:  # поддержание
        return tdee

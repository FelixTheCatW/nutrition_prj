from contextlib import asynccontextmanager
from datetime import date, datetime
from decimal import Decimal
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.db.database import Database
from src.db.db_config import DBConfig


@asynccontextmanager
async def lifespan(app: FastAPI):
    DBConfig.load_from_env()
    Database.initialize(DBConfig.as_dict())
    yield


app = FastAPI(title="Nutrition Tracker API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _rows(query, params=None):
    rows = Database.fetch_all(query, params) or []
    return [_clean(dict(r)) for r in rows]


def _one(query, params=None):
    row = Database.fetch_one(query, params)
    return _clean(dict(row)) if row else None


def _clean(d: dict) -> dict:
    out = {}
    for k, v in d.items():
        if isinstance(v, (date, datetime)):
            out[k] = str(v)
        elif isinstance(v, Decimal):
            out[k] = float(v)
        else:
            out[k] = v
    return out


# ── Users ─────────────────────────────────────────────────────────────────────

@app.get("/api/users")
def get_users():
    return _rows("""
        SELECT id, name, city, gender, goal, age,
               height_cm, weight_kg, target_cal_per_day, activity_level
        FROM person ORDER BY name
    """)


# ── Reports ───────────────────────────────────────────────────────────────────

@app.get("/api/reports/personal_statistics")
def personal_statistics(user_id: int):
    info = _one("""
        SELECT p.target_cal_per_day,
               MIN(fe.date) AS start_date,
               MAX(fe.date) AS end_date
        FROM person p
        JOIN food_entry fe ON p.id = fe.person_id
        WHERE p.id = %s
        GROUP BY p.target_cal_per_day
    """, (user_id,))
    if not info:
        raise HTTPException(404, "User not found")

    daily = _rows("""
        SELECT fe.date::date AS date,
               ROUND(SUM(f.calories  * fe.servings)::numeric, 0) AS calories,
               ROUND(SUM(f.protein_g * fe.servings)::numeric, 1) AS protein,
               ROUND(SUM(f.fat_g     * fe.servings)::numeric, 1) AS fat,
               ROUND(SUM(f.carbs_g   * fe.servings)::numeric, 1) AS carbs
        FROM food_entry fe
        JOIN food f ON fe.food_id = f.id
        WHERE fe.person_id = %s
        GROUP BY fe.date::date
        ORDER BY date
    """, (user_id,))
    if not daily:
        raise HTTPException(404, "No entries")

    target   = float(info["target_cal_per_day"])
    calories = [float(r["calories"]) for r in daily]
    avg_cal  = sum(calories) / len(calories)
    proteins = [float(r["protein"]) for r in daily]
    fats     = [float(r["fat"])     for r in daily]
    carbs    = [float(r["carbs"])   for r in daily]

    return {
        "summary": {
            "period_start":  info["start_date"],
            "period_end":    info["end_date"],
            "total_days":    len(daily),
            "target_cal":    round(target),
            "avg_cal":       round(avg_cal),
            "avg_protein":   round(sum(proteins) / len(proteins), 1),
            "avg_fat":       round(sum(fats)     / len(fats),     1),
            "avg_carbs":     round(sum(carbs)    / len(carbs),    1),
            "deviation":     round(avg_cal - target),
            "pct_of_target": round((avg_cal / target) * 100, 1),
        },
        "chart_data": [
            {"date": r["date"], "calories": float(r["calories"]), "target": round(target)}
            for r in daily[-60:]
        ],
        "table_data": daily[-15:],
    }


@app.get("/api/reports/macro_analysis")
def macro_analysis(user_id: int):
    row = _one("""
        SELECT AVG(protein_sum) AS avg_protein,
               AVG(fat_sum)     AS avg_fat,
               AVG(carbs_sum)   AS avg_carbs,
               AVG(cal_sum)     AS avg_cal
        FROM (
            SELECT fe.date::date,
                   SUM(f.protein_g * fe.servings) AS protein_sum,
                   SUM(f.fat_g     * fe.servings) AS fat_sum,
                   SUM(f.carbs_g   * fe.servings) AS carbs_sum,
                   SUM(f.calories  * fe.servings) AS cal_sum
            FROM food_entry fe
            JOIN food f ON fe.food_id = f.id
            WHERE fe.person_id = %s
            GROUP BY fe.date::date
        ) daily
    """, (user_id,))
    if not row:
        raise HTTPException(404)

    p   = float(row["avg_protein"] or 0)
    fat = float(row["avg_fat"]     or 0)
    c   = float(row["avg_carbs"]   or 0)
    avg_cal = float(row["avg_cal"] or 0)

    cal_p = p * 4;  cal_f = fat * 9;  cal_c = c * 4
    total = cal_p + cal_f + cal_c

    pct_p = cal_p / total * 100 if total else 0
    pct_f = cal_f / total * 100 if total else 0
    pct_c = cal_c / total * 100 if total else 0

    return {
        "summary": {
            "avg_protein": round(p, 1),   "cal_from_protein": round(cal_p), "pct_protein": round(pct_p, 1),
            "avg_fat":     round(fat, 1), "cal_from_fat":     round(cal_f), "pct_fat":     round(pct_f, 1),
            "avg_carbs":   round(c, 1),   "cal_from_carbs":   round(cal_c), "pct_carbs":   round(pct_c, 1),
            "total_cal":   round(avg_cal),
        },
        "pie_data": [
            {"name": "Белки",    "value": round(pct_p, 1), "grams": round(p,   1)},
            {"name": "Жиры",     "value": round(pct_f, 1), "grams": round(fat, 1)},
            {"name": "Углеводы", "value": round(pct_c, 1), "grams": round(c,   1)},
        ],
        "recommended": [30, 20, 50],
    }


@app.get("/api/reports/top_frequent_dishes")
def top_frequent_dishes(user_id: int, top_n: int = 10):
    return {"items": _rows("""
        SELECT f.name AS dish_name, COUNT(*) AS frequency
        FROM food_entry fe
        JOIN food f ON fe.food_id = f.id
        WHERE fe.person_id = %s
        GROUP BY f.name
        ORDER BY frequency DESC
        LIMIT %s
    """, (user_id, top_n))}


@app.get("/api/reports/top_caloric_dishes")
def top_caloric_dishes(user_id: int, top_n: int = 10):
    return {"items": _rows("""
        SELECT f.name AS dish_name,
               ROUND(AVG(f.calories * fe.servings)::numeric, 0) AS avg_cal_per_meal
        FROM food_entry fe
        JOIN food f ON fe.food_id = f.id
        WHERE fe.person_id = %s
        GROUP BY f.name
        ORDER BY avg_cal_per_meal DESC
        LIMIT %s
    """, (user_id, top_n))}


@app.get("/api/reports/compare_users")
def compare_users():
    rows = _rows("""
        WITH daily_user AS (
            SELECT p.id, p.name, p.gender, p.activity_level,
                   p.height_cm, p.weight_kg, p.target_cal_per_day,
                   fe.date::date AS day,
                   SUM(f.calories * fe.servings) AS daily_cal
            FROM person p
            JOIN food_entry fe ON p.id = fe.person_id
            JOIN food f ON fe.food_id = f.id
            GROUP BY p.id, p.name, p.gender, p.activity_level,
                     p.height_cm, p.weight_kg, p.target_cal_per_day, fe.date::date
        )
        SELECT id, name, gender, activity_level, target_cal_per_day,
               ROUND(AVG(daily_cal)::numeric, 0) AS avg_cal,
               COUNT(DISTINCT day) AS total_days,
               MAX(height_cm) AS height_cm,
               MAX(weight_kg) AS weight_kg
        FROM daily_user
        GROUP BY id, name, gender, activity_level, target_cal_per_day
        ORDER BY avg_cal DESC
    """)
    for r in rows:
        h = float(r["height_cm"]) / 100
        r["bmi"]          = round(float(r["weight_kg"]) / (h * h), 1)
        r["deviation"]    = round(float(r["avg_cal"]) - float(r["target_cal_per_day"]))
        r["pct_of_target"] = round(float(r["avg_cal"]) / float(r["target_cal_per_day"]) * 100, 1)

    return {
        "users": rows,
        "chart_data": [
            {
                "name":    r["name"].split()[0],
                "avg_cal": float(r["avg_cal"]),
                "target":  float(r["target_cal_per_day"]),
            }
            for r in rows
        ],
    }


@app.get("/api/reports/meal_time_analysis")
def meal_time_analysis(user_id: int):
    meal_stats = _rows("""
        SELECT fe.meal_type,
               ROUND(AVG(f.calories * fe.servings)::numeric, 0) AS avg_cal,
               COUNT(*) AS count
        FROM food_entry fe
        JOIN food f ON fe.food_id = f.id
        WHERE fe.person_id = %s
        GROUP BY fe.meal_type
        ORDER BY avg_cal DESC
    """, (user_id,))

    late_snacks = _rows("""
        SELECT fe.date::date AS date,
               f.name AS dish_name,
               fe.servings,
               ROUND((f.calories * fe.servings)::numeric, 0) AS dish_calories
        FROM food_entry fe
        JOIN food f ON fe.food_id = f.id
        WHERE fe.person_id = %s
          AND fe.meal_type = 'перекус'
          AND EXTRACT(HOUR FROM fe.eaten_at::time) >= 21
        ORDER BY fe.date DESC, fe.eaten_at DESC
        LIMIT 8
    """, (user_id,))

    return {
        "meal_stats":  meal_stats,
        "late_snacks": late_snacks,
        "late_count":  len(late_snacks),
    }


@app.get("/api/reports/nutrition_calendar")
def nutrition_calendar(user_id: int):
    last = _one("""
        SELECT MAX(EXTRACT(YEAR  FROM date::date)) AS year,
               MAX(EXTRACT(MONTH FROM date::date)) AS month
        FROM food_entry WHERE person_id = %s
    """, (user_id,))
    if not last or not last.get("year"):
        raise HTTPException(404)

    year  = int(float(last["year"]))
    month = int(float(last["month"]))

    info   = _one("SELECT target_cal_per_day FROM person WHERE id = %s", (user_id,))
    target = float(info["target_cal_per_day"]) if info else 2000

    daily = _rows("""
        SELECT fe.date::date AS date,
               ROUND(SUM(f.calories * fe.servings)::numeric, 0) AS calories
        FROM food_entry fe
        JOIN food f ON fe.food_id = f.id
        WHERE fe.person_id = %s
          AND EXTRACT(YEAR  FROM fe.date::date) = %s
          AND EXTRACT(MONTH FROM fe.date::date) = %s
        GROUP BY fe.date::date
        ORDER BY date
    """, (user_id, year, month))

    for r in daily:
        cal = float(r["calories"])
        dev = cal - target
        r["deviation"]     = round(dev)
        r["pct_of_target"] = round(cal / target * 100, 1)
        if dev > target * 0.1:
            r["status"] = "превышение"
        elif dev < -target * 0.1:
            r["status"] = "недобор"
        else:
            r["status"] = "норма"

    return {"year": year, "month": month, "target": round(target), "daily": daily}


@app.get("/api/reports/progress_to_goal")
def progress_to_goal(user_id: int):
    info = _one(
        "SELECT tdee, weight_kg, target_cal_per_day FROM person WHERE id = %s",
        (user_id,)
    )
    if not info:
        raise HTTPException(404)

    tdee           = float(info["tdee"])
    initial_weight = float(info["weight_kg"])
    target_cal     = float(info["target_cal_per_day"])

    daily = _rows("""
        SELECT fe.date::date AS date,
               ROUND(SUM(f.calories * fe.servings)::numeric, 0) AS actual_cal
        FROM food_entry fe
        JOIN food f ON fe.food_id = f.id
        WHERE fe.person_id = %s
        GROUP BY fe.date::date
        ORDER BY date
    """, (user_id,))
    if not daily:
        raise HTTPException(404)

    cumulative = 0.0
    for r in daily:
        deficit     = tdee - float(r["actual_cal"])
        cumulative += deficit
        r["deficit"]            = round(deficit)
        r["cumulative_deficit"] = round(cumulative)
        r["predicted_weight"]   = round(initial_weight + cumulative / 7700, 2)

    actual_cals = [float(r["actual_cal"]) for r in daily]
    avg_actual  = sum(actual_cals) / len(actual_cals)
    weight_change = cumulative / 7700

    return {
        "summary": {
            "initial_weight":   initial_weight,
            "tdee":             round(tdee),
            "target_cal":       round(target_cal),
            "avg_actual_cal":   round(avg_actual),
            "total_deficit":    round(cumulative),
            "weight_change":    round(weight_change, 2),
            "predicted_weight": round(initial_weight + weight_change, 1),
        },
        "chart_data": [
            {
                "date":               r["date"],
                "actual_cal":         float(r["actual_cal"]),
                "predicted_weight":   r["predicted_weight"],
                "cumulative_deficit": r["cumulative_deficit"],
            }
            for r in daily[-60:]
        ],
        "tdee": round(tdee),
    }


@app.get("/api/reports/overall_statistics")
def overall_statistics():
    stats = _one("""
        SELECT COUNT(DISTINCT p.id)  AS total_users,
               COUNT(fe.id)          AS total_meals,
               COUNT(DISTINCT f.name) AS total_dishes,
               MIN(fe.date)          AS min_date,
               MAX(fe.date)          AS max_date
        FROM person p
        JOIN food_entry fe ON p.id = fe.person_id
        JOIN food f ON fe.food_id = f.id
    """)
    goals = _rows(
        "SELECT goal, COUNT(*) AS cnt FROM person GROUP BY goal ORDER BY cnt DESC"
    )
    avg_cal = _one("""
        SELECT AVG(user_avg) AS overall_avg
        FROM (
            SELECT AVG(f.calories * fe.servings) AS user_avg
            FROM food_entry fe
            JOIN food f ON fe.food_id = f.id
            GROUP BY fe.person_id
        ) u
    """)
    return {
        "stats": {
            **stats,
            "avg_cal_per_meal": round(float(avg_cal["overall_avg"] or 0)),
        },
        "goals": goals,
    }


@app.get("/api/reports/efficiency_report")
def efficiency_report(user_id: int):
    info = _one("SELECT target_cal_per_day FROM person WHERE id = %s", (user_id,))
    if not info:
        raise HTTPException(404)
    target = float(info["target_cal_per_day"])

    daily = _rows("""
        SELECT fe.date::date AS date,
               ROUND(SUM(f.calories * fe.servings)::numeric, 0) AS total_cal
        FROM food_entry fe
        JOIN food f ON fe.food_id = f.id
        WHERE fe.person_id = %s
        GROUP BY fe.date::date
    """, (user_id,))

    total_days = len(daily)
    within = sum(1 for r in daily if target * 0.9 <= float(r["total_cal"]) <= target * 1.1)
    over   = sum(1 for r in daily if float(r["total_cal"]) > target * 1.1)
    under  = sum(1 for r in daily if float(r["total_cal"]) < target * 0.9)

    meal_types = _rows("""
        SELECT fe.date::date,
               COUNT(DISTINCT fe.meal_type) AS meal_types
        FROM food_entry fe
        WHERE fe.person_id = %s
        GROUP BY fe.date::date
    """, (user_id,))
    low_meal = sum(1 for r in meal_types if r["meal_types"] < 3)

    return {
        "summary": {
            "target":      round(target),
            "total_days":  total_days,
            "within_10pct": within,
            "pct_within":  round(within / total_days * 100, 1) if total_days else 0,
            "over_days":   over,
            "under_days":  under,
            "low_meal_days": low_meal,
        },
        "breakdown": [
            {"label": "В норме (±10%)",     "value": within, "color": "#af87af"},
            {"label": "Превышение (>110%)", "value": over,   "color": "#d75fd7"},
            {"label": "Недобор (<90%)",     "value": under,  "color": "#875fd7"},
        ],
    }

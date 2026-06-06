import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
from tabulate import tabulate
from src.core.person import Person
from src.core.registries import REPORT_CAPTIONS
from src.db.database import Database

# Настройки matplotlib (как в исходном коде)
matplotlib.use("TkAgg")
plt.rcParams["font.sans-serif"] = ["Arial", "DejaVu Sans", "Microsoft Sans Serif"]
plt.rcParams["axes.unicode_minus"] = False




# ------------------- Инициализация БД -------------------
def init_database(config: dict):
    """Инициализирует пул соединений Database."""
    Database.initialize(config)


def db_to_df(query: str, params: tuple = None) -> pd.DataFrame:
    rows = Database.fetch_all(query, params)
    if not rows:
        return pd.DataFrame()
    
    return pd.DataFrame(rows)


def pretty_print(df: pd.DataFrame, columns: list[str] = None) -> list[str]:
    if columns is None:
        columns = [col for col in df.columns if col in REPORT_CAPTIONS]
    df_display = df[columns].copy().rename(columns=REPORT_CAPTIONS)
    return tabulate(df_display, headers="keys", tablefmt="plain", showindex=False).split("\n")


def personal_statistics(user_id: int) -> list[str]:
    # Получаем цель и даты
    query_info = """
        SELECT p.target_cal_per_day,
               MIN(fe.date) AS start_date,
               MAX(fe.date) AS end_date
        FROM person p
        JOIN food_entry fe ON p.id = fe.person_id
        WHERE p.id = %s
        GROUP BY p.target_cal_per_day
    """
    info_rows = Database.fetch_all(query_info, (user_id,))
    if not info_rows:
        return [f"Пользователь с ID {user_id} не найден."]
    info = info_rows[0]
    target_cal = info["target_cal_per_day"]
    start_date = info["start_date"]
    end_date = info["end_date"]

    # Дневная агрегация
    query_daily = """
        SELECT
            fe.date::date AS date_only,
            SUM(f.calories * fe.servings) AS total_cal,
            SUM(f.protein_g * fe.servings) AS total_protein,
            SUM(f.fat_g * fe.servings) AS total_fat,
            SUM(f.carbs_g * fe.servings) AS total_carbs
        FROM food_entry fe
        JOIN food f ON fe.food_id = f.id
        WHERE fe.person_id = %s
        GROUP BY fe.date::date
        ORDER BY date_only
    """
    daily = db_to_df(query_daily, (user_id,))
    if daily.empty:
        return [f"Нет записей приёмов для пользователя {user_id}"]

    total_days = len(daily)
    avg_cal = daily["total_cal"].mean()
    avg_protein = daily["total_protein"].mean()
    avg_fat = daily["total_fat"].mean()
    avg_carbs = daily["total_carbs"].mean()
    deviation = avg_cal - target_cal
    percent_of_target = (avg_cal / target_cal) * 100

    out = []
    out.append("=== Персональная статистика ===")
    out.append(f"Период: {start_date} – {end_date}")
    out.append(f"Всего дней с записями: {total_days}")
    out.append("Среднее в день:")
    out.append(
        f"  Калории: {avg_cal:.0f} ккал (цель {target_cal:.0f} ккал, {percent_of_target:.1f}% от цели)"
    )
    out.append(f"  Белки: {avg_protein:.1f} г")
    out.append(f"  Жиры: {avg_fat:.1f} г")
    out.append(f"  Углеводы: {avg_carbs:.1f} г")
    out.append(f"Отклонение от цели: {deviation:+.0f} ккал в день")
    out.append("Динамика по дням (первые 7 дней):")
    out.extend(pretty_print(daily.head(7)))

    plot_calorie_trend(daily.copy(), target_cal)
    return out


def macro_analysis(user_id: int) -> list[str]:
    query = """
        SELECT
            AVG(protein_sum) AS avg_protein,
            AVG(fat_sum) AS avg_fat,
            AVG(carbs_sum) AS avg_carbs,
            AVG(cal_sum) AS avg_cal
        FROM (
            SELECT
                fe.date::date,
                SUM(f.protein_g * fe.servings) AS protein_sum,
                SUM(f.fat_g * fe.servings) AS fat_sum,
                SUM(f.carbs_g * fe.servings) AS carbs_sum,
                SUM(f.calories * fe.servings) AS cal_sum
            FROM food_entry fe
            JOIN food f ON fe.food_id = f.id
            WHERE fe.person_id = %s
            GROUP BY fe.date::date
        ) daily
    """
    stats = db_to_df(query, (user_id,))
    if stats.empty:
        return [f"Пользователь с ID {user_id} не найден или нет записей."]
    avg_protein = stats.iloc[0]["avg_protein"]
    avg_fat = stats.iloc[0]["avg_fat"]
    avg_carbs = stats.iloc[0]["avg_carbs"]
    avg_cal = stats.iloc[0]["avg_cal"]

    cal_from_protein = avg_protein * 4
    cal_from_fat = avg_fat * 9
    cal_from_carbs = avg_carbs * 4
    total_calc = cal_from_protein + cal_from_fat + cal_from_carbs
    if total_calc > 0:
        pct_protein = cal_from_protein / total_calc * 100
        pct_fat = cal_from_fat / total_calc * 100
        pct_carbs = cal_from_carbs / total_calc * 100
    else:
        pct_protein = pct_fat = pct_carbs = 0

    out = ["=== Анализ макронутриентов ==="]
    out.append("Среднее потребление в день:")
    out.append(f"  Белки: {avg_protein:.1f} г → {cal_from_protein:.0f} ккал ({pct_protein:.1f}%)")
    out.append(f"  Жиры:  {avg_fat:.1f} г → {cal_from_fat:.0f} ккал ({pct_fat:.1f}%)")
    out.append(f"  Углеводы: {avg_carbs:.1f} г → {cal_from_carbs:.0f} ккал ({pct_carbs:.1f}%)")
    out.append(
        f"  Итого (расчёт): {total_calc:.0f} ккал, средние калории из таблицы: {avg_cal:.0f} ккал"
    )
    out.append("Сравнение с рекомендуемым соотношением (30/20/50):")
    out.append(f"  Белки: {pct_protein:.1f}% vs 30%")
    out.append(f"  Жиры:  {pct_fat:.1f}% vs 20%")
    out.append(f"  Углеводы: {pct_carbs:.1f}% vs 50%")

    plot_macro_pie(avg_protein, avg_fat, avg_carbs)
    return out


def top_frequent_dishes(user_id: int, top_n: int = 10) -> list[str]:
    query = """
        SELECT f.name AS dish_name, COUNT(*) AS frequency
        FROM food_entry fe
        JOIN food f ON fe.food_id = f.id
        WHERE fe.person_id = %s
        GROUP BY f.name
        ORDER BY frequency DESC
        LIMIT %s
    """
    freq = db_to_df(query, (user_id, top_n))
    if freq.empty:
        return [f"Пользователь с ID {user_id} не найден или нет блюд."]

    out = [f"=== Топ-{top_n} самых частых блюд ==="]
    for i, (dish, count) in enumerate(zip(freq["dish_name"], freq["frequency"]), 1):
        out.append(f"{i:2}. {dish:30} – {count} раз(а)")
    return out


def top_caloric_dishes(user_id: int, top_n: int = 10) -> list[str]:
    query = """
        SELECT
            f.name AS dish_name,
            AVG(f.calories * fe.servings) AS avg_cal_per_meal
        FROM food_entry fe
        JOIN food f ON fe.food_id = f.id
        WHERE fe.person_id = %s
        GROUP BY f.name
        ORDER BY avg_cal_per_meal DESC
        LIMIT %s
    """
    caloric = db_to_df(query, (user_id, top_n))
    if caloric.empty:
        return [f"Пользователь с ID {user_id} не найден или нет блюд."]

    out = [f"=== Топ-{top_n} самых калорийных блюд (средняя калорийность за приём) ==="]
    for i, (dish, cal) in enumerate(zip(caloric["dish_name"], caloric["avg_cal_per_meal"]), 1):
        out.append(f"{i:2}. {dish:30} – {cal:.0f} ккал в среднем за приём")
    return out


def compare_users(user_id: int = None) -> list[str]:
    # user_id не используется, но оставлен для совместимости
    query = """
        WITH daily_user AS (
            SELECT
                p.id,
                p.name,
                p.gender,
                p.activity_level,
                p.height_cm,
                p.weight_kg,
                p.target_cal_per_day,
                fe.date::date AS day,
                SUM(f.calories * fe.servings) AS daily_cal
            FROM person p
            JOIN food_entry fe ON p.id = fe.person_id
            JOIN food f ON fe.food_id = f.id
            GROUP BY p.id, p.name, p.gender, p.activity_level, p.height_cm, p.weight_kg,
                     p.target_cal_per_day, fe.date::date
        )
        SELECT
            id,
            name,
            gender,
            activity_level,
            target_cal_per_day,
            AVG(daily_cal) AS avg_cal,
            COUNT(DISTINCT day) AS total_days,
            MAX(height_cm) AS height_cm,
            MAX(weight_kg) AS weight_kg
        FROM daily_user
        GROUP BY id, name, gender, activity_level, target_cal_per_day
    """
    users = db_to_df(query)
    if users.empty:
        return ["Нет данных для сравнения пользователей."]

    users["bmi"] = (users["weight_kg"] / ((users["height_cm"] / 100) ** 2)).round(0)
    users["deviation"] = (users["avg_cal"] - users["target_cal_per_day"]).round(0)
    users["avg_cal"] = users["avg_cal"].round(0)
    users["percent_of_target"] = ((users["avg_cal"] / users["target_cal_per_day"]) * 100).round(0)

    out = ["=== Сравнение пользователей ==="]
    out.extend(
        pretty_print(
            users[
                [
                    "name",
                    "gender",
                    "activity_level",
                    "bmi",
                    "target_cal_per_day",
                    "avg_cal",
                    "deviation",
                    "percent_of_target",
                ]
            ]
        )
    )
    plot_users_comparison(users.copy())
    return out


def meal_time_analysis(user_id: int) -> list[str]:
    query_stats = """
        SELECT
            fe.meal_type,
            AVG(f.calories * fe.servings) AS avg_cal,
            COUNT(*) AS count
        FROM food_entry fe
        JOIN food f ON fe.food_id = f.id
        WHERE fe.person_id = %s
        GROUP BY fe.meal_type
    """
    meal_stats = db_to_df(query_stats, (user_id,))
    if meal_stats.empty:
        return [f"Пользователь с ID {user_id} не найден или нет приёмов."]

    # Поздние перекусы (после 21:00)
    query_late = """
        SELECT
            fe.date::date AS date_only,
            f.name AS dish_name,
            fe.servings,
            f.calories * fe.servings AS dish_calories
        FROM food_entry fe
        JOIN food f ON fe.food_id = f.id
        WHERE fe.person_id = %s
          AND fe.meal_type = 'перекус'
          AND EXTRACT(HOUR FROM fe.eaten_at::time) >= 21
        ORDER BY fe.date, fe.eaten_at
        LIMIT 5
    """
    late_snacks = db_to_df(query_late, (user_id,))
    late_count = len(late_snacks)
    late_days = late_snacks["date_only"].nunique() if not late_snacks.empty else 0

    out = ["=== Анализ приемов пищи ==="]
    out.append("Средняя калорийность по типам приёмов:")
    for _, row in meal_stats.iterrows():
        out.append(
            f"  {row['meal_type']:10} – {row['avg_cal']:.0f} ккал (всего {row['count']} приёмов)"
        )
    out.append(f"Поздние перекусы (после 21:00): {late_count} раз(а) за {late_days} дней")
    if late_count > 0:
        out.append("  Примеры:")
        out.extend(
            pretty_print(late_snacks[["date_only", "dish_name", "servings", "dish_calories"]])
        )

    plot_meal_type_calories(meal_stats.copy())
    return out


def nutrition_calendar(user_id: int) -> list[str]:
    # Определяем последний доступный месяц
    query_last_month = """
        SELECT
            MAX(EXTRACT(YEAR FROM date::date)) AS year,
            MAX(EXTRACT(MONTH FROM date::date)) AS month
        FROM food_entry
        WHERE person_id = %s
    """
    last = db_to_df(query_last_month, (user_id,))
    if last.empty or pd.isna(last.iloc[0]["year"]):
        return [f"Нет записей для пользователя {user_id}."]
    year = int(last.iloc[0]["year"])
    month = int(last.iloc[0]["month"])

    query_cal = """
        SELECT
            fe.date::date AS date,
            SUM(f.calories * fe.servings) AS calories
        FROM food_entry fe
        JOIN food f ON fe.food_id = f.id
        WHERE fe.person_id = %s
          AND EXTRACT(YEAR FROM fe.date::date) = %s
          AND EXTRACT(MONTH FROM fe.date::date) = %s
        GROUP BY fe.date::date
        ORDER BY date
    """
    daily_cal = db_to_df(query_cal, (user_id, year, month))
    if daily_cal.empty:
        return [f"Нет данных за {year}-{month:02d} для пользователя {user_id}."]

    target_query = "SELECT target_cal_per_day FROM person WHERE id = %s"
    target_rows = Database.fetch_one(target_query, (user_id,))
    target = target_rows["target_cal_per_day"] if target_rows else 0

    daily_cal["deviation"] = daily_cal["calories"] - target
    daily_cal["status"] = daily_cal["deviation"].apply(
        lambda x: (
            "⬆️ превышение"
            if x > target * 0.1
            else ("⬇️ недобор" if x < -target * 0.1 else "✅ норма")
        )
    )

    out = [f"=== Календарь питания за {year}-{month:02d} ==="]
    out.append(f"Цель: {target:.0f} ккал/день")
    out.extend(daily_cal.to_string(index=False).split("\n"))

    plot_monthly_calendar(daily_cal.copy(), target)
    return out


def progress_to_goal(user_id: int) -> list[str]:
    info_query = "SELECT tdee, weight_kg, target_cal_per_day FROM person WHERE id = %s"
    info_rows = Database.fetch_one(info_query, (user_id,))
    if not info_rows:
        return [f"Пользователь с ID {user_id} не найден."]
    tdee = info_rows["tdee"]
    initial_weight = info_rows["weight_kg"]
    target_cal = info_rows["target_cal_per_day"]

    daily_query = """
        SELECT
            fe.date::date AS date_only,
            SUM(f.calories * fe.servings) AS actual_cal
        FROM food_entry fe
        JOIN food f ON fe.food_id = f.id
        WHERE fe.person_id = %s
        GROUP BY fe.date::date
        ORDER BY date_only
    """
    daily = db_to_df(daily_query, (user_id,))
    if daily.empty:
        return [f"Нет записей приёмов для пользователя {user_id}"]

    daily["deficit"] = tdee - daily["actual_cal"]
    cumulative_deficit = daily["deficit"].sum()
    weight_change = cumulative_deficit / 7700
    final_weight = initial_weight + weight_change

    out = ["=== Прогресс к цели ==="]
    out.append(f"Начальный вес: {initial_weight:.1f} кг")
    out.append(f"TDEE: {tdee:.0f} ккал/день, целевая калорийность: {target_cal:.0f} ккал/день")
    out.append(f"Фактическое среднее потребление: {daily['actual_cal'].mean():.0f} ккал/день")
    out.append(f"Общий дефицит(+) / профицит(-) за период: {cumulative_deficit:+.0f} ккал")
    out.append(f"Прогнозируемое изменение веса: {weight_change:+.1f} кг")
    out.append(f"Текущий прогнозируемый вес: {final_weight:.1f} кг")
    if len(daily) > 1:
        out.append("Динамика дефицита по дням (первые 7 дней):")
        out.extend(
            daily.head(7)[["date_only", "actual_cal", "deficit"]].to_string(index=False).split("\n")
        )

    plot_cumulative_deficit(daily.copy())
    return out


def overall_statistics(user_id: int = None) -> list[str]:
    query = """
        SELECT
            COUNT(DISTINCT p.id) AS total_users,
            COUNT(fe.id) AS total_meals,
            COUNT(DISTINCT f.name) AS total_dishes,
            MIN(fe.date) AS min_date,
            MAX(fe.date) AS max_date
        FROM person p
        JOIN food_entry fe ON p.id = fe.person_id
        JOIN food f ON fe.food_id = f.id
    """
    stats = db_to_df(query)
    if stats.empty:
        return ["Нет данных для общей статистики."]
    total_users = stats.iloc[0]["total_users"]
    total_meals = stats.iloc[0]["total_meals"]
    total_dishes = stats.iloc[0]["total_dishes"]
    min_date = stats.iloc[0]["min_date"]
    max_date = stats.iloc[0]["max_date"]
    date_range = f"{min_date} – {max_date}"

    goals_query = "SELECT goal, COUNT(*) AS cnt FROM person GROUP BY goal"
    goals = db_to_df(goals_query)

    avg_cal_per_user_query = """
        SELECT AVG(user_avg) AS overall_avg_cal
        FROM (
            SELECT AVG(f.calories * fe.servings) AS user_avg
            FROM food_entry fe
            JOIN food f ON fe.food_id = f.id
            GROUP BY fe.person_id
        ) u
    """
    avg_cal_df = db_to_df(avg_cal_per_user_query)
    user_avg_cal = avg_cal_df.iloc[0]["overall_avg_cal"] if not avg_cal_df.empty else 0

    out = ["=== Общая статистика ==="]
    out.append(f"Период данных: {date_range}")
    out.append(f"Всего пользователей: {total_users}")
    out.append(f"Всего приёмов пищи: {total_meals}")
    out.append(f"Уникальных блюд: {total_dishes}")
    out.append("Распределение целей:")
    for _, row in goals.iterrows():
        out.append(f"  {row['goal']}: {row['cnt']} пользователь(ей)")
    out.append(f"Среднее потребление калорий на одного пользователя: {user_avg_cal:.0f} ккал/приём")
    return out


def efficiency_report(user_id: int) -> list[str]:
    info_query = "SELECT target_cal_per_day FROM person WHERE id = %s"
    info_rows = Database.fetch_one(info_query, (user_id,))
    if not info_rows:
        return [f"Пользователь с ID {user_id} не найден."]
    target = info_rows["target_cal_per_day"]

    daily_query = """
        SELECT
            fe.date::date AS date_only,
            SUM(f.calories * fe.servings) AS total_cal
        FROM food_entry fe
        JOIN food f ON fe.food_id = f.id
        WHERE fe.person_id = %s
        GROUP BY fe.date::date
    """
    daily = db_to_df(daily_query, (user_id,))
    if daily.empty:
        return [f"Нет записей приёмов для пользователя {user_id}"]

    total_days = len(daily)
    within_10pct = (
        (daily["total_cal"] >= target * 0.9) & (daily["total_cal"] <= target * 1.1)
    ).sum()
    pct = (within_10pct / total_days) * 100 if total_days > 0 else 0

    meals_query = """
        SELECT
            fe.date::date,
            COUNT(DISTINCT fe.meal_type) AS meal_types
        FROM food_entry fe
        WHERE fe.person_id = %s
        GROUP BY fe.date::date
    """
    meals_per_day = db_to_df(meals_query, (user_id,))
    low_meal_days = (meals_per_day["meal_types"] < 3).sum() if not meals_per_day.empty else 0

    over_days = (daily["total_cal"] > target * 1.1).sum()
    under_days = (daily["total_cal"] < target * 0.9).sum()

    out = ["=== Отчет по эффективности ==="]
    out.append(f"Цель: {target:.0f} ккал/день")
    out.append(f"Всего дней с данными: {total_days}")
    out.append(f"Дней в пределах ±10% от цели: {within_10pct} ({pct:.1f}%)")
    out.append(f"Дней с малым количеством приёмов (<3): {low_meal_days}")
    out.append(f"Дней с превышением (>110%): {over_days}")
    out.append(f"Дней с недобором (<90%): {under_days}")

    plot_efficiency_bars(total_days, under_days, within_10pct, over_days)
    return out

def plot_calorie_trend(daily_df: pd.DataFrame, target_cal: float):
    plt.figure(figsize=(10, 5))
    plt.plot(
        daily_df["date_only"],
        daily_df["total_cal"],
        marker="o",
        linestyle="-",
        linewidth=1,
        markersize=3,
    )
    plt.axhline(y=target_cal, color="r", linestyle="--", label=f"Цель {target_cal:.0f} ккал")
    plt.xlabel("Дата")
    plt.ylabel("Калории (ккал)")
    plt.title("Динамика потребления калорий")
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.show(block=True)


def plot_macro_pie(avg_protein, avg_fat, avg_carbs):
    cal_protein = avg_protein * 4
    cal_fat = avg_fat * 9
    cal_carbs = avg_carbs * 4
    sizes = [cal_protein, cal_fat, cal_carbs]
    labels = ["Белки", "Жиры", "Углеводы"]
    colors = ["#66b3ff", "#ff9999", "#99ff99"]
    plt.figure(figsize=(6, 6))
    plt.pie(sizes, labels=labels, autopct="%1.1f%%", colors=colors, startangle=90)
    plt.title("Распределение калорий по макронутриентам")
    plt.axis("equal")
    plt.tight_layout()
    plt.show(block=True)


def plot_users_comparison(users_display: pd.DataFrame):
    users_sorted = users_display.sort_values("avg_cal")
    x = range(len(users_sorted))
    width = 0.35
    plt.figure(figsize=(10, 6))
    plt.bar(x, users_sorted["avg_cal"], width, label="Среднее потребление", color="blue")
    plt.bar(
        [i + width for i in x],
        users_sorted["target_cal_per_day"],
        width,
        label="Цель",
        color="orange",
    )
    plt.xticks([i + width / 2 for i in x], users_sorted["name"], rotation=45)
    plt.ylabel("Калории (ккал)")
    plt.title("Сравнение среднего потребления с целевой калорийностью")
    plt.legend()
    plt.tight_layout()
    plt.show(block=True)


def plot_meal_type_calories(meal_stats: pd.DataFrame):
    plt.figure(figsize=(8, 4))
    plt.bar(meal_stats["meal_type"], meal_stats["avg_cal"], color="skyblue")
    plt.xlabel("Тип приёма пищи")
    plt.ylabel("Средняя калорийность (ккал)")
    plt.title("Средняя калорийность по типам приёмов")
    plt.tight_layout()
    plt.show(block=True)


def plot_monthly_calendar(daily_cal: pd.DataFrame, target: float):
    daily_cal = daily_cal.sort_values("date")
    plt.figure(figsize=(12, 5))
    plt.bar(daily_cal["date"].dt.day, daily_cal["calories"], width=0.8, color="teal")
    plt.axhline(y=target, color="r", linestyle="--", label=f"Цель {target:.0f} ккал")
    plt.xlabel("День месяца")
    plt.ylabel("Калории (ккал)")
    plt.title(f"Калорийность по дням за {daily_cal['date'].dt.strftime('%Y-%m').iloc[0]}")
    plt.legend()
    plt.xticks(range(1, 32))
    plt.tight_layout()
    plt.show(block=True)


def plot_cumulative_deficit(daily: pd.DataFrame):
    daily = daily.sort_values("date_only")
    daily["cumulative"] = daily["deficit"].cumsum()
    plt.figure(figsize=(10, 5))
    plt.fill_between(daily["date_only"], 0, daily["cumulative"], color="green", alpha=0.3)
    plt.plot(daily["date_only"], daily["cumulative"], marker="o", linestyle="-", linewidth=1)
    plt.xlabel("Дата")
    plt.ylabel("Накопленный дефицит (ккал)")
    plt.title("Накопленный дефицит калорий")
    plt.axhline(y=0, color="black", linestyle="-", linewidth=0.5)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show(block=True)


def plot_efficiency_bars(total_days, under_days, within_days, over_days):
    categories = ["Недобор (<90%)", "Норма (±10%)", "Превышение (>110%)"]
    values = [under_days, within_days, over_days]
    plt.figure(figsize=(6, 4))
    plt.bar(categories, values, color=["red", "green", "orange"])
    plt.ylabel("Количество дней")
    plt.title("Эффективность достижения цели по дням")
    plt.tight_layout()
    plt.show(block=True)
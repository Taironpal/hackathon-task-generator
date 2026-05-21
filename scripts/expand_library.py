"""Расширение библиотеки: добавляем subject + textbook к существующим записям
и дописываем новые задачи по программе Виленкин 5-6 / Макарычев 7-9 / Атанасян 7-9 /
алгебра-геометрия 10-11 / Перышкин 7-9 / Мякишев 10-11 / Габриелян 8-9 / Босова 7-9.

Запуск: python -m scripts.expand_library
"""
from __future__ import annotations

import json
from pathlib import Path

LIB_PATH = Path(__file__).resolve().parents[1] / "data" / "library.json"


def textbook_for(item: dict) -> str:
    """Подобрать учебник для существующего элемента по grade и topic."""
    g = item["grade"]
    topic = item["topic"].lower()
    if "геометри" in topic or "пифагор" in topic or "трапеци" in topic or "треугольник" in topic:
        if g <= 9:
            return "Атанасян 7-9"
        return "Атанасян 10-11"
    if g <= 4:
        return "Моро 1-4"
    if g <= 6:
        return "Виленкин 5-6"
    if g <= 9:
        return "Макарычев 7-9"
    return "Алимов 10-11"


# Новые элементы, разбитые по предмету и учебнику.
NEW_ITEMS: list[dict] = [
    # ===== Математика. Виленкин 5 (дополнение) =====
    {
        "id": "vil5-natural-mult",
        "grade": 5, "subject": "математика", "topic": "умножение натуральных чисел",
        "subtopic": "арифметика", "tags": ["умножение", "натуральные"], "is_combined": False,
        "textbook": "Виленкин 5",
        "statement": "Найдите значение выражения: 234 * 18.",
    },
    {
        "id": "vil5-natural-div",
        "grade": 5, "subject": "математика", "topic": "деление натуральных чисел",
        "subtopic": "арифметика", "tags": ["деление", "натуральные"], "is_combined": False,
        "textbook": "Виленкин 5",
        "statement": "Найдите частное от деления 1782 на 18.",
    },
    {
        "id": "vil5-area-rect",
        "grade": 5, "subject": "математика", "topic": "площадь прямоугольника",
        "subtopic": "геометрия", "tags": ["площадь", "прямоугольник"], "is_combined": False,
        "textbook": "Виленкин 5",
        "statement": "Найдите площадь прямоугольника со сторонами 17 см и 12 см.",
    },
    {
        "id": "vil5-volume-cube",
        "grade": 5, "subject": "математика", "topic": "объём куба",
        "subtopic": "геометрия", "tags": ["объём", "куб"], "is_combined": False,
        "textbook": "Виленкин 5",
        "statement": "Найдите объём куба с длиной ребра 6 см.",
    },
    {
        "id": "vil5-decimal-mult",
        "grade": 5, "subject": "математика", "topic": "умножение десятичных дробей",
        "subtopic": "десятичные", "tags": ["десятичные", "умножение"], "is_combined": False,
        "textbook": "Виленкин 5",
        "statement": "Найдите произведение: 3,4 * 2,5.",
    },
    {
        "id": "vil5-decimal-div",
        "grade": 5, "subject": "математика", "topic": "деление десятичных дробей",
        "subtopic": "десятичные", "tags": ["десятичные", "деление"], "is_combined": False,
        "textbook": "Виленкин 5",
        "statement": "Найдите частное: 17,5 / 2,5.",
    },
    # ===== Математика. Виленкин 6 (дополнение) =====
    {
        "id": "vil6-gcd",
        "grade": 6, "subject": "математика", "topic": "наибольший общий делитель",
        "subtopic": "делимость", "tags": ["НОД"], "is_combined": False,
        "textbook": "Виленкин 6",
        "statement": "Найдите наибольший общий делитель чисел 48 и 36.",
    },
    {
        "id": "vil6-lcm",
        "grade": 6, "subject": "математика", "topic": "наименьшее общее кратное",
        "subtopic": "делимость", "tags": ["НОК"], "is_combined": False,
        "textbook": "Виленкин 6",
        "statement": "Найдите наименьшее общее кратное чисел 12 и 18.",
    },
    {
        "id": "vil6-fraction-mult",
        "grade": 6, "subject": "математика", "topic": "умножение обыкновенных дробей",
        "subtopic": "дроби", "tags": ["дроби", "умножение"], "is_combined": False,
        "textbook": "Виленкин 6",
        "statement": "Найдите произведение: 3/5 * 5/9.",
    },
    {
        "id": "vil6-fraction-div",
        "grade": 6, "subject": "математика", "topic": "деление обыкновенных дробей",
        "subtopic": "дроби", "tags": ["дроби", "деление"], "is_combined": False,
        "textbook": "Виленкин 6",
        "statement": "Найдите частное: 4/7 / 2/3.",
    },
    {
        "id": "vil6-ratio",
        "grade": 6, "subject": "математика", "topic": "отношение чисел",
        "subtopic": "отношения", "tags": ["отношение"], "is_combined": False,
        "textbook": "Виленкин 6",
        "statement": "Запишите отношение 24 к 30 в виде несократимой дроби.",
    },
    {
        "id": "vil6-coordinate-point",
        "grade": 6, "subject": "математика", "topic": "координатная плоскость",
        "subtopic": "координаты", "tags": ["координаты"], "is_combined": False,
        "textbook": "Виленкин 6",
        "statement": "Найдите расстояние от точки A(3, 4) до начала координат.",
    },
    # ===== Математика. Макарычев 7-9 (дополнение) =====
    {
        "id": "mak7-formula-square-sum",
        "grade": 7, "subject": "математика", "topic": "формула квадрата суммы",
        "subtopic": "алгебра", "tags": ["формулы сокращённого умножения"], "is_combined": False,
        "textbook": "Макарычев 7",
        "statement": "Раскройте скобки и упростите: (3 + 5)^2.",
    },
    {
        "id": "mak7-system-linear",
        "grade": 7, "subject": "математика", "topic": "система линейных уравнений",
        "subtopic": "алгебра", "tags": ["система", "уравнения"], "is_combined": True,
        "textbook": "Макарычев 7",
        "statement": "Решите систему: 2x + y = 7, x - y = 2. Найдите x.",
    },
    {
        "id": "mak7-function-linear",
        "grade": 7, "subject": "математика", "topic": "линейная функция",
        "subtopic": "функции", "tags": ["функция", "линейная"], "is_combined": False,
        "textbook": "Макарычев 7",
        "statement": "Найдите значение функции y = 3x - 4 в точке x = 5.",
    },
    {
        "id": "mak8-rational-fraction",
        "grade": 8, "subject": "математика", "topic": "рациональные дроби",
        "subtopic": "алгебра", "tags": ["рациональные", "дроби"], "is_combined": False,
        "textbook": "Макарычев 8",
        "statement": "Найдите значение выражения 12/x при x = 4.",
    },
    {
        "id": "mak9-quadratic-function",
        "grade": 9, "subject": "математика", "topic": "квадратичная функция",
        "subtopic": "функции", "tags": ["квадратичная", "функция"], "is_combined": False,
        "textbook": "Макарычев 9",
        "statement": "Найдите значение функции y = x^2 - 4x + 3 в точке x = 5.",
    },
    {
        "id": "mak9-sum-geom-prog",
        "grade": 9, "subject": "математика", "topic": "сумма геометрической прогрессии",
        "subtopic": "прогрессии", "tags": ["прогрессия", "геометрическая"], "is_combined": False,
        "textbook": "Макарычев 9",
        "statement": "Найдите сумму первых 5 членов геометрической прогрессии с b1 = 2 и q = 3.",
    },
    # ===== Геометрия. Атанасян 7-9 =====
    {
        "id": "atan7-segment",
        "grade": 7, "subject": "математика", "topic": "длина отрезка",
        "subtopic": "геометрия", "tags": ["отрезок", "длина"], "is_combined": False,
        "textbook": "Атанасян 7-9",
        "statement": "Точка C делит отрезок AB длиной 12 см так, что AC относится к CB как 2 к 1. Найдите длину AC.",
    },
    {
        "id": "atan8-rectangle-perimeter",
        "grade": 8, "subject": "математика", "topic": "периметр прямоугольника",
        "subtopic": "геометрия", "tags": ["периметр", "прямоугольник"], "is_combined": False,
        "textbook": "Атанасян 7-9",
        "statement": "Найдите периметр прямоугольника со сторонами 8 см и 5 см.",
    },
    {
        "id": "atan8-parallelogram-area",
        "grade": 8, "subject": "математика", "topic": "площадь параллелограмма",
        "subtopic": "геометрия", "tags": ["параллелограмм", "площадь"], "is_combined": False,
        "textbook": "Атанасян 7-9",
        "statement": "Найдите площадь параллелограмма с основанием 9 см и высотой 4 см.",
    },
    {
        "id": "atan9-circle-area",
        "grade": 9, "subject": "математика", "topic": "площадь круга",
        "subtopic": "геометрия", "tags": ["круг", "площадь"], "is_combined": False,
        "textbook": "Атанасян 7-9",
        "statement": "Найдите площадь круга радиуса 5 см. Число пи принять равным 3,14.",
    },
    # ===== Стереометрия. Атанасян 10-11 =====
    {
        "id": "atan10-cuboid-volume",
        "grade": 10, "subject": "математика", "topic": "объём параллелепипеда",
        "subtopic": "стереометрия", "tags": ["параллелепипед", "объём"], "is_combined": False,
        "textbook": "Атанасян 10-11",
        "statement": "Найдите объём прямоугольного параллелепипеда с измерениями 4, 5 и 6 см.",
    },
    {
        "id": "atan10-pyramid-volume",
        "grade": 10, "subject": "математика", "topic": "объём пирамиды",
        "subtopic": "стереометрия", "tags": ["пирамида", "объём"], "is_combined": False,
        "textbook": "Атанасян 10-11",
        "statement": "Найдите объём пирамиды с площадью основания 30 см^2 и высотой 9 см.",
    },
    {
        "id": "atan11-sphere-area",
        "grade": 11, "subject": "математика", "topic": "площадь поверхности шара",
        "subtopic": "стереометрия", "tags": ["шар", "поверхность"], "is_combined": False,
        "textbook": "Атанасян 10-11",
        "statement": "Найдите площадь поверхности шара радиуса 7 см. Число пи принять равным 3,14.",
    },
    # ===== ФИЗИКА. Перышкин 7-9 =====
    {
        "id": "ph7-density",
        "grade": 7, "subject": "физика", "topic": "плотность вещества",
        "subtopic": "механика", "tags": ["плотность", "масса", "объём"], "is_combined": False,
        "textbook": "Перышкин 7",
        "statement": "Найдите плотность тела массой 540 г и объёмом 200 см^3. Ответ выразите в г/см^3.",
    },
    {
        "id": "ph7-pressure-solid",
        "grade": 7, "subject": "физика", "topic": "давление твёрдого тела",
        "subtopic": "механика", "tags": ["давление", "сила", "площадь"], "is_combined": False,
        "textbook": "Перышкин 7",
        "statement": "Тело весом 240 Н давит на опору площадью 0,3 м^2. Найдите давление в паскалях.",
    },
    {
        "id": "ph7-work",
        "grade": 7, "subject": "физика", "topic": "механическая работа",
        "subtopic": "механика", "tags": ["работа", "сила", "путь"], "is_combined": False,
        "textbook": "Перышкин 7",
        "statement": "Какую работу совершает сила 150 Н на пути 8 м? Ответ в джоулях.",
    },
    {
        "id": "ph8-current-strength",
        "grade": 8, "subject": "физика", "topic": "сила тока",
        "subtopic": "электричество", "tags": ["ток", "напряжение", "сопротивление"], "is_combined": False,
        "textbook": "Перышкин 8",
        "statement": "Найдите силу тока в участке с сопротивлением 10 Ом и напряжением 24 В.",
    },
    {
        "id": "ph8-thermal-quantity",
        "grade": 8, "subject": "физика", "topic": "количество теплоты",
        "subtopic": "тепловые явления", "tags": ["теплота", "теплоёмкость"], "is_combined": False,
        "textbook": "Перышкин 8",
        "statement": "Сколько теплоты получит вода массой 0,5 кг при нагревании на 40 градусов? Удельная теплоёмкость воды 4200 Дж/(кг·°С).",
    },
    {
        "id": "ph9-uniform-motion",
        "grade": 9, "subject": "физика", "topic": "равномерное движение",
        "subtopic": "кинематика", "tags": ["скорость", "путь", "время"], "is_combined": False,
        "textbook": "Перышкин 9",
        "statement": "Тело движется равномерно со скоростью 15 м/с. Какой путь оно пройдёт за 12 секунд?",
    },
    {
        "id": "ph9-second-newton",
        "grade": 9, "subject": "физика", "topic": "второй закон Ньютона",
        "subtopic": "динамика", "tags": ["сила", "масса", "ускорение"], "is_combined": False,
        "textbook": "Перышкин 9",
        "statement": "На тело массой 4 кг действует сила 20 Н. Найдите ускорение в м/с^2.",
    },
    # ===== ФИЗИКА. Мякишев 10-11 =====
    {
        "id": "ph10-kinetic-energy",
        "grade": 10, "subject": "физика", "topic": "кинетическая энергия",
        "subtopic": "динамика", "tags": ["энергия", "скорость", "масса"], "is_combined": False,
        "textbook": "Мякишев 10",
        "statement": "Найдите кинетическую энергию тела массой 2 кг, движущегося со скоростью 6 м/с.",
    },
    {
        "id": "ph10-pendulum",
        "grade": 10, "subject": "физика", "topic": "период математического маятника",
        "subtopic": "колебания", "tags": ["маятник", "период"], "is_combined": False,
        "textbook": "Мякишев 10",
        "statement": "Найдите период колебаний математического маятника длиной 1 м. Ускорение свободного падения 9,8 м/с^2. Число пи принять равным 3,14.",
    },
    {
        "id": "ph11-photon-energy",
        "grade": 11, "subject": "физика", "topic": "энергия фотона",
        "subtopic": "квантовая", "tags": ["фотон", "энергия", "длина волны"], "is_combined": False,
        "textbook": "Мякишев 11",
        "statement": "Найдите энергию фотона с частотой 5*10^14 Гц. Постоянная Планка 6,63*10^-34 Дж·с.",
    },
    # ===== ХИМИЯ. Габриелян 8-9 =====
    {
        "id": "chem8-mass-fraction",
        "grade": 8, "subject": "химия", "topic": "массовая доля",
        "subtopic": "растворы", "tags": ["раствор", "массовая доля"], "is_combined": False,
        "textbook": "Габриелян 8",
        "statement": "Найдите массовую долю соли в растворе, если в 200 г раствора содержится 30 г соли. Ответ в процентах.",
    },
    {
        "id": "chem8-molar-mass",
        "grade": 8, "subject": "химия", "topic": "молярная масса",
        "subtopic": "количество вещества", "tags": ["молярная масса", "моль"], "is_combined": False,
        "textbook": "Габриелян 8",
        "statement": "Найдите количество вещества в 88 г углекислого газа CO2. Молярная масса CO2 равна 44 г/моль.",
    },
    {
        "id": "chem9-volume-gas",
        "grade": 9, "subject": "химия", "topic": "объём газа",
        "subtopic": "стехиометрия", "tags": ["объём", "газ", "моль"], "is_combined": False,
        "textbook": "Габриелян 9",
        "statement": "Найдите объём 2 моль водорода при нормальных условиях. Молярный объём 22,4 л/моль.",
    },
    {
        "id": "chem9-solution-prepare",
        "grade": 9, "subject": "химия", "topic": "приготовление раствора",
        "subtopic": "растворы", "tags": ["раствор", "массовая доля"], "is_combined": True,
        "textbook": "Габриелян 9",
        "statement": "Сколько граммов соли нужно для приготовления 250 г раствора с массовой долей соли 8%?",
    },
    # ===== ИНФОРМАТИКА. Босова 7-9 =====
    {
        "id": "inf7-binary-from-dec",
        "grade": 7, "subject": "информатика", "topic": "перевод в двоичную систему",
        "subtopic": "системы счисления", "tags": ["двоичная", "перевод"], "is_combined": False,
        "textbook": "Босова 7",
        "statement": "Переведите число 25 из десятичной системы в двоичную и запишите как десятичное число (без основания). Например, 5 -> 101.",
    },
    {
        "id": "inf7-info-volume",
        "grade": 7, "subject": "информатика", "topic": "количество информации",
        "subtopic": "информация", "tags": ["биты", "байты"], "is_combined": False,
        "textbook": "Босова 7",
        "statement": "Сколько байт информации в строке из 256 символов, если каждый символ кодируется 8 битами?",
    },
    {
        "id": "inf8-loop-sum",
        "grade": 8, "subject": "информатика", "topic": "сумма натуральных",
        "subtopic": "алгоритмы", "tags": ["цикл", "сумма"], "is_combined": False,
        "textbook": "Босова 8",
        "statement": "Найдите сумму всех натуральных чисел от 1 до 100.",
    },
    {
        "id": "inf9-perm",
        "grade": 9, "subject": "информатика", "topic": "перестановки",
        "subtopic": "комбинаторика", "tags": ["перестановки", "факториал"], "is_combined": False,
        "textbook": "Босова 9",
        "statement": "Сколько различных перестановок можно составить из 6 элементов?",
    },
    # ===== Доп. начальная школа =====
    {
        "id": "moro2-add-sub",
        "grade": 2, "subject": "математика", "topic": "сложение и вычитание в пределах 100",
        "subtopic": "арифметика", "tags": ["сложение", "вычитание", "до 100"], "is_combined": False,
        "textbook": "Моро 2",
        "statement": "Найдите значение выражения: 36 + 47 - 28.",
    },
    {
        "id": "moro3-mult-by-1digit",
        "grade": 3, "subject": "математика", "topic": "умножение на однозначное число",
        "subtopic": "арифметика", "tags": ["умножение"], "is_combined": False,
        "textbook": "Моро 3",
        "statement": "Найдите значение выражения: 28 * 4.",
    },
    {
        "id": "moro4-multistep-buy",
        "grade": 4, "subject": "математика", "topic": "задача в три действия",
        "subtopic": "комбинированная", "tags": ["комбинированная", "покупки"], "is_combined": True,
        "textbook": "Моро 4",
        "statement": "Маша купила 3 тетради по 18 рублей и 2 ручки по 25 рублей. Сколько сдачи она получит со 150 рублей?",
    },
]


def main() -> int:
    with LIB_PATH.open(encoding="utf-8") as f:
        lib = json.load(f)

    # 1) обогатить существующие items
    existing_ids = set()
    for it in lib["items"]:
        existing_ids.add(it["id"])
        it.setdefault("subject", "математика")
        if "textbook" not in it or it.get("textbook") is None:
            it["textbook"] = textbook_for(it)

    # 2) добавить новые (если их ещё нет)
    added = 0
    for new in NEW_ITEMS:
        if new["id"] in existing_ids:
            continue
        lib["items"].append(new)
        existing_ids.add(new["id"])
        added += 1

    # 3) обновить версию и описание
    lib["version"] = "2026.05.21"
    lib["description"] = (
        "Библиотека эталонных задач 1-11 класс. "
        "Математика (Виленкин 5-6, Макарычев 7-9, Атанасян 7-9, алгебра+геометрия 10-11), "
        "физика (Перышкин 7-9, Мякишев 10-11), химия (Габриелян 8-9), информатика (Босова 7-9). "
        "Используется как примеры для генератора вариантов."
    )

    with LIB_PATH.open("w", encoding="utf-8") as f:
        json.dump(lib, f, ensure_ascii=False, indent=2)

    print(f"всего записей: {len(lib['items'])}")
    print(f"добавлено новых: {added}")
    by_subject: dict[str, int] = {}
    for it in lib["items"]:
        by_subject[it["subject"]] = by_subject.get(it["subject"], 0) + 1
    print("по предметам:")
    for s, n in sorted(by_subject.items()):
        print(f"  {s}: {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

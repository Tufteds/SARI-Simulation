import matplotlib.pyplot as plt
import csv
from matplotlib.patches import Patch
from models import MathematicalModel
import json

data, cases = [], []
with open('data/school/orvi_cases.csv', 'r', encoding='UTF-8') as f1, \
      open('data/school/population.csv', 'r') as f2:
    rd1 = csv.DictReader(f1)
    rd2 = csv.DictReader(f2)
    for row in rd2:
        population = int(row['count'])
        break
    for n, row in enumerate(rd1, 1):
        data.append(n)
        cases.append(int(row['new_cases']))

colors = []
for day in data:
    if day % 6 == 0:
        colors.append('green')
    else:
        colors.append('steelblue')

fig, ax = plt.subplots()

ax.bar(data, cases, color=colors)
ax.set_ylabel('Количество заболевших')
ax.set_xlabel('День')
ax.set_title('Активность вируса ОРВИ 12.12.2025–29.12.2025')

math_model = MathematicalModel(population_size=population, days=len(data))
math_model.I = 87
math_model.V = 356
math_model.E = 20
math_model.run(print)
with open("data/simulation_history.json", "r", encoding="utf-8") as f:
    model_data = json.load(f)

model_cases = model_data["history"]["infected"]

print("День | Реальность | Модель | Разница")
print("-" * 35)
for d, real, model in zip(data, cases, model_cases):
    print(f"{d:>4} | {real:>10} | {model:>6} | {real-model:>8}")
print(math_model.beta)

fig, (ax1, ax2) = plt.subplots(
    2, 1,
    figsize=(10, 7),
    sharex=True,
    gridspec_kw={'height_ratios': [1, 2]}
)

# --- модель (верх) ---
ax1.bar(
    data,
    model_cases[:len(data)],
    color='crimson'
)
ax1.set_ylabel('Модель')
ax1.set_title('Результат математического моделирования')

# --- реальные данные (низ) ---
ax2.bar(
    data,
    cases,
    color=colors
)
ax2.set_ylabel('Реальность')
ax2.set_xlabel('День')

plt.tight_layout()
plt.show()


import matplotlib.pyplot as plt
import csv
from models import MathematicalModel
import json

# ------------------ ДАННЫЕ ------------------
with open('data/school/population.csv', 'r') as f2:
    rd2 = csv.DictReader(f2)
    for row in rd2:
        population = int(row['count'])
        break

# ------------------ МАТЕМАТИЧЕСКАЯ МОДЕЛЬ ------------------
math_model = MathematicalModel(population_size=population, days=13)  # 30 дней для примера
math_model.I = 87
math_model.V = 356
math_model.E = 20
math_model.run(print)

# Загружаем результаты
with open("data/simulation_history.json", "r", encoding="utf-8") as f:
    model_data = json.load(f)

model_cases = model_data["history"]["infected"]

# Дни для графика
data = list(range(1, len(model_cases) + 1))

# ------------------ ГРАФИК МОДЕЛИ ------------------
fig, ax = plt.subplots(figsize=(10,5))

ax.bar(
    data,
    model_cases,
    color='crimson'
)
ax.set_xlabel('День')
ax.set_ylabel('Количество заболевших')
ax.set_title('Результаты математической модели ОРВИ')
ax.set_ylim(0, max(model_cases)*1.05)  # чуть выше максимума для красоты

plt.tight_layout()
plt.show()

import matplotlib.pyplot as plt

# ------------------ ДАННЫЕ ------------------
model_cases = [
    21, 25, 27, 29, 31, 34, 36, 39, 41, 44, 46, 49, 52
]

# Дни для графика
data = list(range(1, len(model_cases)+1))

# ------------------ ГРАФИК ------------------
fig, ax = plt.subplots(figsize=(10,5))

ax.bar(
    data,
    model_cases,
    color='crimson'
)
ax.set_xlabel('День')
ax.set_ylabel('Количество заболевших')
ax.set_title('Результаты математической модели ОРВИ')
ax.set_ylim(0, max(model_cases)*1.05)  # чуть выше максимума для красоты

plt.tight_layout()
plt.show()

# ------------------ ТАБЛИЦА ------------------
print("День | Модель")
print("-" * 20)
for d, model in zip(data, model_cases):
    print(f"{d:>4} | {model:>6}")






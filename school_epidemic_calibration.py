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
    if (day-1) % 6 == 0:
        colors.append('gold')
    else:
        colors.append('steelblue')

fig, ax = plt.subplots()

ax.bar(data, cases, color=colors)
ax.set_ylabel('Количество заболевших')
ax.set_xlabel('День')
ax.set_title('Активность вируса ОРВИ 12.12.2025–29.12.2025')

legend_elements = [
    Patch(facecolor='steelblue', label='Обычный день'),
    Patch(facecolor='gold', label='Суббота')
]
ax.legend(handles=legend_elements)


math_model = MathematicalModel(population_size=population, days=len(data))
math_model.I = 27
math_model.V = 356
math_model.E = 20
math_model.beta = 0.5

math_model.run(print)
with open("data/simulation_history.json", "r", encoding="utf-8") as f:
    model_data = json.load(f)

model_cases = model_data["history"]["infected"]

print("День | Реальность | Модель | Разница")
print("-" * 35)
for d, real, model in zip(data, cases, model_cases):
    print(f"{d:>4} | {real:>10} | {model:>6} | {real-model:>8}")
print(math_model.beta)


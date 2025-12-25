import pandas as pd
from models import MathematicalModel

# 1. Загружаем данные
pop_df = pd.read_csv("data/school/population.csv")
vac_df = pd.read_csv("data/school/vaccination.csv")
cases_df = pd.read_csv("data/school/orvi_cases.csv")

N = int(pop_df["count"].sum())
vaccinated_percent = vac_df["vaccinated_percent"].mean()

real_cases = cases_df["new_cases"].tolist()  # [23, 27, 40, 32, 34]
days = len(real_cases)

I0 = real_cases[0]        # 23
E0 = int(0.3 * I0)        # логично
V0 = int(N * vaccinated_percent)
R0 = 0
S0 = N - V0 - I0 - E0

model = MathematicalModel(population_size=N, days=days)
model.beta = 0.5
model.gamma = 1/7

model.S = S0
model.V = V0
model.E = E0
model.I = I0
model.R = R0

history = model.run(lambda x: None)

print("День | Реальные ОРВИ | Модель")
for day in range(days):
    print(
        f"{day+1:>4} | {real_cases[day]:>13} | {history['infected'][day]}"
    )

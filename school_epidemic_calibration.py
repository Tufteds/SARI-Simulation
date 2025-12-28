import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import List, Dict
from sklearn.metrics import mean_squared_error, r2_score

# Начальные модули
import random
import numpy as np
import json
from collections import defaultdict
from abc import ABC, abstractmethod
from utils import singleton
from dataclasses import dataclass

@dataclass
class Immunity:
    innate_strength: float = 0.5        # врожденная устойчивость (0–1)
    adaptive_delay: int = 3             # дней до появления антител
    antibody_level: float = 0.0         # текущий уровень антител (0–1)
    memory_strength: float = 0.0        # иммунная память (0–1)
    memory_decay_rate: float = 0.01     # спад памяти
    immunocompromised: bool = False     # слабый иммунитет

# Вирус в единственном экземпляре
@singleton
class Virus:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.type = 'ОРВИ'
            cls._instance.time_incubation = 2
            cls._instance.base_duration = 6
            cls._instance.infection_probability = 0.12
        return cls._instance

virus = Virus()

class Person:
    def __init__(self):
        self.status = 'healthy'
        self.days_infected = 0
        self.incubation = 0
        self.immunity = Immunity()
        self.vaccinated = False
        self.days_since_vaccination = 0
        self._cured_time = 0

    # Логика обновления состояния и иммунитета
    def update_infections(self):
        # Обновляем иммунитет (антитела и память ослабевают)
        self.immunity.antibody_level = max(0, self.immunity.antibody_level * 0.99)
        self.immunity.memory_strength = max(
            0, self.immunity.memory_strength * (1 - self.immunity.memory_decay_rate)
        )

        # Обработка вакцинации для ВСЕХ статусов (кроме infected)
        if not self.vaccinated and self.status != 'infected' and random.random() < 0.001:
            self.vaccinated = True
            self._days_since_vaccination = 0
            # Вакцинация повышает иммунитет, но не так сильно как болезнь
            self.immunity.antibody_level = min(1.0, self.immunity.antibody_level + 0.3)
            self.immunity.memory_strength = min(1.0, self.immunity.memory_strength + 0.15)

        # Если вакцинирован, отслеживаем время
        if self.vaccinated:
            self._days_since_vaccination += 1
            # Вакцинный иммунитет ослабевает через 180 дней (полгода)
            if self._days_since_vaccination >= 180:
                self.vaccinated = False
                # Ослабление иммунитета при потере вакцинной защиты
                self.immunity.antibody_level *= 0.7
                self.immunity.memory_strength *= 0.8

        # Логика болезни
        if self.status == 'exposed':
            self.incubation += 1

            # адаптивный иммунитет начинает работать после задержки
            if self.incubation >= self.immunity.adaptive_delay:
                self.immunity.antibody_level += 0.02

            # переход в инфекционную фазу
            if self.incubation >= virus.time_incubation:
                self.status = 'infected'

        elif self.status == 'infected':
            self.days_infected += 1

            # активная выработка антител и рост памяти
            self.immunity.antibody_level = min(1.0, self.immunity.antibody_level + 0.05)
            self.immunity.memory_strength = min(1.0, self.immunity.memory_strength + 0.01)

            # завершение болезни
            if self.days_infected >= virus.base_duration:
                self.status = 'cured'
                self._cured_time = 10

        elif self.status == 'cured':
            self._cured_time -= 1
            if self._cured_time <= 0:
                self.status = 'healthy'
                self.days_infected = 0
                self.incubation = 0

class Population:
    def __init__(self, size, infected_count):
        self.people = [Person() for _ in range(size)]
        for person in random.sample(self.people, infected_count):
            person.status = 'exposed'

    def update(self):
        groups = self.group_by_status()
        new_infections = 0

        for person in self.people:
            person.update_infections()

        infected_group = groups['infected']
        exposed_group = groups['exposed']
        healthy_group = groups['healthy']

        if infected_group and healthy_group:

            random.shuffle(healthy_group)

            infectious = infected_group + exposed_group

            for sick_person in infectious:
                for _ in range(np.random.poisson(3)):
                    if not healthy_group:
                        break
                    target = healthy_group.pop()
                    chance = virus.infection_probability
                    chance *= (1 - target.immunity.innate_strength)
                    chance *= max(0.05, 1 - target.immunity.antibody_level)
                    chance *= (1 - target.immunity.memory_strength)

                    if target.immunity.immunocompromised:
                        chance *= 1.5

                    if random.random() < chance:
                        target.status = 'exposed'
                        target.incubation = 0
                        new_infections += 1

        return new_infections

    # группировка людей
    def group_by_status(self):
        groups = defaultdict(list)
        for person in self.people:
            groups[person.status].append(person)
        return groups


class BaseModel(ABC):
    def __init__(self, population_size, days):
        self.population_size = population_size
        self.days = days
        self.history = {}

    @abstractmethod
    def run(self, log_callback):
        pass

class AgentBasedModel(BaseModel):
    def __init__(self, population_size, days):
        super().__init__(population_size, days)
        self.population = Population(population_size, round(population_size * 0.01))
        self.history = {'healthy': [], 'vaccinated': [], 'exposed': [], 'infected': [], 'cured': []}
        self.peak_day = 0
        self.max_infected = 0

    def run(self, log_callback):
        for day in range(self.days):
            # Получаем актуальные группы
            groups = self.population.group_by_status()
            healthy = len(groups.get('healthy', []))
            exposed = len(groups.get('exposed', []))
            infected = len(groups.get('infected', []))
            cured = len(groups.get('cured', []))

            # Подсчитываем вакцинированных отдельно
            vaccinated_count = sum(1 for person in self.population.people
                                   if person.vaccinated)

            self.history['healthy'].append(healthy)
            self.history['vaccinated'].append(vaccinated_count)
            self.history['exposed'].append(exposed)
            self.history['infected'].append(infected)
            self.history['cured'].append(cured)

            if infected > self.max_infected:
                self.max_infected = infected
                self.peak_day = day

            log_callback(f"--- День {day + 1} ---")
            log_callback(
                f"Здоровые: {healthy}, Вакцинированные: {vaccinated_count}, "
                f"Подверженные: {exposed}, Заражённые: {infected}, Вылеченные: {cured}"
            )

            # раннее завершение, если эпидемия закончилась
            if (infected == 0 and exposed == 0) or healthy == 0:
                log_callback("Симуляция завершена.")
                break

            new_infected = self.population.update()
            log_callback(f"Новые заражённые: {new_infected}")

        return self.history

class MathematicalModel(BaseModel):
    def __init__(self, population_size, days):
        super().__init__(population_size, days)
        self.history = {'healthy': [], 'vaccinated': [], 'exposed': [], 'infected': [], 'cured': []}
        self.peak_day = 0
        self.max_infected = 0

        # SEIRS параметры
        self.beta = 0.3
        self.epsilon = 0.3
        self.vaccination_rate = 0.001
        self.omega_v = 1/180
        self.sigma = 1 / 2
        self.gamma = 1 / 6
        self.T_immunity = 90
        self.delta = 1 / self.T_immunity

        initial_exposed = round(population_size * 0.03)
        initial_infected = round(population_size * 0.02)
        self.S = population_size - initial_infected - initial_exposed
        self.V = 0
        self.E = initial_exposed
        self.I = initial_infected
        self.R = 0

    def run(self, log_callback):
        for day in range(self.days):
            new_exposed = self.beta * self.S * self.I / self.population_size
            new_vaccinations = self.vaccination_rate * self.S
            infected_vaccinated = self.epsilon * self.beta * self.V * self.I / self.population_size
            lost_immunity_v = self.omega_v * self.V
            new_infected = self.sigma * self.E
            new_recovered = self.gamma * self.I
            back_to_susceptible = self.delta * self.R

            self.S += back_to_susceptible - new_exposed - new_vaccinations + lost_immunity_v
            self.V += new_vaccinations - infected_vaccinated - lost_immunity_v
            self.E += new_exposed - new_infected - infected_vaccinated
            self.I += new_infected - new_recovered
            self.R += new_recovered - back_to_susceptible

            self.S = max(self.S, 0)
            self.V = max(self.V, 0)
            self.E = max(self.E, 0)
            self.I = max(self.I, 0)
            self.R = max(self.R, 0)

            self.history['healthy'].append(int(self.S))
            self.history['vaccinated'].append(int(self.V))
            self.history['exposed'].append(int(self.E))
            self.history['infected'].append(int(self.I))
            self.history['cured'].append(int(self.R))

            if self.I > self.max_infected:
                self.max_infected = int(self.I)
                self.peak_day = day

            log_callback(f"--- День {day+1} ---")
            log_callback(
                f"Здоровые: {int(self.S)}, Вакцинированные: {int(self.V)}, Подверженные: {int(self.E)}, "
                f"Заражённые: {int(self.I)}, Вылеченные: {int(self.R)}"
            )

            log_callback(f"Новые заражённые: {int(new_exposed)}")

        return self.history

class HybrydModel(BaseModel):
    def run(self, log_callback):
        log_callback("Гибридная модель пока не реализована.")
        return {'healthy': [], 'exposed': [], 'infected': [], 'cured': []}


@dataclass
class SchoolData:
    """Класс для хранения данных школы"""
    population: int
    vaccinated: int
    real_cases: List[int]
    dates: List[str]

    @property
    def vaccination_rate(self) -> float:
        return self.vaccinated / self.population

    @property
    def total_cases(self) -> int:
        return sum(self.real_cases)


# ================== Часть 3: Адаптированные модели для школы ==================
class SchoolAgentBasedModel(AgentBasedModel):
    """Агентная модель, адаптированная под школу"""

    def __init__(self, school_data: SchoolData, days: int = 5):
        super().__init__(school_data.population, days)
        self.school_data = school_data
        self._initialize_for_school()

    def _initialize_for_school(self):
        """Инициализация с реальными данными школы"""
        # Инициализируем вакцинированных
        vaccinated_count = self.school_data.vaccinated
        people_to_vaccinate = random.sample(self.population.people, vaccinated_count)
        for person in people_to_vaccinate:
            person.vaccinated = True
            person.immunity.antibody_level = 0.4

        # Инициализируем начальные случаи
        initial_cases = self.school_data.real_cases[0] if self.school_data.real_cases else 10
        people_to_infect = random.sample(self.population.people, min(initial_cases, len(self.population.people)))
        for person in people_to_infect:
            if person.vaccinated:
                if random.random() < 0.5:  # 50% эффективность
                    person.status = 'exposed'
            else:
                person.status = 'exposed'


class SchoolMathematicalModel(MathematicalModel):
    """Математическая модель, адаптированная под школу"""

    def __init__(self, school_data: SchoolData, days: int = 5):
        super().__init__(school_data.population, days)
        self.school_data = school_data

        # Переопределяем начальные условия
        self.S = school_data.population - school_data.vaccinated
        self.V = school_data.vaccinated
        self.E = int(school_data.real_cases[0] * 0.3)
        self.I = int(school_data.real_cases[0] * 0.7)
        self.R = 0


# ================== Часть 4: Калибратор с интерфейсом ==================
class ModelCalibrator:
    """Инструмент для калибровки моделей"""

    def __init__(self, school_data: SchoolData):
        self.data = school_data
        self.results = {}

    def run_agent_model(self, **params):
        """Запуск агентной модели"""
        model = SchoolAgentBasedModel(self.data, days=len(self.data.real_cases))
        # Здесь можно настроить параметры модели через params
        history = model.run(lambda x: None)  # Без вывода логов

        # Извлекаем новые случаи из истории
        simulated_cases = self._extract_new_cases_from_history(history)

        return self._analyze_results(simulated_cases, "agent", params)

    def run_math_model(self, **params):
        """Запуск математической модели"""
        model = SchoolMathematicalModel(self.data, days=len(self.data.real_cases))
        history = model.run(lambda x: None)

        simulated_cases = self._extract_new_cases_from_history(history)

        return self._analyze_results(simulated_cases, "math", params)

    def _extract_new_cases_from_history(self, history):
        """Извлекает новые случаи из истории модели"""
        # Простая логика: считаем, что новые случаи = exposed каждый день
        return history.get('exposed', [])[:len(self.data.real_cases)]

    def _analyze_results(self, simulated, model_type, params):
        """Анализирует результаты моделирования"""
        if len(simulated) != len(self.data.real_cases):
            simulated = simulated[:len(self.data.real_cases)]

        comparison = {
            'simulated': simulated,
            'real': self.data.real_cases,
            'mse': mean_squared_error(self.data.real_cases, simulated),
            'r2': r2_score(self.data.real_cases, simulated),
            'params': params
        }

        self.results[model_type] = comparison
        return comparison

    def plot_comparison(self, model_type="agent"):
        """Рисует график сравнения"""
        if model_type not in self.results:
            print(f"Нет результатов для модели {model_type}")
            return

        result = self.results[model_type]

        plt.figure(figsize=(10, 6))
        days = range(1, len(result['real']) + 1)

        plt.plot(days, result['real'], 'bo-', label='Реальные данные', linewidth=2)
        plt.plot(days, result['simulated'], 'rs--', label='Модель', linewidth=2)

        plt.xlabel('День')
        plt.ylabel('Новые случаи')
        plt.title(f'Сравнение: {model_type} модель\nMSE: {result["mse"]:.1f}, R²: {result["r2"]:.3f}')
        plt.legend()
        plt.grid(True, alpha=0.3)

        # Подписи значений
        for i, (real_val, sim_val) in enumerate(zip(result['real'], result['simulated'])):
            plt.text(i + 1, real_val + 2, str(real_val), ha='center', color='blue')
            plt.text(i + 1, sim_val - 2, str(int(sim_val)), ha='center', color='red')

        plt.show()

    def interactive_mode(self):
        """Интерактивный режим калибровки"""
        print("=== КАЛИБРОВКА МОДЕЛИ РАСПРОСТРАНЕНИЯ ОРВИ В ШКОЛЕ ===")
        print(f"Данные школы: {self.data.population} человек, {self.data.vaccinated} вакцинированы")
        print(f"Реальные случаи: {self.data.real_cases}")
        print()

        while True:
            print("\nВыберите действие:")
            print("1. Запустить агентную модель")
            print("2. Запустить математическую модель")
            print("3. Сравнить обе модели")
            print("4. Выйти")

            choice = input("Ваш выбор (1-4): ")

            if choice == "1":
                print("\nЗапуск агентной модели...")
                result = self.run_agent_model()
                print(f"Результаты: MSE={result['mse']:.1f}, R²={result['r2']:.3f}")
                self.plot_comparison("agent")

            elif choice == "2":
                print("\nЗапуск математической модели...")
                result = self.run_math_model()
                print(f"Результаты: MSE={result['mse']:.1f}, R²={result['r2']:.3f}")
                self.plot_comparison("math")

            elif choice == "3":
                if "agent" in self.results and "math" in self.results:
                    plt.figure(figsize=(12, 6))
                    days = range(1, len(self.data.real_cases) + 1)

                    plt.subplot(1, 2, 1)
                    plt.plot(days, self.results['agent']['real'], 'bo-', label='Реальные')
                    plt.plot(days, self.results['agent']['simulated'], 'r--', label='Агентная')
                    plt.title(f"Агентная (MSE: {self.results['agent']['mse']:.1f})")
                    plt.legend()

                    plt.subplot(1, 2, 2)
                    plt.plot(days, self.results['math']['real'], 'bo-', label='Реальные')
                    plt.plot(days, self.results['math']['simulated'], 'g--', label='Математическая')
                    plt.title(f"Математическая (MSE: {self.results['math']['mse']:.1f})")
                    plt.legend()

                    plt.tight_layout()
                    plt.show()
                else:
                    print("Сначала запустите обе модели!")

            elif choice == "4":
                print("Выход...")
                break
            else:
                print("Неверный выбор, попробуйте снова.")


# ================== Часть 5: Главная функция запуска ==================
def main():
    """Главная функция для запуска программы"""

    # 1. Создаем объект с данными вашей школы
    my_school_data = SchoolData(
        population=831,
        vaccinated=406,
        real_cases=[51, 68, 83, 87, 86],
        dates=['2025-12-12', '2025-12-13', '2025-12-14', '2025-12-15', '2025-12-16']
    )

    print("=" * 50)
    print("МОДЕЛИРОВАНИЕ ВСПЫШКИ ОРВИ В ШКОЛЕ")
    print("=" * 50)
    print(f"Общая популяция: {my_school_data.population} человек")
    print(f"Вакцинировано: {my_school_data.vaccinated} ({my_school_data.vaccination_rate * 100:.1f}%)")
    print(f"Реальные случаи за 5 дней: {my_school_data.real_cases}")
    print(
        f"Всего случаев: {my_school_data.total_cases} ({my_school_data.total_cases / my_school_data.population * 100:.1f}% популяции)")
    print("=" * 50)

    # 2. Создаем калибратор
    calibrator = ModelCalibrator(my_school_data)

    # 3. Запускаем интерактивный режим
    calibrator.interactive_mode()

    # ИЛИ можно запустить конкретные модели:
    # result_agent = calibrator.run_agent_model()
    # result_math = calibrator.run_math_model()
    # calibrator.plot_comparison("agent")
    # calibrator.plot_comparison("math")


# ================== Запуск программы ==================
if __name__ == "__main__":
    # Убедитесь, что у вас установлены необходимые библиотеки:
    # pip install numpy matplotlib scikit-learn

    # Запускаем программу
    main()
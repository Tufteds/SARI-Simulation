# Начальные модули
import random
from collections import defaultdict
from abc import ABC, abstractmethod
from utils import singleton

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

# Человек
class Person:
    def __init__(self, immunity):
        self.status = 'healthy'
        self.days_infected = 0
        self.incubation = 0
        self.immunity = immunity
        self.immunity_effects = {'low': 1, 'medium': 0, 'strong': -1}
        self._cured_time = 0

    # Логика обновления статуса
    def update_infections(self):
        if self.status == 'exposed':
            self.incubation += 1
            if self.incubation >= virus.time_incubation:
                self.status = 'infected'
        elif self.status == 'infected':
            self.days_infected += 1
            if self.days_infected >= virus.base_duration + self.immunity_effects[self.immunity]:
                self.status = 'cured'
        elif self.status == 'cured':
            self._cured_time -= 1
            if self._cured_time <= 0:
                self.status = 'healthy'
                self.days_infected = 0
                self.incubation = 0

# Популяция
class Population:
    def __init__(self, size, infected_count):
        self.people = [Person(random.choice(['low', 'medium', 'strong'])) for _ in range(size)]
        # Наделение начальных людей зараженными
        for person in random.sample(self.people, infected_count):
            person.status = 'exposed'

    # Механизм заражения
    def update(self):
        groups = self.group_by_status()
        new_infections = 0

        for person in self.people:
            person.update_infections()

        infected_group = groups['infected']
        healthy_group = groups['healthy']

        if infected_group and healthy_group:
            random.shuffle(healthy_group)
            for infected_person in infected_group:
                for _ in range(2):
                    if not healthy_group:
                        break
                    target = healthy_group.pop()
                    # Сравнение случайного шанса с заболеваемостью вируса
                    if random.random() < virus.infection_probability:
                        target.status = 'exposed'
                        target.incubation = 0
                        new_infections += 1
        return new_infections

    # Группировка по статусу
    def group_by_status(self):
        groups = defaultdict(list)
        for person in self.people:
            groups[person.status].append(person)
        return groups

    # Получение статистики
    def get_statistics(self):
        return {status: len(group) for status, group in self.group_by_status().items()}

# Абстрактный класс моделей
class BaseModel(ABC):
    def __init__(self, population_size, days):
        self.population_size = population_size
        self.days = days
        self.history = {}

    @abstractmethod
    def run(self, log_callback):
        pass

# Агентная модель
class AgentBasedModel(BaseModel):
    def __init__(self, population_size, days):
        super().__init__(population_size, days)
        self.population = Population(population_size, round(population_size * 0.05))
        self.history = {'healthy': [], 'exposed': [], 'infected': [], 'cured': []}
        self.peak_day = 0
        self.max_infected = 0

    # Запуск относительно агентной модели
    def run(self, log_callback):
        for day in range(self.days):
            groups = self.population.group_by_status()
            healthy = len(groups.get('healthy', []))
            exposed = len(groups.get('exposed', []))
            infected = len(groups.get('infected', []))
            cured = len(groups.get('cured', []))

            self.history['healthy'].append(healthy)
            self.history['exposed'].append(exposed)
            self.history['infected'].append(infected)
            self.history['cured'].append(cured)

            if infected > self.max_infected:
                self.max_infected = infected
                self.peak_day = day

            log_callback(f"--- День {day + 1} ---")
            log_callback(
                f"Здоровые: {healthy}, Подверженные: {exposed}, Заражённые: {infected}, Вылеченные: {cured}"
            )

            if (infected == 0 and exposed == 0) or healthy == 0:
                log_callback("Симуляция завершена.")
                break

            new_infected = self.population.update()
            log_callback(f"Новые заражённые: {new_infected}")

        return self.history

# Математическая модель
class MathematicalModel(BaseModel):
    def __init__(self, population_size, days):
        super().__init__(population_size, days)
        self.population = Population(population_size, round(population_size * 0.05))
        self.history = {'healthy': [], 'exposed': [], 'infected': [], 'cured': []}
        self.peak_day = 0
        self.max_infected = 0

        self.beta = 0.3
        self.sigma = 1/2
        self.gamma = 1/6
        self.T_immunity = 10
        self.delta = 1 / self.T_immunity

        initial_infected = round(population_size * 0.05)
        self.S = population_size - initial_infected
        self.E = initial_infected
        self.I = 0
        self.R = 0

    # Запуск относительно математической модели
    def run(self, log_callback):
        for day in range(self.days):
            new_exposed = self.beta * self.S * self.I / self.population_size
            new_infected = self.sigma * self.E
            new_recovered = self.gamma * self.I
            back_to_susceptible = self.delta * self.R

            self.S += back_to_susceptible - new_exposed
            self.E += new_exposed - new_infected
            self.I += new_infected - new_recovered
            self.R += new_recovered - back_to_susceptible

            self.S = max(self.S, 0)
            self.E = max(self.E, 0)
            self.I = max(self.I, 0)
            self.R = max(self.R, 0)

            self.history['healthy'].append(int(self.S))
            self.history['exposed'].append(int(self.E))
            self.history['infected'].append(int(self.I))
            self.history['cured'].append(int(self.R))

            if self.I > self.max_infected:
                self.max_infected = int(self.I)
                self.peak_day = day

            log_callback(f"--- День {day+1} ---")
            log_callback(
                f"Здоровые: {int(self.S)}, Подверженные: {int(self.E)}, "
                f"Заражённые: {int(self.I)}, Вылеченные: {int(self.R)}"
            )

        return self.history

# Гибридная модель
class HybrydModel(BaseModel):
    def run(self, log_callback):
        log_callback("Гибридная модель пока не реализована.")
        return {'healthy': [], 'exposed': [], 'infected': [], 'cured': []}

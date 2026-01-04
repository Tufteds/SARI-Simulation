# Начальные модули
import random
import numpy as np
import json
from collections import defaultdict
from abc import ABC, abstractmethod
from utils import singleton, Utils
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
        self.history_file = "data/simulation_history.json"

        # SEIRS параметры
        self.beta = 0.3
        self.epsilon = 0.3
        self.vaccination_rate = 0.3
        self.omega_v = 1/180
        self.sigma = 1 / 1.5
        self.gamma = 1 / 7
        self.T_immunity = 90
        self.delta = 1 / self.T_immunity

        initial_exposed = round(population_size * 0.03)
        initial_infected = round(population_size * 0.05)
        self.V = round(0.46 * population_size)
        self.S = population_size - initial_infected - initial_exposed - self.V
        self.E = initial_exposed
        self.I = initial_infected
        self.R = 0

    def run(self, log_callback):
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump({}, f)

        for day in range(self.days):
            k = Utils.activity_factor(day)

            if day <= self.peak_day:
                effective_gamma = self.gamma
                effective_beta = self.beta
            elif day - self.peak_day >= 3:
                effective_gamma = self.gamma * 1.3
                effective_beta = self.beta * 0.1
            else:
                effective_gamma = self.gamma*1.2
                effective_beta = self.beta*k

            new_exposed = effective_beta* self.S * self.I *k / self.population_size
            new_vaccinations = self.vaccination_rate * self.S
            infected_vaccinated = self.epsilon * effective_beta * k * self.V * self.I / self.population_size
            lost_immunity_v = self.omega_v * self.V
            new_infected = self.sigma * self.E
            new_recovered = effective_gamma * self.I
            back_to_susceptible = self.delta * self.R

            self.S += back_to_susceptible - new_exposed - new_vaccinations + lost_immunity_v
            self.V += new_vaccinations - infected_vaccinated - lost_immunity_v
            self.E += new_exposed + infected_vaccinated - new_infected
            self.I += new_infected - new_recovered
            self.R += new_recovered - back_to_susceptible

            self.S = max(self.S, 0)
            self.V = max(self.V, 0)
            self.E = max(self.E, 0)
            self.I = max(self.I, 0)
            self.R = max(self.R, 0)


            if (day+1)%6==0:
                observed_i = self.I*0.3
            else:
                observed_i = self.I


            self.history['healthy'].append(int(self.S))
            self.history['vaccinated'].append(int(self.V))
            self.history['exposed'].append(int(self.E))
            self.history['infected'].append(int(observed_i))
            self.history['cured'].append(int(self.R))

            if self.I > self.max_infected:
                self.max_infected = int(self.I)
                self.peak_day = day

            log_callback(f"--- День {day+1} ---")
            log_callback(
                f"Здоровые: {int(self.S)}, Вакцинированные: {int(self.V)}, Подверженные: {int(self.E)}, "
                f"Заражённые: {int(self.I)}, Вылеченные: {int(self.R)}"
            )

            log_callback(f"Новые заражённые: {int(new_infected)}")

            result = {
                "meta": {
                    "population_size": self.population_size,
                    "days": self.days,
                    "peak_day": self.peak_day + 1,
                    "max_infected": self.max_infected,
                },
                "parameters": {
                    "beta": self.beta,
                    "epsilon": self.epsilon,
                    "vaccination_rate": self.vaccination_rate,
                    "omega_v": self.omega_v,
                    "sigma": self.sigma,
                    "gamma": self.gamma,
                    "T_immunity": self.T_immunity,
                    "delta": self.delta
                },
                "history": self.history
            }

            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=4)

        return self.history

class HybrydModel(BaseModel):
    def run(self, log_callback):
        log_callback("Гибридная модель пока не реализована.")
        return {'healthy': [], 'exposed': [], 'infected': [], 'cured': []}

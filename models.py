# Начальные модули
import random
import numpy as np
import json
from collections import defaultdict
from abc import ABC, abstractmethod
from utils import singleton, Utils
from dataclasses import dataclass, field
from enum import Enum, auto

class HealthState(Enum):
    SUSCEPTIBLE = auto()
    EXPOSED = auto()
    INFECTED = auto()
    RECOVERED = auto()
    VACCINATED = auto()

class Parameters(Enum):
    AGE_SUSCEPTIBILITY = {
        "child": 1.2,
        "teen": 1.0,
        "adult": 0.9,
    }

    ROLE_INFECTIVITY = {
        "student": 1.0,
        "teacher": 1.1,
    }

    CONTACT_WEIGHT = {
        ("student", "student"): 1.0,
        ("student", "teacher"): 1.3,
        ("teacher", "student"): 1.3,
        ("teacher", "teacher"): 0.7,
    }

@dataclass
class Immunity:
    innate_strength: float = 0.5        # врожденная устойчивость (0–1)
    adaptive_delay: int = 3             # дней до появления антител
    antibody_level: float = 0.0         # текущий уровень антител (0–1)
    memory_strength: float = 0.0        # иммунная память (0–1)
    memory_decay_rate: float = 0.01     # спад памяти
    immunocompromised: bool = False     # слабый иммунитет

with open('data/school/classes.json', 'r', encoding='UTF-8') as f:
    SCHOOL_CONFIG = json.load(f)

@singleton
class Virus:
    def __new__(cls):
        obj = super().__new__(cls)
        obj.type = "ОРВИ"
        obj.time_incubation = 2
        obj.base_duration = 7
        obj.infection_probability = 0.02  # ↓ чтобы не вымирали за 10 дней
        return obj
virus = Virus()

@dataclass
class Person:
    id: int
    role: str
    age: int
    class_id: str | None = None
    is_homeroom: bool = False

    state: HealthState = HealthState.SUSCEPTIBLE
    immunity: Immunity = field(default_factory=Immunity)

    days_exposed: int = 0
    days_infected: int = 0
    days_since_recovery: int = 0
    days_since_vaccination: int = 0

    incubation_period: int = 2
    infectious_period: int = 7

    # ---------

    def age_group(self):
        if self.age <= 10:
            return "child"
        elif self.age <= 18:
            return "teen"
        return "adult"

    def is_infectious(self):
        return self.state == HealthState.INFECTED

    def can_be_infected(self):
        return self.state in (
            HealthState.SUSCEPTIBLE,
            HealthState.VACCINATED
        )

    def exposed(self):
        if self.can_be_infected():
            self.state = HealthState.EXPOSED
            self.days_exposed = 0

    def vaccinate(self):
        self.state = HealthState.VACCINATED
        self.days_since_vaccination = 0
        self.immunity.antibody_level = min(1.0, self.immunity.antibody_level + 0.6)
        self.immunity.memory_strength = min(1.0, self.immunity.memory_strength + 0.4)

    # ---------

    def update(self):
        if self.state == HealthState.EXPOSED:
            self.days_exposed += 1
            if self.days_exposed >= self.incubation_period:
                self.state = HealthState.INFECTED
                self.days_infected = 0

        elif self.state == HealthState.INFECTED:
            self.days_infected += 1
            if self.days_infected >= self.infectious_period:
                self.state = HealthState.RECOVERED
                self.days_since_recovery = 0
                self.immunity.antibody_level = min(1.0, self.immunity.antibody_level + 0.7)
                self.immunity.memory_strength = min(1.0, self.immunity.memory_strength + 0.5)

        elif self.state == HealthState.RECOVERED:
            self.days_since_recovery += 1

            # экспоненциальный спад
            self.immunity.antibody_level *= 0.97
            self.immunity.memory_strength *= (1 - self.immunity.memory_decay_rate)

            if self.immunity.antibody_level < 0.2:
                self.state = HealthState.SUSCEPTIBLE
                self.days_since_recovery = 0

        elif self.state == HealthState.VACCINATED:
            self.days_since_vaccination += 1
            self.immunity.antibody_level *= 0.985


class Population:
    def __init__(self, config=SCHOOL_CONFIG):
        self.config = config
        self.students = []
        self.teachers = []
        self.classes = {}
        self._next_id = 0

        self._build_students()
        self._build_teachers()

    # ---------

    def random_infections(self, chance=0.002):
        """
        chance — вероятность заражения каждого человека вне контактов
        """
        for p in self.students + self.teachers:
            if p.can_be_infected() and random.random() < chance:
                p.exposed()

    def _build_students(self):
        for class_id, info in self.config["classes"].items():
            grade, size = info["grade"], info["size"]
            self.classes[class_id] = []

            age_min, age_max = Utils.age_range_for_grade(grade)

            for _ in range(size):
                s = Person(
                    id=self._next_id,
                    role="student",
                    age=random.randint(age_min, age_max),
                    class_id=class_id
                )
                self.students.append(s)
                self.classes[class_id].append(s)
                self._next_id += 1

    def _build_teachers(self):
        for class_id in self.classes:
            t = Person(
                id=self._next_id,
                role="teacher",
                age=random.randint(30, 60),
                class_id=class_id,
                is_homeroom=True
            )
            self.teachers.append(t)
            self._next_id += 1

        for _ in range(30):
            t = Person(
                id=self._next_id,
                role="teacher",
                age=random.randint(30, 60)
            )
            self.teachers.append(t)
            self._next_id += 1

    # ---------

    def get_daily_contacts(self, person: Person):
        contacts = []

        if person.role == "student":
            contacts.extend(random.sample(self.classes[person.class_id], min(3, len(self.classes[person.class_id]))))

            for t in self.teachers:
                if t.is_homeroom and t.class_id == person.class_id:
                    contacts.append(t)

            others = [t for t in self.teachers if not t.is_homeroom]
            contacts.extend(random.sample(others, min(2, len(others))))

        else:
            if person.is_homeroom:
                contacts.extend(self.classes[person.class_id])

            for cls in random.sample(list(self.classes.values()), min(2, len(self.classes))):
                contacts.extend(cls)

        return contacts

    def try_infect(self, source: Person, target: Person):
        if not source.is_infectious():
            return
        if not target.can_be_infected():
            return

        beta = virus.infection_probability
        w = Parameters.CONTACT_WEIGHT.value[(source.role, target.role)]
        s = Parameters.AGE_SUSCEPTIBILITY.value[target.age_group()]
        i = Parameters.ROLE_INFECTIVITY.value[source.role]

        immunity_factor = 1 - (
            target.immunity.antibody_level * 0.7 +
            target.immunity.memory_strength * 0.3
        )

        p = beta * w * s * i * immunity_factor
        p *= random.uniform(0.7, 1.0)  # немного случайности
        p = max(0.0, min(p, 0.9))

        if random.random() < p:
            target.exposed()

    def step_day(self):
        self.random_infections(chance=0.002)  # можно подбирать под динамику

        # 2) заражения через контакты
        infected = [p for p in self.students + self.teachers if p.is_infectious()]
        for source in infected:
            for target in self.get_daily_contacts(source):
                if target.id != source.id:
                    self.try_infect(source, target)

        # 3) обновляем состояния
        for p in self.students + self.teachers:
            p.update()

        all_p = self.students + self.teachers
        return {
            "S": sum(p.state == HealthState.SUSCEPTIBLE for p in all_p),
            "E": sum(p.state == HealthState.EXPOSED for p in all_p),
            "I": sum(p.state == HealthState.INFECTED for p in all_p),
            "R": sum(p.state == HealthState.RECOVERED for p in all_p),
            "V": sum(p.state == HealthState.VACCINATED for p in all_p),
            }

    def vaccinate_population(self, rate=0.5):
        susceptible = [
            p for p in self.students + self.teachers
            if p.state == HealthState.SUSCEPTIBLE
        ]
        for p in random.sample(susceptible, int(len(susceptible) * rate)):
            p.vaccinate()


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
        self.population = Population()
        self.history = {'healthy': [], 'vaccinated': [], 'exposed': [], 'infected': [], 'cured': []}
        self.peak_day = 0
        self.max_infected = 0
        for _ in range(5):
            random.choice(self.population.students).state = HealthState.INFECTED

    def run(self, log_callback):
        for day in range(self.days):
            stats = self.population.step_day()

            S = stats["S"]
            E = stats["E"]
            I = stats["I"]
            R = stats["R"]
            V = stats["V"]

            self.history['healthy'].append(S)
            self.history['vaccinated'].append(V)
            self.history['exposed'].append(E)
            self.history['infected'].append(I)
            self.history['cured'].append(R)

            if I > self.max_infected:
                self.max_infected = I
                self.peak_day = day

            log_callback(f"--- День {day + 1} ---")
            log_callback(
                f"Здоровые: {S}, Вакцинированные: {V}, "
                f"Подверженные: {E}, Заражённые: {I}, Вылеченные: {R}"
            )

            # раннее завершение, если эпидемия закончилась
            if I == 0 and E == 0:
                log_callback("Симуляция завершена.")
                break

        return self.history

class MathematicalModel(BaseModel):
    def __init__(self, population_size, days):
        super().__init__(population_size, days)
        self.history = {'healthy': [], 'vaccinated': [], 'exposed': [], 'infected': [], 'cured': []}
        self.peak_day = 0
        self.max_infected = 0
        self.history_file = "data/simulation_history.json"

        # SEIRS параметры
        self.beta = 0.2
        self.epsilon = 0.3
        self.vaccination_rate = 0.1
        self.omega_v = 1/180
        self.sigma = 1 / 1.5
        self.gamma = 1 / 7
        self.T_immunity = 90
        self.delta = 1 / self.T_immunity

        initial_exposed = round(population_size * 0.03)
        initial_infected = round(population_size * 0.05)
        self.V = 0
        self.S = population_size - initial_infected - initial_exposed - self.V
        self.E = initial_exposed
        self.I = initial_infected
        self.R = 0

    def seasonal_factor(self, day):
        year = 365
        return (
                1
                + 0.35 * np.sin(2 * np.pi * day / year)
                + 0.20 * np.sin(4 * np.pi * day / year)
        )

    def vaccination_campaign(self, day):
        """
        Импульсная вакцинация: 2 кампании в год
        """
        start, end = 90, 120
        if start <= day <= end:
                return 0.05  # 5% от S в день
        return 0.0

    def run(self, log_callback):
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump({}, f)

        for day in range(self.days):
            activity_factor = Utils.activity_factor(day)
            season_factor = self.seasonal_factor(day)

            vacc_rate_today = self.vaccination_campaign(day)
            new_vaccinations = vacc_rate_today * self.S

            effective_beta = self.beta * season_factor * activity_factor
            effective_gamma = self.gamma
            imported_exposed = 0.3 * season_factor

            new_exposed = effective_beta * self.S * self.I / self.population_size
            infected_vaccinated = self.epsilon * effective_beta * self.V * self.I / self.population_size
            lost_immunity_v = self.omega_v * self.V
            new_infected = self.sigma * self.E
            new_recovered = effective_gamma * self.I
            back_to_susceptible = self.delta * self.R

            self.S += back_to_susceptible - new_exposed - new_vaccinations + lost_immunity_v
            self.V += new_vaccinations - infected_vaccinated - lost_immunity_v
            self.E += new_exposed + infected_vaccinated - new_infected + imported_exposed
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

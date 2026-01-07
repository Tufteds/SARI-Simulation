import json
from dataclasses import dataclass, field
from enum import Enum, auto
from utils import singleton

with open('data/school/classes.json', 'r', encoding='UTF-8') as f:
    SCHOOL_CONFIG = json.load(f)

class HealthState(Enum):
    SUSCEPTIBLE = auto()
    EXPOSED = auto()
    INFECTED = auto()
    RECOVERED = auto()
    VACCINATED = auto()

@singleton
class Virus:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.type = 'ОРВИ'
            cls._instance.time_incubation = 2
            cls._instance.base_duration = 7
            cls._instance.infection_probability = 0.12
        return cls._instance

virus = Virus()

@dataclass
class Immunity:
    innate_strength: float = 0.5        # врожденная устойчивость (0–1)
    adaptive_delay: int = 3             # дней до появления антител
    antibody_level: float = 0.0         # текущий уровень антител (0–1)
    memory_strength: float = 0.0        # иммунная память (0–1)
    memory_decay_rate: float = 0.01     # спад памяти
    immunocompromised: bool = False

@dataclass
class Person:
    id: int
    role: str
    age: int

    state: HealthState = HealthState.SUSCEPTIBLE
    immunity: Immunity = field(default_factory=Immunity)

    days_infected: int = 0
    days_exposed: int = 0
    days_since_vaccination: int = 0
    days_since_recovery: int = 0

    incubation_period: int = 2
    infectious_period: int = 7

    def is_infectious(self) -> bool:
        return self.state ==  HealthState.INFECTED

    def can_be_infected(self) -> bool:
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
        self.immunity.antibody_level = min(
            1.0,
            self.immunity.antibody_level + 0.5
        )
        self.immunity.memory_strength = min(
            1.0,
            self.immunity.memory_strength + 0.3
        )

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
                self.immunity.antibody_level = min(1.0, self.immunity.antibody_level + 0.6)

        elif self.state == HealthState.RECOVERED:
            self.days_since_recovery += 1
            self.immunity.antibody_level *= 0.995
            self.immunity.memory_strength *= (1 - self.immunity.memory_decay_rate)

        elif self.state == HealthState.VACCINATED:
            self.days_since_vaccination += 1
            self.immunity.antibody_level *= 0.998

class Population:
    def __init__(self, config=SCHOOL_CONFIG):
        self.config = config
        self.students = []
        self.teacher = []
        self.classes = {}
        self._next_id = 0

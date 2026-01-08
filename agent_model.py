import json
import random
from dataclasses import dataclass, field
from enum import Enum, auto
from utils import Utils, singleton

with open('data/school/classes.json', 'r', encoding='UTF-8') as f:
    SCHOOL_CONFIG = json.load(f)

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
    class_id: str | None = None
    is_homeroom: bool = False

    state: HealthState = HealthState.SUSCEPTIBLE
    immunity: Immunity = field(default_factory=Immunity)

    days_infected: int = 0
    days_exposed: int = 0
    days_since_vaccination: int = 0
    days_since_recovery: int = 0

    incubation_period: int = 2
    infectious_period: int = 7

    def is_infectious(self) -> bool:
        return self.state == HealthState.INFECTED

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
    def age_group(self):
        if self.age <= 10:
            return 'child'
        elif self.age <= 18:
            return 'teen'
        return 'adult'

class Population:
    def __init__(self, config=SCHOOL_CONFIG):
        self.config = config
        self.students = []
        self.teachers = []
        self.classes = {}
        self._next_id = 0

        self._build_students()
        self._build_teachers()

    def _build_students(self):
        for class_id, info in self.config['classes'].items():
            grade, size = info['grade'], info['size']

            self.classes[class_id] = []
            age_min, age_max = Utils.age_range_for_grade(grade)

            for _ in range(size):
                student = Person(
                    id=self._next_id,
                    role='student',
                    age=random.randint(age_min, age_max),
                )
                student.class_id = class_id

                self.students.append(student)
                self.classes[class_id].append(student)

                self._next_id += 1

    def _build_teachers(self):
        for class_id in self.classes:
            teacher = Person(
                id=self._next_id,
                role='teacher',
                age=random.randint(30, 60),
            )
            teacher.class_id = class_id
            teacher.is_homeroom = True

            self.teachers.append(teacher)
            self._next_id += 1

        total_staff = self.config.get("teachers_per_class", 63)
        max_teachers = 40
        current = len(self.teachers)

        n_additional = max(0, min(max_teachers - current, total_staff - current))

        for _ in range(n_additional):
            teacher = Person(
                id = self._next_id,
                role='teacher',
                age=random.randint(30, 60),
            )
            self.teachers.append(teacher)
            self._next_id += 1

    def get_daily_contacts(self, person: Person) -> list:
        contacts = set()

        if person.role == 'student':
            contacts.update(self.classes[person.class_id])

            for t in self.teachers:
                if t.is_homeroom and t.class_id == person.class_id:
                    contacts.add(t)

            subject_teachers = [t for t in self.teachers if not t.is_homeroom]
            contacts.update(random.sample(subject_teachers, k=min(3, len(subject_teachers))))

        elif person.role == 'teacher':
            if person.is_homeroom:
                contacts.update(self.classes[person.class_id])

            other_classes = random.sample(
                list(self.classes.values()),
                k=min(3, len(self.classes))
            )
            for cls in other_classes:
                contacts.update(cls)

            other_teachers = [t for t in self.teachers if t.id != person.id]
            contacts.update(random.sample(other_teachers, k=min(3, len(other_teachers))))

        contacts.discard(person)
        return list(contacts)

    def try_infect(self, source: Person, target: Person):
        if not source.is_infectious():
            return

        if not target.can_be_infected():
            return

        beta = virus.infection_probability

        w = Parameters.CONTACT_WEIGHT.value.get(
            (source.role, target.role), 1.0
        )

        s = Parameters.AGE_SUSCEPTIBILITY.value[target.age_group()]
        i = Parameters.ROLE_INFECTIVITY.value[source.role]

        immunity_factor = 1 - (
                target.immunity.antibody_level * 0.7 +
                target.immunity.innate_strength * 0.3
        )

        p = beta * w * s * i * immunity_factor
        p = min(max(p, 0.0), 0.95)

        if random.random() < p:
            target.exposed()

    def step_day(self):
        infected_people = [
            p for p in self.students + self.teachers if p.is_infectious
        ]

        for source in infected_people:
            contacts = self.get_daily_contacts(source)

            for target in contacts:
                self.try_infect(source, target)

        for person in self.students + self.teachers:
            person.update()

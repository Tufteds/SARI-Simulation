# --- Стандартные библиотеки ---
import os, sys
import tkinter as tk
import random
from tkinter import messagebox, scrolledtext, ttk
from collections import defaultdict
from abc import ABC, abstractmethod

# --- Сторонние библиотеки ---
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# Декоратор синглтона
def singleton(cls):
    instances = {}
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return get_instance

# Класс утилит-функций
class Utils():
    @staticmethod
    def resource_path(relative_path):
        """Возвращает абсолютный путь к ресурсу (иконка, файл и т.д.)"""
        try:
            # если это PyInstaller
            base_path = sys._MEIPASS
        except AttributeError:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

# Отдельный класс вируса
@singleton
class Virus():
    def __init__(self):
        self.type = 'ОРВИ'
        self.time_incubation = 2
        self.base_duration = random.randint(5, 7)
        self.infection_probability = 0.1

virus = Virus()

# Класс человека
class Person():
    def __init__(self, immunity):
        self.status = 'healthy'
        self.days_infected = 0
        self.incubation = 0
        self.immunity = immunity
        self.immunity_effects = {'low': 1, 'medium': 0, 'strong': -1}

    # Обновление статуса
    def update_infections(self):
        if self.status == 'exposed':
            self.incubation += 1
            if self.incubation >= virus.time_incubation:
                self.status = 'infected'
        elif self.status == 'infected':
            self.days_infected += 1
            if self.days_infected >= virus.base_duration + self.immunity_effects[self.immunity]:
                self.status = 'cured'

    # Функиця на будущее
    def get_contact(self):
        pass

# Класс популяции людей
class Population():
    def __init__(self, size, infected_count):
        self.people = [Person(random.choice(['low', 'medium', 'strong'])) for _ in range(size)]
        for person in random.sample(self.people, infected_count):
            person.status = 'exposed'

    # Обновление статуса
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
                    if random.random() < virus.infection_probability:
                        target.status = 'exposed'
                        target.incubation = 0
                        new_infections += 1
        return new_infections

    # Группировка людей по статусу
    def group_by_status(self):
        groups = defaultdict(list)
        for person in self.people:
            groups[person.status].append(person)
        return groups

    # Получение статистики за текущий день
    def get_statistics(self):
        return {status: len(group) for status, group in self.group_by_status().items()}

# Класс симуляции
class Simulation():
    def __init__(self, population_size, days, log_callback):
        self.population = Population(population_size, round(population_size*0.05))
        self.days = days
        self.history = {'healthy': [], 'exposed': [], 'infected': [], 'cured': []}
        self.log_callback = log_callback
        self.peak_day = 0
        self.max_infected = 0

    # Вывод логов
    def log_message(self, message):
        self.log_callback(message)

    # Запуск симуляции
    def run(self):
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

            self.log_message(f"--- День {day + 1} ---")
            self.log_message(
                f"Здоровые: {healthy}, Подверженные: {exposed}, Заражённые: {infected}, Вылеченные: {cured}")

            if (infected == 0 and exposed == 0) or healthy == 0:
                self.log_message("Симуляция завершена.")
                break

            new_infected = self.population.update()
            self.log_message(f"Новые заражённые: {new_infected}")

        return self.history

class BaseModel(ABC):
    def __init__(self, population_size, days):
        self.population_size = population_size
        self.days = days
        self.history = {}

    @abstractmethod
    def run(self):
        pass

class AgentBasedModel(BaseModel):
    def run(self):
        pass

class MathematicalModel(BaseModel):
    def run(self):
        pass

# Класс графического интерфейса
class GUI():
    def __init__(self, root):
        self.root = root
        self.font = ('Segoe UI', 13)
        self.graph_canvas = None
        self.build_ui()

    # Построение окна tkninter
    def build_ui(self):
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill='both', expand=True)

        self.left_frame = tk.Frame(self.main_frame)
        self.left_frame.pack(side='left', fill='both', expand=True, padx=10, pady=10)

        self.right_frame = tk.Frame(self.main_frame)
        self.right_frame.pack(side='right', fill='both', expand=True, padx=10, pady=10)

        # Шрифт для всех элементов ввода
        self.font = ('Segoe UI', 13)

        # Поле ввода размера популяции
        tk.Label(self.left_frame, text="Размер популяции:", font=self.font).pack(pady=5)
        self.population_entry = tk.Entry(self.left_frame, font=self.font, width=20)
        self.population_entry.pack(pady=5)

        # Поле ввода количества дней
        tk.Label(self.left_frame, text="Количество дней симуляции:", font=self.font).pack(pady=5)
        self.days_entry = tk.Entry(self.left_frame, font=self.font, width=20)
        self.days_entry.pack(pady=5)

        # Выпадающий список выбора типа модели
        tk.Label(self.left_frame, text="Тип модели:", font=self.font).pack(pady=5)
        self.model_var = tk.StringVar()
        self.model_combobox = ttk.Combobox(
            self.left_frame,
            textvariable=self.model_var,
            state='readonly',  # запрет ручного ввода
            values=['Выберите тип модели', 'Агентная', 'Математическая', 'Гибридная'],
            width=20,  # ширина как у Entry
            font=self.font,
            height=5  # сколько элементов видно при раскрытии
        )
        self.model_combobox.current(0)  # первый элемент по умолчанию
        self.model_combobox.pack(pady=5)

        def remove_placeholder(event):
            current = self.model_var.get()
            if current != "Выберите тип модели":
                # Обновляем список без плейсхолдера
                self.model_combobox['values'] = ['Агентная', 'Математическая', 'Гибридная']

        self.model_combobox.bind("<<ComboboxSelected>>", remove_placeholder)

        # Кнопка запуска
        tk.Button(
            self.left_frame,
            text="🚀 Запустить симуляцию",
            font=self.font,
            command=self.start_simulation
        ).pack(pady=10)

        # Лог
        self.log_output = scrolledtext.ScrolledText(
            self.left_frame, height=20, font=('Consolas', 11)
        )
        self.log_output.pack(pady=10, fill='both', expand=True)

    # Старт симуляции (по кнопке)
    def start_simulation(self):
        try:
            population_size = int(self.population_entry.get().replace('.', ''))
            days = int(self.days_entry.get().replace('.', ''))
            selected_model = self.model_var.get()
            if population_size <= 0 or days <= 0:
                raise ValueError
            if selected_model == "Выберите тип модели":
                messagebox.showwarning("Ошибка", "Пожалуйста, выберите тип модели!")
                return
        except ValueError:
            messagebox.showerror("Ошибка", "Пожалуйста, введите корректные значения.")
            return

        self.log_output.delete(1.0, tk.END)

        self.sim = Simulation(population_size, days, self.log_message)
        self.sim.run()
        self.draw_graph(self.sim.history)

    # Вывод в GUI
    def log_message(self, msg):
        self.log_output.insert(tk.END, msg + '\n')
        self.log_output.see(tk.END)

    # Отрисовка графика
    def draw_graph(self, history):
        if self.graph_canvas:
            self.graph_canvas.get_tk_widget().destroy()

        fig = Figure(figsize=(6, 4), dpi=100)
        plot = fig.add_subplot(111)
        plot.plot(history['healthy'], label='Здоровые', color='green')
        plot.plot(history['exposed'], label='Подверженные', color='orange')
        plot.plot(history['infected'], label='Заражённые', color='red')
        plot.plot(history['cured'], label='Вылеченные', color='blue')
        plot.legend()
        plot.grid(True, linestyle='--', alpha=0.5)

        plot.plot(self.sim.peak_day, self.sim.max_infected, 'ro')  # 'ro' — красная точка
        plot.text(self.sim.peak_day, self.sim.max_infected, f'Пик болезни\nДень {self.sim.peak_day + 1}',
                  fontsize=10, color='black', ha='center', va='bottom')

        plot.set_xlabel('Дни', color='black')
        plot.set_ylabel('Люди', color='black')
        plot.set_title('ОРВИ Симуляция', color='black')
        plot.tick_params(colors='black')
        plot.grid(True, linestyle='--', alpha=0.5)
        plot.legend()

        self.graph_canvas = FigureCanvasTkAgg(fig, master=self.right_frame)
        self.graph_canvas.draw()
        self.graph_canvas.get_tk_widget().pack(fill='both', expand=True)

# Запуск программы
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Симуляция распространения ОРВИ")
    root.geometry("1500x600")
    root.iconbitmap(Utils.resource_path("icons/virus.ico"))
    gui = GUI(root)
    root.mainloop()

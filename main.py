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
        self.infection_probability = 0.2

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

class BaseModel(ABC):
    def __init__(self, population_size, days):
        self.population_size = population_size
        self.days = days
        self.history = {}

    @abstractmethod
    def run(self,log_callback):
        pass

class AgentBasedModel(BaseModel):
    def __init__(self, population_size, days):
        super().__init__(population_size, days)
        self.population = Population(population_size, round(population_size * 0.05))
        self.history = {'healthy': [], 'exposed': [], 'infected': [], 'cured': []}
        self.peak_day = 0
        self.max_infected = 0

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
                f"Здоровые: {healthy}, Подверженные: {exposed}, Заражённые: {infected}, Вылеченные: {cured}")

            if (infected == 0 and exposed == 0) or healthy == 0:
                log_callback("Симуляция завершена.")
                break

            new_infected = self.population.update()
            log_callback(f"Новые заражённые: {new_infected}")

        return self.history

class MathematicalModel(BaseModel):
    def __init__(self, population_size, days):
        super().__init__(population_size, days)
        self.population = Population(population_size, round(population_size * 0.05))
        self.history = {'healthy': [], 'exposed': [], 'infected': [], 'cured': []}
        self.peak_day = 0
        self.max_infected = 0

        # Параметры SEIR
        self.beta = 0.3
        self.sigma = 1/2
        self.gamma = 1/6

        # Начальные состояния
        initial_infected = round(population_size * 0.05)
        self.S = population_size - initial_infected
        self.E = initial_infected
        self.I = 0
        self.R = 0

        self.history = {'healthy': [], 'exposed': [], 'infected': [], 'cured': []}

    def run(self, log_callback):
        for day in range(self.days):
            new_exposed = self.beta * self.S * self.I / self.population_size
            new_infected = self.sigma * self.E
            new_recovered = self.gamma * self.I

            if self.I < 0.5 and self.E < 0.5:
                log_callback(f"Эпидемия завершилась на дне {day}.")
                break

            self.S -= new_exposed
            self.E += new_exposed - new_infected
            self.I += new_infected - new_recovered
            self.R += new_recovered

            current_S = max(0, int(self.S))
            current_E = max(0, int(self.E))
            current_I = max(0, int(self.I))
            current_R = max(0, int(self.R))

            self.history['healthy'].append(current_S)
            self.history['exposed'].append(current_E)
            self.history['infected'].append(current_I)
            self.history['cured'].append(current_R)

            if current_I > self.max_infected:
                self.max_infected = current_I
                self.peak_day = day

            # Лог
            log_callback(f"--- День {day+1} ---")
            log_callback(
                f"Здоровые: {int(self.S)}, Подверженные: {int(self.E)}, Заражённые: {int(self.I)}, Вылеченные: {int(self.R)}"
            )

        return self.history

class HybrydModel(BaseModel):
    def run(self, log_callback):
        pass

# Класс графического интерфейса
class GUI():
    def __init__(self, root):
        self.root = root
        self.font = ('Segoe UI', 13)
        self.graph_canvas = None
        self.build_ui()

    def open_advanced_settings(self):
        top = tk.Toplevel(self.root)
        top.title("Расширенные настройки")
        top.geometry("400x300")
        tk.Label(top, text="Здесь будут расширенные настройки", font=self.font).pack(pady=20)
        tk.Button(top, text="Закрыть", command=top.destroy).pack(pady=20)

    def build_ui(self):
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill='both', expand=True)

        # Левый фрейм для управления
        self.left_frame = tk.Frame(self.main_frame)
        self.left_frame.pack(side='left', fill='both', expand=True, padx=10, pady=10)

        # Правый фрейм для графика
        self.right_frame = tk.Frame(self.main_frame)
        self.right_frame.pack(side='right', fill='both', expand=True, padx=10, pady=10)

        # ---------- Заголовок ----------
        tk.Label(
            self.left_frame,
            text="Основные параметры",
            font=('Segoe UI', 16, 'bold'),
            fg='black'
        ).grid(row=0, column=0, columnspan=4, pady=(0, 10))

        # ---------- Матрица ввода ----------
        # Размер популяции
        tk.Label(self.left_frame, text="Размер популяции:", font=self.font).grid(row=1, column=0, sticky='w', padx=5,
                                                                                 pady=5)
        self.population_entry = tk.Entry(self.left_frame, font=self.font, width=20)
        self.population_entry.grid(row=1, column=1, padx=5, pady=5, sticky='w')

        # Тип модели
        tk.Label(self.left_frame, text="Тип модели:", font=self.font).grid(row=1, column=2, sticky='w', padx=5, pady=5)
        self.model_var = tk.StringVar()
        self.model_combobox = ttk.Combobox(
            self.left_frame,
            textvariable=self.model_var,
            state='readonly',
            values=['Выберите тип модели', 'Агентная', 'Математическая'],
            width=20,
            font=self.font
        )
        self.model_combobox.current(0)
        self.model_combobox.grid(row=1, column=3, padx=(0, 5), pady=5, sticky='w')

        # Количество дней
        tk.Label(self.left_frame, text="Количество дней:", font=self.font).grid(row=2, column=0, sticky='w', padx=5,
                                                                                pady=5)
        self.days_entry = tk.Entry(self.left_frame, font=self.font, width=20)
        self.days_entry.grid(row=2, column=1, padx=5, pady=5, sticky='w')

        # Тип графика
        tk.Label(self.left_frame, text="Тип графика:", font=self.font).grid(row=2, column=2, sticky='w', padx=5, pady=5)
        self.chart_type_var = tk.StringVar()
        self.chart_type_combobox = ttk.Combobox(
            self.left_frame,
            textvariable=self.chart_type_var,
            state='readonly',
            values=['Линейный', 'Круговой'],
            width=20,
            font=self.font
        )
        self.chart_type_combobox.current(0)
        self.chart_type_combobox.grid(row=2, column=3, padx=(0, 5), pady=5, sticky='w')

        # ---------- Кнопки ----------
        tk.Button(
            self.left_frame,
            text="🚀 Запустить симуляцию",
            font=self.font,
            command=self.start_simulation
        ).grid(row=3, column=1, pady=10, padx=(0, 10))

        tk.Button(
            self.left_frame,
            text="⚙ Расширенные настройки",
            font=self.font,
            command=self.open_advanced_settings
        ).grid(row=3, column=2, pady=10, padx=(10, 0))

        # ---------- Лог ----------
        self.log_output = scrolledtext.ScrolledText(
            self.left_frame, height=20, font=('Consolas', 11)
        )
        self.log_output.grid(row=4, column=0, columnspan=4, pady=10, sticky='nsew')

        # Растяжение левого фрейма
        self.left_frame.grid_rowconfigure(4, weight=1)
        self.left_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # ---------- Заглушка графика ----------
        self.graph_placeholder = tk.Frame(
            self.right_frame,
            width=625,
            height=600,
            bg='white',
            relief='ridge',
            bd=2
        )
        self.graph_placeholder.pack(padx=10, pady=10)
        self.graph_placeholder.pack_propagate(False)

        # Текст по центру заглушки
        label = tk.Label(
            self.graph_placeholder,
            text="Место для графика",
            font=('Segoe UI', 16),
            fg='gray',
            bg='white'
        )
        label.place(relx=0.5, rely=0.5, anchor='center')

    # ---------- Старт симуляции ----------
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

        # Выбор модели
        if selected_model == 'Агентная':
            self.sim = AgentBasedModel(population_size, days)
        elif selected_model == 'Математическая':
            self.sim = MathematicalModel(population_size, days)
        else:
            messagebox.showerror("Ошибка", "Выбранный тип модели не поддерживается!")
            return

        # Запуск модели
        self.sim.run(self.log_message)

        # Отрисовка графика
        self.draw_graph(self.sim.history)

    # ---------- Вывод в лог ----------
    def log_message(self, msg):
        self.log_output.insert(tk.END, msg + '\n')
        self.log_output.see(tk.END)

    # ---------- Отрисовка графика ----------
    def draw_graph(self, history):
        if hasattr(self, 'graph_placeholder') and self.graph_placeholder:
            self.graph_placeholder.pack_forget()
            self.graph_placeholder = None

        if self.graph_canvas:
            self.graph_canvas.get_tk_widget().destroy()

        chart_type = self.chart_type_var.get()
        fig = Figure(figsize=(6, 4), dpi=100)

        if chart_type == 'Линейный':
            plot = fig.add_subplot(111)
            plot.plot(history['healthy'], label='Здоровые', color='green')
            plot.plot(history['exposed'], label='Подверженные', color='orange')
            plot.plot(history['infected'], label='Заражённые', color='red')
            plot.plot(history['cured'], label='Вылеченные', color='blue')
            plot.set_xlabel('Дни')
            plot.set_ylabel('Люди')
            plot.set_title('ОРВИ Симуляция')
            plot.legend()
            plot.grid(True, linestyle='--', alpha=0.5)

            if hasattr(self.sim, 'peak_day') and hasattr(self.sim, 'max_infected'):
                plot.scatter(self.sim.peak_day, self.sim.max_infected, color='red', s=100, zorder=5)
                plot.text(self.sim.peak_day, self.sim.max_infected, f'день {self.sim.peak_day}', color='red',
                          fontsize=10,
                          ha='left', va='bottom')

        elif chart_type == 'Круговой':
            plot = fig.add_subplot(111)
            sizes = [
                sum(history['healthy']) / len(history['healthy']),
                sum(history['exposed']) / len(history['exposed']),
                sum(history['infected']) / len(history['infected']),
                sum(history['cured']) / len(history['cured']),
            ]
            labels = ['Здоровые', 'Подверженные', 'Заражённые', 'Вылеченные']
            plot.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90,
                     colors=['green', 'orange', 'red', 'blue'])
            plot.set_title(f'Статистика симуляции')

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

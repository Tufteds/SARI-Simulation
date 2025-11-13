# --- Стандартные библиотеки ---
import os, sys
import tkinter as tk
import random
from tkinter import messagebox, scrolledtext
from collections import defaultdict

# --- Сторонние библиотеки ---
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

def singleton(cls):
    instances = {}
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return get_instance

@singleton
class Virus():
    def __init__(self):
        self.type = 'ОРВИ'
        self.time_incubation = 2
        self.base_duration = random.randint(5, 6)
        self.infection_probability = 0.1

virus = Virus()

class Person():
    def __init__(self, immunity):
        self.status = 'healthy'
        self.days_infected = 0
        self.incubation = 0
        self.immunity = immunity
        self.immunity_effects = {'low': 1, 'medium': 0, 'strong': -1}

    def update_infections(self):
        if self.status == 'exposed':
            self.incubation += 1
            if self.incubation >= virus.time_incubation:
                self.status = 'infected'
        elif self.status == 'infected':
            self.days_infected += 1
            if self.days_infected >= virus.base_duration + self.immunity_effects[self.immunity]:
                self.status = 'cured'

    def get_contact(self):
        pass

class Population():
    def __init__(self, size, infected_count):
        self.people = [Person(random.choice(['low', 'medium', 'strong'])) for _ in range(size)]
        for person in random.sample(self.people, infected_count):
            person.status = 'exposed'

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
    def group_by_status(self):
        groups = defaultdict(list)
        for person in self.people:
            groups[person.status].append(person)
        return groups

    def get_statistics(self):
        return {status: len(group) for status, group in self.group_by_status().items()}

class Simulation():
    def __init__(self, population_size, days, log_callback):
        self.population = Population(population_size, round(population_size*0.05))
        self.days = days
        self.history = {'healthy': [], 'exposed': [], 'infected': [], 'cured': []}
        self.log_callback = log_callback

    def log_message(self, message):
        self.log_callback(message)

    def run(self):
        for day in range(self.days):
            groups = self.population.group_by_status()
            healthy = len(groups.get('healthy', []))
            exposed = len(groups.get('exposed', []))
            infected = len(groups.get('infected', []))
            cured = len(groups.get('cured', []))

            # сохраняем в history всегда в одном порядке и с 0 по-умолчанию
            self.history['healthy'].append(healthy)
            self.history['exposed'].append(exposed)
            self.history['infected'].append(infected)
            self.history['cured'].append(cured)

            # Логи в требуемом формате
            self.log_message(f"--- День {day + 1} ---")
            self.log_message(
                f"Здоровые: {healthy}, Подверженные: {exposed}, Заражённые: {infected}, Вылеченные: {cured}")

            # если эпидемия кончилась — останавливаем
            if (infected == 0 and exposed == 0) or healthy == 0:
                self.log_message("Симуляция завершена.")
                break

            # обновляем популяцию — получаем число новых заражённых
            new_infected = self.population.update()
            self.log_message(f"Новые заражённые: {new_infected}")

        return self.history

class GUI():
    def __init__(self, root):
        self.root = root
        self.font = ('Segoe UI', 13)
        self.graph_canvas = None
        self.build_ui()


    def build_ui(self):
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill='both', expand=True)

        self.left_frame = tk.Frame(self.main_frame)
        self.left_frame.pack(side='left', fill='both', expand=True, padx=10, pady=10)

        self.right_frame = tk.Frame(self.main_frame)
        self.right_frame.pack(side='right', fill='both', expand=True, padx=10, pady=10)

        tk.Label(self.left_frame, text="Размер популяции:", font=self.font).pack(pady=5)
        self.population_entry = tk.Entry(self.left_frame, font=self.font)
        self.population_entry.pack(pady=5)

        tk.Label(self.left_frame, text="Количество дней симуляции:", font=self.font).pack(pady=5)
        self.days_entry = tk.Entry(self.left_frame, font=self.font)
        self.days_entry.pack(pady=5)

        tk.Button(self.left_frame, text="🚀 Запустить симуляцию", font=self.font, command=self.start_simulation).pack(
            pady=10)

        self.log_output = scrolledtext.ScrolledText(self.left_frame, height=20, font=('Consolas', 11))
        self.log_output.pack(pady=10, fill='both', expand=True)

    def start_simulation(self):
        try:
            population_size = int(self.population_entry.get().replace('.', ''))
            days = int(self.days_entry.get().replace('.', ''))
            if population_size <= 0 or days <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Ошибка", "Пожалуйста, введите корректные значения.")
            return

        # очищаем лог перед новой симуляцией
        self.log_output.delete(1.0, tk.END)

        # запускаем симуляцию и отрисовываем график
        sim = Simulation(population_size, days, self.log_message)
        sim.run()
        self.draw_graph(sim.history)
    def log_message(self, msg):
        self.log_output.insert(tk.END, msg + '\n')
        self.log_output.see(tk.END)

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

        self.graph_canvas = FigureCanvasTkAgg(fig, master=self.right_frame)
        self.graph_canvas.draw()
        self.graph_canvas.get_tk_widget().pack(fill='both', expand=True)

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Симуляция распространения ОРВИ")
    root.geometry("1500x600")
    # root.iconbitmap(resource_path("virus.ico"))
    gui = GUI(root)
    root.mainloop()

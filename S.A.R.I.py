# --- Стандартные библиотеки ---
import os, sys
import tkinter as tk
import random
from tkinter import messagebox, scrolledtext
from collections import defaultdict

# --- Сторонние библиотеки ---
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

class Person():
    def __init__(self, immunity):
        self.status = 'healthy'
        self.days_infected = 0
        self.incubation = 0
        self.immunity = immunity

    def update_infections(self):
        if self.status == 'exposed':
            self.incubation += 1
            if self.incubation >= time_incubation:
                self.status = 'infected'
        elif self.status == 'infected':
            self.days_infected += 1
            if self.days_infected >= base_duration + immunity_effects[self.immunity]:
                self.status = 'cured'

    def get_contact(self):
        pass

class Population():
    def __init__(self, size, infected_count):
        self.people = [Person(random.choice(power_immunity) for _ in range(size))]
        for person in random.sample(self.people, infected_count):
            person.status = 'exposed'

    def update(self):
        pass

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
            stats = self.population.get_statistics()
            for status, count in stats.items():
                self.history[status].append(count)
            self.log_message(f"День {day + 1}: {stats}")
            self.population.update()
        return self.history

class GUI():
    def __init__(self, root):
        self.root = root

    def build_ui(self):
        self.left_frame = tk.Frame(self.root)
        self.left_frame.pack(side='left', fill='both', expand=True, padx=10, pady=10)

        self.right_frame = tk.Frame(self.root)
        self.right_frame.pack(side='right', fill='both', expand=True, padx=10, pady=10)

        self.log_output = scrolledtext.ScrolledText(self.left_frame, height=20)
        self.log_output.pack(fill='both', expand=True, pady=10)

        self.population_entry = tk.Entry(self.left_frame)
        self.population_entry.pack(pady=5)
        self.days_entry = tk.Entry(self.left_frame)
        self.days_entry.pack(pady=5)

        tk.Button(
            self.left_frame, text="🚀 Запустить", command=self.start_simulation
        ).pack(pady=10)

    def start_simulation(self):
        pop_size = int(self.population_entry.get())
        days = int(self.days_entry.get())
        sim = Simulation(pop_size, days, self.log_message)
        sim.run()
        self.draw_graph(sim.history)

    def log_message(self, msg):
        self.log_output.insert(tk.END, msg + '\n')
        self.log_output.see(tk.END)

    def draw_graph(self, history):
        fig = Figure(figsize=(6, 4), dpi=100)
        plot = fig.add_subplot(111)
        plot.plot(history['healthy'], label='Здоровые', color='green')
        plot.plot(history['exposed'], label='Подверженные', color='orange')
        plot.plot(history['infected'], label='Заражённые', color='red')
        plot.plot(history['cured'], label='Вылеченные', color='blue')
        plot.legend()
        plot.grid(True, linestyle='--', alpha=0.5)

        canvas = FigureCanvasTkAgg(fig, master=self.right_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)

if __name__ == "__main__":
    root = tk.Tk()
    gui = GUI(root)
    root.mainloop()

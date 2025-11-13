# --- Стандартные библиотеки ---
import os, sys
import tkinter as tk
import random
from tkinter import messagebox, scrolledtext
from collections import defaultdict

# --- Сторонние библиотеки ---
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# Параметры
infection_probability = 0.1
base_duration = random.randint(5, 6)
power_immunity = ['low', 'medium', 'strong']
immunity_effects = {'low': 1, 'medium': 0, 'strong': -1}
time_incubation = 2

# Глобальные
graph_canvas = None
log_output = None

def resource_path(relative_path):
    """Возвращает путь к ресурсу, работает и в .exe, и при обычном запуске"""
    try:
        base_path = sys._MEIPASS  # если это PyInstaller
    except AttributeError:
        base_path = os.path.abspath(".")  # при обычном запуске
    return os.path.join(base_path, relative_path)

# Группировка
def group_by_status(population):
    groups = defaultdict(list)
    for person in population:
        groups[person['status']].append(person)
    return groups

# Инициализация
def initialize_population(size, infected_count):
    population = [{'status': 'healthy', 'days_infected': 0, 'incubation': 0,
                   'immunity': random.choice(power_immunity)} for _ in range(size)]
    for person in random.sample(population, infected_count):
        person['status'] = 'exposed'
    return population

# Обновление инфекции
def update_infections(groups):
    new_infections = 0
    for person in groups['infected']:
        person['days_infected'] += 1
        if person['days_infected'] >= base_duration + immunity_effects[person['immunity']]:
            person['status'] = 'cured'

    for person in groups['exposed']:
        person['incubation'] += 1
        if person['incubation'] >= time_incubation:
            person['status'] = 'infected'

    infected_group = groups['infected']
    healthy_group = groups['healthy']

    if infected_group and healthy_group:
        random.shuffle(healthy_group)
        contact_index = 0
        for inf in infected_group:
            for _ in range(2):
                if contact_index >= len(healthy_group):
                    break
                target = healthy_group[contact_index]
                contact_index += 1
                adj_prob = infection_probability + \
                    (0.03 if inf['immunity'] == 'low' else -0.03 if inf['immunity'] == 'strong' else 0)
                if random.random() < adj_prob:
                    target['status'] = 'exposed'
                    target['incubation'] = 0
                    new_infections += 1
    return new_infections

def log_message(message):
    log_output.insert(tk.END, message + '\n')
    log_output.see(tk.END)

def simulate(population_size, days):
    global graph_canvas

    initial_infected = round(population_size * 0.05)
    population = initialize_population(population_size, initial_infected)
    history = {'healthy': [], 'exposed': [], 'infected': [], 'cured': []}

    max_infected = 0
    peak_day = 0

    for day in range(days):
        groups = group_by_status(population)
        healthy = len(groups['healthy'])
        exposed = len(groups['exposed'])
        infected = len(groups['infected'])
        cured = len(groups['cured'])

        history['healthy'].append(healthy)
        history['exposed'].append(exposed)
        history['infected'].append(infected)
        history['cured'].append(cured)

        # Определяем пик болезни
        if infected > max_infected:
            max_infected = infected
            peak_day = day

        log_message(f"--- День {day+1} ---")
        log_message(f"Здоровые: {healthy}, Подверженные: {exposed}, Заражённые: {infected}, Вылеченные: {cured}")

        if (infected == 0 and exposed == 0) or healthy == 0:
            log_message("Симуляция завершена.")
            break

        new_infected = update_infections(groups)
        log_message(f"Новые заражённые: {new_infected}")

    if graph_canvas:
        graph_canvas.get_tk_widget().destroy()

    fig = Figure(figsize=(6, 4), dpi=100, facecolor='white')
    plot = fig.add_subplot(111)
    plot.set_facecolor('white')

    plot.plot(history['healthy'], label='Здоровые', color='green', linewidth=2)
    plot.plot(history['exposed'], label='Подверженные', color='orange', linewidth=2)
    plot.plot(history['infected'], label='Заражённые', color='red', linewidth=2)
    plot.plot(history['cured'], label='Вылеченные', color='blue', linewidth=2)

    # Добавление точки на графике для пика болезни
    plot.plot(peak_day, max_infected, 'ro')  # 'ro' — красная точка
    plot.text(peak_day, max_infected, f'Пик болезни\nДень {peak_day + 1}', 
              fontsize=10, color='black', ha='center', va='bottom')

    plot.set_xlabel('Дни', color='black')
    plot.set_ylabel('Люди', color='black')
    plot.set_title('ОРВИ Симуляция', color='black')
    plot.tick_params(colors='black')
    plot.grid(True, linestyle='--', alpha=0.5)
    plot.legend()

    graph_canvas = FigureCanvasTkAgg(fig, master=right_frame)
    graph_canvas.draw()
    graph_canvas.get_tk_widget().pack(fill='both', expand=True)


def start_simulation():
    log_output.delete(1.0, tk.END)
    try:
        population_size = int(population_entry.get().replace('.', ''))
        days = int(days_entry.get().replace('.', ''))
        if population_size <= 0 or days <= 0:
            raise ValueError
        simulate(population_size, days)
    except ValueError:
        messagebox.showerror("Ошибка", "Пожалуйста, введите корректные значения.")

# Интерфейс
root = tk.Tk()
root.title("Симуляция распространения ОРВИ")
root.geometry("1500x600")
root.iconbitmap(resource_path("virus.ico"))
font = ('Segoe UI', 13)

# Макет
main_frame = tk.Frame(root)
main_frame.pack(fill='both', expand=True)

left_frame = tk.Frame(main_frame)
left_frame.pack(side='left', fill='both', expand=True, padx=10, pady=10)

right_frame = tk.Frame(main_frame)
right_frame.pack(side='right', fill='both', expand=True, padx=10, pady=10)

# Элементы слева
tk.Label(left_frame, text="Размер популяции:", font=font).pack(pady=5)
population_entry = tk.Entry(left_frame, font=font)
population_entry.pack(pady=5)

tk.Label(left_frame, text="Количество дней симуляции:", font=font).pack(pady=5)
days_entry = tk.Entry(left_frame, font=font)
days_entry.pack(pady=5)

tk.Button(left_frame, text="🚀 Запустить симуляцию", font=font, command=start_simulation).pack(pady=10)

log_output = scrolledtext.ScrolledText(left_frame, height=20, font=('Consolas', 11))
log_output.pack(pady=10, fill='both', expand=True)

root.mainloop()

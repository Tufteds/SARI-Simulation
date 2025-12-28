# Начальные модули
import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.animation import FuncAnimation
from models import AgentBasedModel, MathematicalModel, HybrydModel

# Графический интерфейс
class GUI():
    def __init__(self, root):
        self.root = root
        self.animate_graph = tk.BooleanVar(value=True)
        self.font = ('Segoe UI', 13)
        self.graph_canvas = None
        self.build_ui()

    # Расширенные настройки
    def open_advanced_settings(self):
        top = tk.Toplevel(self.root)
        top.title("Расширенные настройки")
        top.geometry("400x300")

        tk.Label(top, text="Расширенные настройки", font=self.font).pack(pady=20)
        tk.Checkbutton(
            top,
            text="Анимировать график",
            variable=self.animate_graph,
            font=self.font
        ).pack(pady=10)

        tk.Button(top, text="Закрыть", command=top.destroy).pack(pady=20)

    # Построение окна
    def build_ui(self):
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill='both', expand=True)

        # Левый фрейм для управления
        self.left_frame = tk.Frame(self.main_frame)
        self.left_frame.pack(side='left', fill='both', expand=True, padx=10, pady=10)

        # Правый фрейм для графика
        self.right_frame = tk.Frame(self.main_frame)
        self.right_frame.pack(side='right', fill='both', expand=True, padx=10, pady=10)

        # Заголовок
        tk.Label(
            self.left_frame,
            text="Основные параметры",
            font=('Segoe UI', 16, 'bold'),
            fg='black'
        ).grid(row=0, column=0, columnspan=4, pady=(0, 10))

        # Матрица ввода
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
            values=['Линейный', 'Круговой', 'Столбчатый'],
            width=20,
            font=self.font
        )
        self.chart_type_combobox.current(0)
        self.chart_type_combobox.grid(row=2, column=3, padx=(0, 5), pady=5, sticky='w')

        # Кнопки
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

        # Лог
        self.log_output = scrolledtext.ScrolledText(
            self.left_frame, height=20, font=('Consolas', 11)
        )
        self.log_output.grid(row=4, column=0, columnspan=4, pady=10, sticky='nsew')

        # Растяжение левого фрейма
        self.left_frame.grid_rowconfigure(4, weight=1)
        self.left_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Заглушка для графика
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

        # Текст в заглушке
        label = tk.Label(
            self.graph_placeholder,
            text="Место для графика",
            font=('Segoe UI', 16),
            fg='gray',
            bg='white'
        )
        label.place(relx=0.5, rely=0.5, anchor='center')

    # Старт симуляции
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

        if hasattr(self.sim, 'peak_day'):
            self.peak_day = self.sim.peak_day
            self.log_message(f"День пика заражений: {self.peak_day}")

        # Отрисовка графика
        self.draw_graph(self.sim.history)

    # Вывод в лог
    def log_message(self, msg):
        self.log_output.insert(tk.END, msg + '\n')
        self.log_output.see(tk.END)

    # Отрисовка графика
    def draw_graph(self, history):
        if hasattr(self, 'graph_placeholder') and self.graph_placeholder:
            self.graph_placeholder.pack_forget()
            self.graph_placeholder = None

        if self.graph_canvas:
            self.graph_canvas.get_tk_widget().destroy()

        chart_type = self.chart_type_var.get()
        fig = Figure(figsize=(6, 4), dpi=100)
        plot = fig.add_subplot(111)

        # Подготовка канвы
        self.graph_canvas = FigureCanvasTkAgg(fig, master=self.right_frame)
        canvas_widget = self.graph_canvas.get_tk_widget()
        canvas_widget.pack(fill='both', expand=True)

        # Берём данные
        days = list(range(len(history['infected'])))
        healthy = history['healthy']
        vaccinated = history['vaccinated']
        exposed = history['exposed']
        infected = history['infected']
        cured = history['cured']

        # Линейный график с анимацией
        if chart_type == "Линейный":
            plot.set_xlim(0, len(days))
            plot.set_ylim(0, max(healthy + vaccinated + exposed + infected + cured))
            plot.set_xlabel('Дни')
            plot.set_ylabel('Люди')
            plot.set_title('Симуляция')
            plot.grid(True, linestyle='--', alpha=0.5)

            peak_day_idx = self.peak_day - 1 if hasattr(self, 'peak_day') else None
            if peak_day_idx is not None:
                peak_value = infected[peak_day_idx]
                plot.plot(peak_day_idx, peak_value, 'ro', markersize=8, label='Пик заражений')

            line_h, = plot.plot([], [], color='green', label='Здоровые')
            line_v, = plot.plot([], [], color='purple', label='Вакцинированные')
            line_e, = plot.plot([], [], color='orange', label='Подверженные')
            line_i, = plot.plot([], [], color='red', label='Заражённые')
            line_c, = plot.plot([], [], color='blue', label='Вылеченные')

            plot.legend()


            if self.animate_graph.get():  # <<< проверка галочки
                # Обновление кадров
                def update(frame):
                    line_h.set_data(days[:frame], healthy[:frame])
                    line_v.set_data(days[:frame], vaccinated[:frame])
                    line_e.set_data(days[:frame], exposed[:frame])
                    line_i.set_data(days[:frame], infected[:frame])
                    line_c.set_data(days[:frame], cured[:frame])

                    return line_h, line_v, line_e, line_i, line_c

                # Запуск анимации
                self.animation = FuncAnimation(
                    fig,
                    update,
                    frames=len(days) + 1,
                    interval=40,
                    blit=True,
                    repeat=False
                )

                self.graph_canvas.draw()
                return
            else:
                line_h.set_data(days, healthy)
                line_v.set_data(days, vaccinated)
                line_e.set_data(days, exposed)
                line_i.set_data(days, infected)
                line_c.set_data(days, cured)

                self.graph_canvas.draw()
                return
        # Круговая диаграмма
        elif chart_type == "Круговой":
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

        # Столбчатая диаграмма
        elif chart_type == "Столбчатый":
            days_idx = list(range(1, len(healthy) + 1))

            plot.bar(days_idx, healthy, label='Здоровые', color='green')
            plot.bar(days_idx, exposed, bottom=healthy, label='Подверженные', color='orange')
            plot.bar(days_idx, infected,
                     bottom=[healthy[i] + exposed[i] for i in range(len(days_idx))],
                     label='Заражённые', color='red')
            plot.bar(days_idx, cured,
                     bottom=[healthy[i] + exposed[i] + infected[i] for i in range(len(days_idx))],
                     label='Вылеченные', color='blue')

            plot.legend()
            plot.set_xlabel("Дни")
            plot.set_ylabel("Количество людей")
            plot.set_title("Столбчатая диаграмма")
            plot.grid(axis='y', linestyle='--', alpha=0.5)

        self.graph_canvas.draw()
import random
from models import MathematicalModel

class SimpleCalibrator:
    """Калибратор для школьной эпидемической модели (SEIRS)"""

    def __init__(self):
        self.real_data = [51, 68, 83, 87, 86]
        self.population = 831
        self.vaccinated = 406
        self.model = MathematicalModel(self.population, 5)

        print("=" * 50)
        print("КАЛИБРОВКА ШКОЛЬНОЙ ЭПИДЕМИЧЕСКОЙ МОДЕЛИ")
        print("=" * 50)
        print(f"Всего в школе: {self.population} человек")
        print(f"Вакцинированы: {self.vaccinated} ({self.vaccinated / self.population * 100:.1f}%)")
        print(f"Реальные случаи (5 дней): {self.real_data}")
        print(f"Всего случаев: {sum(self.real_data)}")
        print("=" * 50)

    def compare(self, model_data):
        """Сравнение модели с реальными данными"""
        total_error = 0

        print("\n" + "=" * 40)
        print("СРАВНЕНИЕ С РЕАЛЬНЫМИ ДАННЫМИ:")
        print("=" * 40)

        for day in range(5):
            real = self.real_data[day]
            model = model_data[day]
            error = real - model
            abs_error = abs(error)
            total_error += abs_error
            bar = "█" * max(0, model // 5)
            print(f"День {day+1}: Реальные {real:3d} | Модель {model:3d} | Ошибка: {error:+3d} | {bar}")

        avg_error = total_error / 5
        print("=" * 40)
        print(f"Средняя ошибка: {avg_error:.1f} случаев в день")

        if avg_error < 5:
            rating = "🔥 ОТЛИЧНО! Модель совпадает с реальностью"
        elif avg_error < 10:
            rating = "✅ ХОРОШО: Модель реалистична"
        elif avg_error < 20:
            rating = "⚠️ НОРМАЛЬНО: Нужно подстроить параметры"
        else:
            rating = "❌ ПЛОХО: Модель сильно отличается от реальности"

        print(f"Оценка модели: {rating}")
        return avg_error

    def run_model(self, beta=None, omega_v=None):
        """
        Запуск SEIRS-модели:
        - вывод в консоль всей статистики (как в оригинале),
        - сбор новых заражений в список для сравнения с реальными данными.
        """

        daily_cases = []

        # Устанавливаем параметры модели, если заданы
        if beta is not None:
            self.model.beta = beta
        if omega_v is not None:
            self.model.omega_v = omega_v

        # callback для вывода и сбора новых заражений
        def log_callback(msg):
            # Выводим в консоль
            print(msg)
            # Сохраняем новые заражения, используя float для точности
            if msg.startswith("Новые заражённые:"):
                # Берём значение из строки, но округляем только для консоли,
                # а в список добавляем float, чтобы не терять точность
                value = float(msg.split(":")[1].strip())
                daily_cases.append(value)

        # Запуск модели
        self.model.run(log_callback)

        # Для сравнения с реальными данными можно округлять здесь
        daily_cases_rounded = [int(round(x)) for x in daily_cases]

        return daily_cases_rounded

    def interactive_tuning(self):
        """Интерактивная настройка параметров"""
        print("\n" + "=" * 50)
        print("ИНТЕРАКТИВНАЯ НАСТРОЙКА ПАРАМЕТРОВ")
        print("=" * 50)
        print("Изменяйте параметры, чтобы модель лучше соответствовала реальным данным.")
        print("Реальные данные: [51, 68, 83, 87, 86]\n")

        current_infection = self.model.beta
        current_vaccine_eff = self.model.epsilon

        while True:
            print(f"\nТекущие параметры:")
            print(f"  Вероятность заражения: {current_infection}")
            print(f"  Эффективность вакцины: {current_vaccine_eff}")

            model_results = self.run_model(current_infection, current_vaccine_eff)
            self.compare(model_results)

            print("\nВыберите действие:")
            print("1. Увеличить вероятность заражения")
            print("2. Уменьшить вероятность заражения")
            print("3. Увеличить эффективность вакцины")
            print("4. Уменьшить эффективность вакцины")
            print("5. Ввести свои значения")
            print("6. Выйти")

            choice = input("Ваш выбор (1-6): ")

            if choice == "1":
                current_infection = min(0.99, current_infection + 0.02)
            elif choice == "2":
                current_infection = max(0.01, current_infection - 0.02)
            elif choice == "3":
                current_vaccine_eff = min(0.95, current_vaccine_eff + 0.05)
            elif choice == "4":
                current_vaccine_eff = max(0.05, current_vaccine_eff - 0.05)
            elif choice == "5":
                try:
                    current_infection = float(input("Новая вероятность заражения (0.01-0.99): "))
                    current_vaccine_eff = float(input("Новая эффективность вакцины (0.0-1.0): "))
                except:
                    print("Неверный ввод!")
            elif choice == "6":
                print("\nФинальные параметры:")
                print(f"  Вероятность заражения: {current_infection}")
                print(f"  Эффективность вакцины: {current_vaccine_eff}")
                break
            else:
                print("Неверный выбор!")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("SCHOOL EPIDEMIC MODEL CALIBRATION TOOL")
    print("=" * 60)

    # Option 1: Use the simple interactive tuner
    print("\nOption 1: Simple interactive tuning")
    calibrator = SimpleCalibrator()
    calibrator.interactive_tuning()

    # Option 2: Use with your actual model (when ready)
    print("\n" + "=" * 60)
    print("\nOption 2: Calibrate your actual model")
    print("=" * 60)

    wrapper = SimpleCalibrator()

    # Step 1: You need to implement run_your_model_with_params()
    # Step 2: Then uncomment this:
    # best_params = wrapper.calibrate()

    print("\nTo use with YOUR model:")
    print("1. Implement run_your_model_with_params() method")
    print("2. It should take infection_rate and vaccine_effectiveness")
    print("3. Return list of 5 numbers (daily new cases)")
    print("4. Then call wrapper.calibrate()")
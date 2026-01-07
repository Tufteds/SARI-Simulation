# Начальные модули
import sys
import os
import math

# Синглтон
def singleton(cls):
    """Декорирует функцию, делая ее синглтоном"""
    instances = {}
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return get_instance

# Функции-утилиты
class Utils():
    # Получение путя иконки
    @staticmethod
    def resource_path(relative_path):
        """Возвращает абсолютный путь к ресурсу (иконка, файл и т.д.)"""
        try:
            base_path = sys._MEIPASS # PyInstaller
        except AttributeError:
            base_path = os.path.abspath(".") # Обычный запуск
        return os.path.join(base_path, relative_path)
    @staticmethod
    def activity_factor(day):
        if (day-1)%6 == 0:
            return 0.4
        else:
            return 1.0
    @staticmethod
    def is_season_peak(day):
        return 1.0 + 0.6 * math.sin(2 * math.pi * day / 365)
    @staticmethod
    def age_range_for_grade(grade):
        return {
            1: (6, 8),
            2: (7, 9),
            3: (8, 10),
            4: (9, 11),
            5: (10, 12),
            6: (11, 13),
            7: (12, 14),
            8: (13, 15),
            9: (14, 16),
            10: (15, 17),
            11: (16, 18),
        }[grade]

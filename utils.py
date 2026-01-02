# Начальные модули
import sys
import os

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
        if day % 7 in (5, 6):  # сб, вс
            return 0.25  # 5 из 20 классов
        else:
            return 1.0
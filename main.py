# Начальные модули
import tkinter as tk
from gui import GUI
from utils import Utils

# Запуск программы
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Симуляция распространения ОРВИ")
    root.geometry("1500x600")
    root.iconbitmap(default=Utils.resource_path("icons/virus.ico"))
    gui = GUI(root)
    root.mainloop()

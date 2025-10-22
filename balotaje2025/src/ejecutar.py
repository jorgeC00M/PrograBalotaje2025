# src/ejecutar.py
# -*- coding: utf-8 -*-
import tkinter as tk
from .interfaz import App   # <--- CAMBIO CLAVE (punto)

def main():
    root = tk.Tk()
    root.title("Balotaje 2025 - Simulación y Análisis")
    root.geometry("1280x800")
    App(root)
    root.mainloop()

if __name__ == "__main__":
    main()

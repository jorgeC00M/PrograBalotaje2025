import tkinter as tk
from tkinter import ttk

# Paquete local
from .configuracion import AppState
from .tablas import registrar_pestanas  # <-- arma todas las pestañas que estén disponibles


class App(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.state = AppState()
        self.pack(fill="both", expand=True)

        self._setup_style()

        # Notebook principal
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True)

        # Barra de estado inferior
        self.statusbar = ttk.Label(self, text=self._status_text(), anchor="w")
        self.statusbar.pack(side="bottom", fill="x")

        # Construir pestañas por módulos
        registrar_pestanas(self)

    # ---------- utilitarios compartidos ----------
    def _setup_style(self):
        style = ttk.Style()
        style.configure("Treeview", rowheight=26, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

    def _status_text(self):
        d = "Cargados" if self.state.df_proc is not None else "No cargados"
        m = "Entrenado" if self.state.model is not None else "No entrenado"
        return (
            f"Datos: {d}  |  "
            f"Modelo logística multinomial: {m}  |  "
            f"Target: {self.state.target or '(no definido)'}  |  "
            f"T={self.state.T}, R={self.state.R}, warmup={self.state.warmup}"
        )

    def actualizar_status(self):
        self.statusbar.config(text=self._status_text())

    def seleccionar_tab(self, nombre):
        for i in range(self.nb.index("end")):
            if self.nb.tab(i, "text") == nombre:
                self.nb.select(i)
                return


def main():
    root = tk.Tk()
    root.title("Análisis y simulación")
    root.geometry("1100x700")
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()

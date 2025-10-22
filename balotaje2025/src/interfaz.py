# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import messagebox, scrolledtext
import threading, sys, io, traceback

# Importa el main del pipeline
from .ejecutar import main as ejecutar_main

class StreamToText:
    """File-like para redirigir stdout/stderr a un Text de Tk."""
    def __init__(self, text_widget):
        self.text = text_widget

    def write(self, msg):
        if not msg:
            return
        # Escribimos en el hilo de la UI
        self.text.after(0, lambda: (self.text.insert(tk.END, msg), self.text.see(tk.END)))

    def flush(self):
        pass

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Balotaje 2025")
        self.geometry("640x480")

        tk.Label(self, text="BALOTAJE 2025", font=("Arial", 18, "bold")).pack(pady=8)

        frame_btn = tk.Frame(self)
        frame_btn.pack(pady=4)

        self.btn_cros = tk.Button(frame_btn, text="Generar Tablas Cruzadas",
                                  width=30, command=lambda: self.run_pipeline("--crosstabs"))
        self.btn_cros.grid(row=0, column=0, padx=4, pady=4)

        self.btn_mnlogit = tk.Button(frame_btn, text="Entrenar Modelo Multinomial",
                                     width=30, command=lambda: self.run_pipeline("--multinomial"))
        self.btn_mnlogit.grid(row=1, column=0, padx=4, pady=4)

        self.btn_sim = tk.Button(frame_btn, text="Correr Simulación",
                                 width=30, command=lambda: self.run_pipeline("--simular"))
        self.btn_sim.grid(row=2, column=0, padx=4, pady=4)

        tk.Button(self, text="Salir", command=self.destroy).pack(pady=6)

        tk.Label(self, text="Salida / Log:").pack(anchor="w", padx=8)
        self.log = scrolledtext.ScrolledText(self, height=16, wrap=tk.WORD)
        self.log.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        self.status = tk.StringVar(value="Listo.")
        tk.Label(self, textvariable=self.status, anchor="w").pack(fill=tk.X, padx=8, pady=(0,8))

    def set_buttons(self, state):
        self.btn_cros.config(state=state)
        self.btn_mnlogit.config(state=state)
        self.btn_sim.config(state=state)

    def run_pipeline(self, flag: str):
        # Desactivar botones mientras corre
        self.set_buttons(tk.DISABLED)
        self.status.set(f"Ejecutando {flag} ...")

        def worker():
            # Redirigir stdout/stderr al Text
            old_out, old_err = sys.stdout, sys.stderr
            sys.stdout = StreamToText(self.log)
            sys.stderr = StreamToText(self.log)

            # Preparar argv y ejecutar
            try:
                sys.argv = ["ejecutar.py", flag]
                print(f">>> Iniciando {flag}\n")
                ejecutar_main()
                print(f"\n>>> Finalizado {flag}\n")
                self.log.after(0, lambda: messagebox.showinfo("Éxito", f"Proceso {flag} completado."))
            except Exception:
                tb = traceback.format_exc()
                print("\n[ERROR]\n" + tb)
                self.log.after(0, lambda: messagebox.showerror("Error", tb))
            finally:
                # Restaurar stdout/stderr y reactivar botones
                sys.stdout, sys.stderr = old_out, old_err
                self.log.after(0, lambda: (self.set_buttons(tk.NORMAL), self.status.set("Listo.")))

        threading.Thread(target=worker, daemon=True).start()

def iniciar_interfaz():
    App().mainloop()

if __name__ == "__main__":
    iniciar_interfaz()

"""
Punto de entrada principal para el juego de lógica Queens.
Inicializa la ventana de Tkinter y lanza la interfaz de usuario.
"""

import tkinter as tk
from ui import QueensUI


def main():
    """Función de arranque de la aplicación."""
    ventana_principal = tk.Tk()

    # Centrar la ventana en la pantalla del usuario
    ventana_principal.update_idletasks()
    ancho_ventana = 640
    alto_ventana = 790
    x_pos = max(0, (ventana_principal.winfo_screenwidth() - ancho_ventana) // 2)
    y_pos = max(0, (ventana_principal.winfo_screenheight() - alto_ventana) // 2)
    ventana_principal.geometry(f"{ancho_ventana}x{alto_ventana}+{x_pos}+{y_pos}")

    # Inicializar la interfaz del juego
    app = QueensUI(ventana_principal)
    ventana_principal.mainloop()


if __name__ == "__main__":
    main()
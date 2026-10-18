"""
Módulo de interfaz gráfica (UI) para el juego Queens con Tkinter.
Controles actualizados:
  - Clic Izquierdo: Alterna Cruz (❌) / Vacía
  - Arrastrar Clic Izquierdo (Drag): Pinta cruces continuas por donde pasa el ratón
  - Clic Derecho: Coloca / Quita Reina (👑)
"""

import time
import random
from typing import Optional, Tuple, Set
import tkinter as tk
from tkinter import ttk, messagebox

from logic import GameLogic, CellState
from levels import PRESET_LEVELS, REGION_COLORS, generate_board
from scoreboard import ScoreboardManager


class QueensUI:
    """
    Interfaz gráfica interactiva para el juego Queens con soporte de arrastre
    y asignación ergonómica de botones de ratón.
    """

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Queens - Juego de Lógica")
        self.root.geometry("680x870")
        self.root.minsize(620, 780)
        self.root.configure(bg="#0F172A")

        self.selected_size = 8
        self.logic = GameLogic(size=self.selected_size)
        self.scoreboard = ScoreboardManager()

        # Configuración visual adaptativa
        self.canvas_max_pixel = 480
        self.board_margin = 12
        self.hover_cell: Optional[Tuple[int, int]] = None
        self.error_cells: Set[Tuple[int, int]] = set()
        self.is_game_won = False

        # Estado para el arrastre con botón izquierdo (Drag to Cross)
        self.is_dragging_left = False
        self.drag_visited_cells: Set[Tuple[int, int]] = set()

        # Cronómetro
        self.start_time: Optional[float] = None
        self.elapsed_seconds = 0
        self.timer_running = False

        self._setup_styles()
        self._build_header()
        self._build_board()
        self._build_controls()
        self._build_status_bar()

        # Apply hover effects after controls are built
        self._apply_hover_effects()
        # Iniciar primera partida generando un nuevo mapa
        self.start_new_game(reset_timer=True)

        # nested _setup_styles removed
    def _setup_styles(self) -> None:
        """Define font styles used throughout the UI."""
        self.font_title = ("Segoe UI", 20, "bold")
        self.font_badge = ("Segoe UI", 11, "bold")
        self.font_btn = ("Segoe UI", 11, "bold")
        self.font_btn_sm = ("Segoe UI", 10)
        self.font_status = ("Segoe UI", 11, "bold")

    def _apply_hover_effects(self) -> None:
        """Add hover background change to primary buttons after they are created."""
        def _add_hover(widget, bg_normal, bg_hover):
            widget.configure(bg=bg_normal)
            widget.bind("<Enter>", lambda e: widget.configure(bg=bg_hover))
            widget.bind("<Leave>", lambda e: widget.configure(bg=bg_normal))

        for btn in (self.reset_btn, self.undo_btn, self.hint_btn,
                    self.new_map_btn, self.records_btn, self.rules_btn):
            _add_hover(btn, btn["bg"], "#475569")

    def _update_cell_dimensions(self) -> None:
        """Calcula el tamaño de cada celda y fuentes según la dimensión NxN."""
        n = self.logic.size
        self.cell_size = max(34, self.canvas_max_pixel // n)
        self.canvas_dim = self.cell_size * n + self.board_margin * 2

        queen_font_size = max(13, int(self.cell_size * 0.46))
        cross_font_size = max(11, int(self.cell_size * 0.40))
        self.font_queen = ("Segoe UI Emoji", queen_font_size)
        self.font_cross = ("Segoe UI", cross_font_size, "bold")

    def _build_header(self) -> None:
        header_frame = tk.Frame(self.root, bg="#0F172A", pady=8)
        header_frame.pack(fill="x", padx=20)

        # Fila 1: Título, Botón de Récords y Botón de Reglas
        top_row = tk.Frame(header_frame, bg="#0F172A")
        top_row.pack(fill="x", pady=(0, 6))

        title_lbl = tk.Label(top_row, text="👑 QUEENS", font=self.font_title, fg="#F8FAFC", bg="#0F172A")
        title_lbl.pack(side="left")

        self.rules_btn = tk.Button(
            top_row, text="📖 Reglas", font=self.font_btn_sm, bg="#334155", fg="#F8FAFC",
            activebackground="#475569", activeforeground="#FFFFFF", relief="flat", bd=0,
            padx=10, pady=4, cursor="hand2", command=self.show_rules_dialog
        )
        self.rules_btn.pack(side="right", padx=(6, 0))

        self.records_btn = tk.Button(
            top_row, text="🏆 Récords", font=self.font_btn_sm, bg="#D97706", fg="#FFFFFF",
            activebackground="#B45309", activeforeground="#FFFFFF", relief="flat", bd=0,
            padx=12, pady=4, cursor="hand2", command=self.show_scoreboard_dialog
        )
        self.records_btn.pack(side="right")

        # Fila 2: Selector de Tamaño de Cuadrícula (4x4 a 12x12), Nuevo Mapa y Estadísticas
        stats_row = tk.Frame(header_frame, bg="#0F172A")
        stats_row.pack(fill="x", pady=(0, 4))

        size_lbl = tk.Label(stats_row, text="Tamaño:", font=self.font_badge, fg="#94A3B8", bg="#0F172A")
        size_lbl.pack(side="left", padx=(0, 4))

        self.size_var = tk.StringVar(value="8x8")
        size_options = [f"{n}x{n}" for n in range(4, 13)]
        self.size_menu = ttk.Combobox(
            stats_row, textvariable=self.size_var, values=size_options, state="readonly",
            width=6, font=self.font_btn_sm
        )
        self.size_menu.pack(side="left", padx=(0, 8))
        self.size_menu.bind("<<ComboboxSelected>>", self._on_size_changed)

        self.new_map_btn = tk.Button(
            stats_row, text="🎲 Nuevo Mapa", font=self.font_btn_sm, bg="#2563EB", fg="#FFFFFF",
            activebackground="#1D4ED8", activeforeground="#FFFFFF", relief="flat", bd=0,
            padx=10, pady=3, cursor="hand2", command=self.generate_new_map
        )
        self.new_map_btn.pack(side="left", padx=(0, 10))

        self.time_lbl = tk.Label(stats_row, text="⏱️ 00:00", font=self.font_badge, fg="#38BDF8", bg="#1E293B", padx=10, pady=3)
        self.time_lbl.pack(side="right", padx=(8, 0))

        self.queens_lbl = tk.Label(stats_row, text="👑 0 / 8", font=self.font_badge, fg="#FBBF24", bg="#1E293B", padx=10, pady=3)
        self.queens_lbl.pack(side="right")

        # Fila 3: Ajuste de Autocompletado de Cruces (Predeterminado activo)
        settings_row = tk.Frame(header_frame, bg="#0F172A")
        settings_row.pack(fill="x", pady=(2, 0))

        self.auto_cross_var = tk.BooleanVar(value=True)
        self.auto_cross_check = tk.Checkbutton(
            settings_row,
            text="✨ Auto-cruces al colocar reina (fila, columna, región y adyacentes)",
            variable=self.auto_cross_var,
            font=("Segoe UI", 9, "bold"),
            fg="#38BDF8",
            bg="#0F172A",
            activebackground="#0F172A",
            activeforeground="#7DD3FC",
            selectcolor="#1E293B",
            cursor="hand2",
            command=self._on_auto_cross_toggled
        )
        self.auto_cross_check.pack(side="left")
    def show_rules_dialog(self) -> None:
        """Display a modal with the game rules / instructions."""
        # Create a top‑level window that behaves like a dialog
        rules_window = tk.Toplevel(self.root)
        rules_window.title("📖 Reglas del juego")
        rules_window.configure(bg="#0F172A")
        # Make the window modal (prevent interaction with main window)
        rules_window.transient(self.root)
        rules_window.grab_set()

        # Content – you can customize the text or add images as needed
        rules_text = (
            "⭐ Objetivo del juego:\n"
            "Coloca N reinas en un tablero N×N sin que se ataquen entre sí.\n\n"
            "🔧 Controles:\n"
            "• Clic izquierdo: coloca / quita una cruz (❌).\n"
            "• Arrastrar con clic izquierdo: pinta cruces continuas.\n"
            "• Clic derecho: coloca / quita una reina (👑).\n"
            "• Botón “↺ Reiniciar”: vuelve a iniciar el nivel actual.\n"
            "• Botón “💡 Pista”: sugiere una casilla válida.\n"
            "• Botón “🎲 Nuevo Mapa”: genera un nuevo tablero.\n\n"
            "💡 Consejo:\n"
            "Usa la casilla de “Auto‑cruces” para marcar automáticamente "
            "las intersecciones de fila, columna, región y adyacentes cuando "
            "colocas una reina."
        )
        lbl = tk.Label(
            rules_window,
            text=rules_text,
            justify="left",
            wraplength=560,
            font=self.font_btn_sm,
            fg="#F8FAFC",
            bg="#0F172A",
            padx=20,
            pady=20,
        )
        lbl.pack(fill="both", expand=True)
        # Close button
        close_btn = tk.Button(
            rules_window,
            text="✖ Cerrar",
            font=self.font_btn_sm,
            bg="#475569",
            fg="#F8FAFC",
            activebackground="#334155",
            activeforeground="#FFFFFF",
            relief="flat",
            bd=0,
            padx=12,
            pady=6,
            cursor="hand2",
            command=rules_window.destroy,
        )
        close_btn.pack(pady=(0, 12))
        # Center the dialog over the main window
        self.root.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (rules_window.winfo_reqwidth() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (rules_window.winfo_reqheight() // 2)
        rules_window.geometry(f"+{x}+{y}")

    def _on_auto_cross_toggled(self) -> None:
        self.logic.auto_cross_enabled = self.auto_cross_var.get()
        estado = "activadas" if self.logic.auto_cross_enabled else "desactivadas"
        self._set_status(f"Auto-cruces {estado}.", "#94A3B8")

    def _build_board(self) -> None:
        self.board_container = tk.Frame(self.root, bg="#1E293B", bd=0, padx=8, pady=8)
        self.board_container.pack(pady=4)

        self._update_cell_dimensions()
        self.canvas = tk.Canvas(
            self.board_container, width=self.canvas_dim, height=self.canvas_dim,
            bg="#0F172A", highlightthickness=0, cursor="hand2"
        )
        self.canvas.pack()

        # Clic Izquierdo: Cruz y Arrastre continuo
        self.canvas.bind("<Button-1>", self._on_left_click)
        self.canvas.bind("<B1-Motion>", self._on_left_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_left_release)

        # Clic Derecho: Reina
        self.canvas.bind("<Button-3>", self._on_right_click)

        # Efecto Hover
        self.canvas.bind("<Motion>", self._on_mouse_move)
        self.canvas.bind("<Leave>", self._on_mouse_leave)

    def _build_controls(self) -> None:
        btn_frame = tk.Frame(self.root, bg="#0F172A", pady=8)
        btn_frame.pack(fill="x", padx=30)

        self.reset_btn = tk.Button(
            btn_frame, text="↺ Reiniciar", font=self.font_btn, bg="#475569", fg="#F8FAFC",
            activebackground="#334155", activeforeground="#FFFFFF", relief="flat", bd=0,
            padx=16, pady=8, cursor="hand2", command=self.reset_board
        )
        self.reset_btn.pack(side="left", expand=True, fill="x", padx=(0, 4))

        self.undo_btn = tk.Button(
            btn_frame, text="↶ Deshacer", font=self.font_btn, bg="#334155", fg="#F8FAFC",
            activebackground="#1E293B", activeforeground="#FFFFFF", relief="flat", bd=0,
            padx=16, pady=8, cursor="hand2", command=self.undo_move
        )
        self.undo_btn.pack(side="left", expand=True, fill="x", padx=4)

        self.hint_btn = tk.Button(
            btn_frame, text="💡 Pista", font=self.font_btn, bg="#059669", fg="#FFFFFF",
            activebackground="#047857", activeforeground="#FFFFFF", relief="flat", bd=0,
            padx=16, pady=8, cursor="hand2", command=self.give_hint
        )
        self.hint_btn.pack(side="left", expand=True, fill="x", padx=(4, 0))

    def _build_status_bar(self) -> None:
        self.status_frame = tk.Frame(self.root, bg="#1E293B", padx=16, pady=8)
        self.status_frame.pack(fill="x", side="bottom", padx=20, pady=(0, 14))

        self.status_lbl = tk.Label(
            self.status_frame, text="Clic Izquierdo: Cruz (arrastra para varias) | Clic Derecho: Reina",
            font=self.font_status, fg="#94A3B8", bg="#1E293B", wraplength=600, justify="center"
        )
        self.status_lbl.pack(fill="x")

    def draw_board(self) -> None:
        self.canvas.delete("all")
        size = self.logic.size
        m = self.board_margin
        cs = self.cell_size

        for r in range(size):
            for c in range(size):
                x1 = m + c * cs
                y1 = m + r * cs
                x2 = x1 + cs
                y2 = y1 + cs

                reg_id = self.logic.regions[r][c]
                base_color = REGION_COLORS[reg_id % len(REGION_COLORS)]

                if (r, c) in self.error_cells:
                    fill_color = "#FCA5A5"
                elif self.hover_cell == (r, c) and not self.is_game_won:
                    fill_color = self._tint_color(base_color, factor=0.92)
                else:
                    fill_color = base_color

                self.canvas.create_rectangle(x1, y1, x2, y2, fill=fill_color, outline="")

        # Líneas internas punteadas
        inner_line_color = "#64748B"
        for r in range(size):
            for c in range(size):
                x1 = m + c * cs
                y1 = m + r * cs
                x2 = x1 + cs
                y2 = y1 + cs
                reg = self.logic.regions[r][c]

                if c < size - 1 and self.logic.regions[r][c + 1] == reg:
                    self.canvas.create_line(x2, y1, x2, y2, fill=inner_line_color, width=1, dash=(2, 2))
                if r < size - 1 and self.logic.regions[r + 1][c] == reg:
                    self.canvas.create_line(x1, y2, x2, y2, fill=inner_line_color, width=1, dash=(2, 2))

        # Bordes gruesos de regiones
        border_color = "#0F172A"
        border_w = max(2, min(4, int(cs * 0.08)))

        for r in range(size):
            for c in range(size):
                x1 = m + c * cs
                y1 = m + r * cs
                x2 = x1 + cs
                y2 = y1 + cs
                reg = self.logic.regions[r][c]

                if r == 0 or self.logic.regions[r - 1][c] != reg:
                    self.canvas.create_line(x1, y1, x2, y1, fill=border_color, width=border_w, capstyle="round")
                if r == size - 1 or self.logic.regions[r + 1][c] != reg:
                    self.canvas.create_line(x1, y2, x2, y2, fill=border_color, width=border_w, capstyle="round")
                if c == 0 or self.logic.regions[r][c - 1] != reg:
                    self.canvas.create_line(x1, y1, x1, y2, fill=border_color, width=border_w, capstyle="round")
                if c == size - 1 or self.logic.regions[r][c + 1] != reg:
                    self.canvas.create_line(x2, y1, x2, y2, fill=border_color, width=border_w, capstyle="round")

        # Reinas y Cruces
        for r in range(size):
            for c in range(size):
                x_center = m + c * cs + cs / 2
                y_center = m + r * cs + cs / 2
                state = self.logic.board[r][c]

                if state == CellState.QUEEN:
                    circle_r = cs * 0.38
                    badge_fill = "#FEF3C7" if (r, c) not in self.error_cells else "#FEE2E2"
                    badge_outline = "#F59E0B" if (r, c) not in self.error_cells else "#EF4444"

                    self.canvas.create_oval(
                        x_center - circle_r, y_center - circle_r,
                        x_center + circle_r, y_center + circle_r,
                        fill=badge_fill, outline=badge_outline, width=max(1, int(cs * 0.04))
                    )
                    self.canvas.create_text(x_center, y_center, text="👑", font=self.font_queen)

                elif state == CellState.CROSS:
                    self.canvas.create_text(x_center, y_center, text="✕", fill="#334155", font=self.font_cross)

        queens_count = self.logic.count_queens()
        self.queens_lbl.config(text=f"👑 {queens_count} / {self.logic.size}")

    def _tint_color(self, hex_color: str, factor: float = 0.9) -> str:
        hex_color = hex_color.lstrip("#")
        r, g, b = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
        r = max(0, min(255, int(r * factor)))
        g = max(0, min(255, int(g * factor)))
        b = max(0, min(255, int(b * factor)))
        return f"#{r:02x}{g:02x}{b:02x}"

    def _get_cell_at_coords(self, x: int, y: int) -> Optional[Tuple[int, int]]:
        m = self.board_margin
        cs = self.cell_size
        col = (x - m) // cs
        row = (y - m) // cs
        if 0 <= row < self.logic.size and 0 <= col < self.logic.size:
            return (row, col)
        return None

    # ==========================================================================
    # MANEJO DE EVENTOS DE RATÓN (NUEVOS CONTROLES Y ARRASTRE)
    # ==========================================================================

    def _on_left_click(self, event: tk.Event) -> None:
        """
        Clic Izquierdo: Alterna entre Cruz (❌) y Vacía.
        Inicia el estado de arrastre para pintar múltiples cruces si se mantiene pulsado.
        """
        if self.is_game_won:
            return

        coords = self._get_cell_at_coords(event.x, event.y)
        if coords is None:
            return

        self.is_dragging_left = True
        self.drag_visited_cells = {coords}

        r, c = coords
        # Alternar cruz
        self.logic.toggle_cross(r, c)

        if not self.timer_running and self.elapsed_seconds == 0:
            self._start_timer()

        self.draw_board()

    def _on_left_drag(self, event: tk.Event) -> None:
        """
        Arrastre con botón izquierdo pulsado: Aplica cruces en todas las casillas
        vacías por las que pasa el cursor.
        """
        if self.is_game_won or not self.is_dragging_left:
            return

        coords = self._get_cell_at_coords(event.x, event.y)
        if coords is None or coords in self.drag_visited_cells:
            return

        self.drag_visited_cells.add(coords)
        r, c = coords

        # Al arrastrar, si la casilla está vacía, colocarle Cruz (❌)
        if self.logic.board[r][c] == CellState.EMPTY:
            self.logic.set_cell(r, c, CellState.CROSS)
            self.draw_board()

    def _on_left_release(self, event: tk.Event) -> None:
        """Finaliza el modo de arrastre."""
        self.is_dragging_left = False
        self.drag_visited_cells.clear()

    def _on_right_click(self, event: tk.Event) -> None:
        """
        Clic Derecho: Coloca o retira una Reina (👑).
        Si la celda no tiene reina, coloca Reina (y auto-cruces si está activado).
        Si ya tiene reina, la quita dejándola vacía.
        """
        if self.is_game_won:
            return

        coords = self._get_cell_at_coords(event.x, event.y)
        if coords is None:
            return

        r, c = coords
        old_state = self.logic.board[r][c]

        if old_state == CellState.QUEEN:
            # Quitar la reina
            self.logic.set_cell(r, c, CellState.EMPTY)
        else:
            # Colocar la reina
            self.logic.set_cell(r, c, CellState.QUEEN)

        if not self.timer_running and self.elapsed_seconds == 0:
            self._start_timer()

        self.draw_board()
        self._check_automatic_victory()

    def _on_mouse_move(self, event: tk.Event) -> None:
        coords = self._get_cell_at_coords(event.x, event.y)
        if coords != self.hover_cell:
            self.hover_cell = coords
            self.draw_board()

    def _on_mouse_leave(self, event: tk.Event) -> None:
        if self.hover_cell is not None:
            self.hover_cell = None
            self.draw_board()

    def _check_automatic_victory(self) -> None:
        """Evalúa si se han cumplido todas las reglas para la victoria."""
        if self.logic.count_queens() == self.logic.size:
            result = self.logic.validate_solution()
            if result.is_valid:
                self.is_game_won = True
                self._stop_timer()
                self.error_cells.clear()
                self.draw_board()

                rank_pos = self.scoreboard.add_record(
                    grid_size=self.logic.size,
                    elapsed_seconds=self.elapsed_seconds,
                    moves=self.logic.move_count
                )

                mins, secs = divmod(self.elapsed_seconds, 60)
                time_str = f"{mins:02d}:{secs:02d}"
                success_msg = f"🎉 ¡VICTORIA! Tablero {self.logic.size}x{self.logic.size} en {time_str} (#{rank_pos} en Récords)."
                self._set_status(success_msg, "#10B981")

                self.show_victory_modal(time_str, rank_pos)

    def show_scoreboard_dialog(self) -> None:
        """Ventana de Scoreboard con estilo premium."""
        dialog = tk.Toplevel(self.root)
        dialog.title("🏆 Scoreboard – Récords")
        dialog.geometry("580x560")
        dialog.configure(bg="#0F172A")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        # Center dialog
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 580) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 560) // 2
        dialog.geometry(f"+{max(0, x)}+{max(0, y)}")

        # Header with gradient background (simulated with a solid dark color)
        header = tk.Frame(dialog, bg="#1E293B", pady=12)
        header.pack(fill="x", padx=20)

        tk.Label(
            header,
            text="🏆 TABLERO DE RÉCORDS",
            font=("Segoe UI", 18, "bold"),
            fg="#FBBF24",
            bg="#1E293B",
        ).pack(side="left", padx=10)

        # Close icon (hover effect)
        def _close_enter(e):
            close_btn.configure(bg="#475569")

        def _close_leave(e):
            close_btn.configure(bg="#334155")

        close_btn = tk.Button(
            header,
            text="✖",
            font=("Segoe UI", 12, "bold"),
            bg="#334155",
            fg="#F8FAFC",
            activebackground="#475569",
            activeforeground="#FFFFFF",
            relief="flat",
            bd=0,
            width=3,
            cursor="hand2",
            command=dialog.destroy,
        )
        close_btn.pack(side="right")
        close_btn.bind("<Enter>", _close_enter)
        close_btn.bind("<Leave>", _close_leave)

        # Tabbed view – one tab per board size
        style = ttk.Style(dialog)
        style.theme_use("clam")
        style.configure(
            "TNotebook",
            background="#0F172A",
            borderwidth=0,
        )
        style.configure(
            "TNotebook.Tab",
            background="#1E293B",
            foreground="#F8FAFC",
            padding=[12, 6],
            font=("Segoe UI", 11, "bold"),
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", "#2563EB")],
            foreground=[("selected", "#FFFFFF")],
        )
        notebook = ttk.Notebook(dialog)
        notebook.pack(fill="both", expand=True, padx=20, pady=(10, 15))

        for sz in range(4, 13):
            tab = tk.Frame(notebook, bg="#1E293B")
            notebook.add(tab, text=f"{sz}x{sz}")

            records = self.scoreboard.get_top_records(grid_size=sz, limit=10)

            if not records:
                tk.Label(
                    tab,
                    text=f"Aún no hay partidas completadas en {sz}x{sz}.\\n¡Gana una para registrar tu tiempo!",
                    font=("Segoe UI", 11),
                    fg="#94A3B8",
                    bg="#1E293B",
                    justify="center",
                ).pack(expand=True, pady=40)
                continue

            # Treeview with modern colors
            tree_frame = tk.Frame(tab, bg="#1E293B", padx=10, pady=10)
            tree_frame.pack(fill="both", expand=True)

            cols = ("pos", "time", "moves", "date")
            tree = ttk.Treeview(
                tree_frame,
                columns=cols,
                show="headings",
                height=9,
                style="mystyle.Treeview",
            )
            for col, width, anchor in (
                ("pos", 50, "center"),
                ("time", 110, "center"),
                ("moves", 100, "center"),
                ("date", 150, "center"),
            ):
                tree.heading(col, text=col.upper())
                tree.column(col, width=width, anchor=anchor)

            # Insert rows with medal emojis
            for idx, rec in enumerate(records, 1):
                medal = (
                    "🥇"
                    if idx == 1
                    else "🥈"
                    if idx == 2
                    else "🥉"
                    if idx == 3
                    else f"#{idx}"
                )
                tree.insert(
                    "",
                    "end",
                    values=(
                        medal,
                        rec["time_formatted"],
                        rec.get("moves", "-"),
                        rec.get("date", "-"),
                    ),
                )
            tree.pack(fill="both", expand=True)

            # Subtle hover highlight (requires a tiny style tweak)
            style.configure(
                "mystyle.Treeview",
                background="#1E293B",
                foreground="#F8FAFC",
                fieldbackground="#1E293B",
                rowheight=25,
                font=("Segoe UI", 10),
            )
            style.map(
                "mystyle.Treeview",
                background=[("selected", "#2563EB")],
                foreground=[("selected", "#FFFFFF")],
            )
            
    def show_victory_modal(self, time_str: str, rank_pos: int) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title("¡Victoria!")
        dialog.geometry("450x380")
        dialog.configure(bg="#0F172A")
        dialog.transient(self.root)
        dialog.grab_set()

        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 450) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 380) // 2
        dialog.geometry(f"+{max(0, x)}+{max(0, y)}")

        tk.Label(
            dialog, text="👑 ¡ENHORABUENA! 👑",
            font=("Segoe UI", 18, "bold"), fg="#FBBF24", bg="#0F172A"
        ).pack(pady=(20, 8))

        tk.Label(
            dialog,
            text=f"¡Has completado el tablero de {self.logic.size}x{self.logic.size}!",
            font=("Segoe UI", 12), fg="#F8FAFC", bg="#0F172A"
        ).pack(pady=(0, 15))

        stats_frame = tk.Frame(dialog, bg="#1E293B", padx=20, pady=15)
        stats_frame.pack(fill="x", padx=30, pady=(0, 20))

        tk.Label(
            stats_frame, text=f"⏱️ Tiempo: {time_str}",
            font=("Segoe UI", 14, "bold"), fg="#38BDF8", bg="#1E293B"
        ).pack(anchor="w", pady=2)

        tk.Label(
            stats_frame, text=f"🎯 Movimientos: {self.logic.move_count}",
            font=("Segoe UI", 12), fg="#94A3B8", bg="#1E293B"
        ).pack(anchor="w", pady=2)

        tk.Label(
            stats_frame, text=f"🏆 Posición en Récords ({self.logic.size}x{self.logic.size}): #{rank_pos}",
            font=("Segoe UI", 12, "bold"), fg="#10B981", bg="#1E293B"
        ).pack(anchor="w", pady=2)

        btn_box = tk.Frame(dialog, bg="#0F172A")
        btn_box.pack(fill="x", padx=30)

        next_map_btn = tk.Button(
            btn_box, text="🎲 Siguiente Partida", font=("Segoe UI", 11, "bold"),
            bg="#10B981", fg="#FFFFFF", activebackground="#059669", activeforeground="#FFFFFF",
            relief="flat", bd=0, padx=14, pady=8, cursor="hand2",
            command=lambda: [dialog.destroy(), self.generate_new_map()]
        )
        next_map_btn.pack(side="left", expand=True, fill="x", padx=(0, 6))

        view_scores_btn = tk.Button(
            btn_box, text="🏆 Ver Scoreboard", font=("Segoe UI", 11, "bold"),
            bg="#2563EB", fg="#FFFFFF", activebackground="#1D4ED8", activeforeground="#FFFFFF",
            relief="flat", bd=0, padx=14, pady=8, cursor="hand2",
            command=lambda: [dialog.destroy(), self.show_scoreboard_dialog()]
        )
        view_scores_btn.pack(side="right", expand=True, fill="x", padx=(6, 0))

    def reset_board(self) -> None:
        self.logic.reset()
        self.error_cells.clear()
        self.is_game_won = False
        self._reset_timer()
        self._set_status("Tablero reiniciado. ¡Buena suerte!", "#94A3B8")
        self.draw_board()

    def undo_move(self) -> None:
        if self.is_game_won:
            return
        if self.logic.undo():
            self.error_cells.clear()
            self._set_status("Movimiento deshecho.", "#94A3B8")
            self.draw_board()

    def give_hint(self) -> None:
        if self.is_game_won:
            return
        solution = self.logic.solve()
        if not solution:
            self._set_status("No se encontró solución para esta configuración.", "#EF4444")
            return

        current_queens = set(self.logic.get_queens())
        missing_queens = [pos for pos in solution if pos not in current_queens]

        if missing_queens:
            r, c = random.choice(missing_queens)
            self.logic.set_cell(r, c, CellState.QUEEN)
            self._set_status(f"💡 Pista: Se colocó una reina en la fila {r+1}, columna {c+1}.", "#F59E0B")
            self.draw_board()
            self._check_automatic_victory()
        else:
            self._set_status("Todas las reinas correctas están colocadas.", "#10B981")

    def _on_size_changed(self, event: tk.Event) -> None:
        raw_size = self.size_var.get().split("x")[0]
        self.selected_size = int(raw_size)
        self.generate_new_map()

    def generate_new_map(self) -> None:
        self.logic.create_new_random_level(size=self.selected_size)
        self._resize_canvas()
        self.error_cells.clear()
        self.is_game_won = False
        self._reset_timer()
        self._set_status(f"Nuevo mapa de {self.selected_size}x{self.selected_size} generado. ¡A jugar!", "#38BDF8")
        self.draw_board()

    def start_new_game(self, reset_timer: bool = True) -> None:
        self.generate_new_map()

    def _resize_canvas(self) -> None:
        self._update_cell_dimensions()
        self.canvas.config(width=self.canvas_dim, height=self.canvas_dim)

    def show_rules_dialog(self) -> None:
        """Ventana modal con instrucciones gráficas y atractivas."""
        # --- Modal setup ---------------------------------------------------------
        dialog = tk.Toplevel(self.root)
        dialog.title("📖 Reglas del Juego")
        dialog.geometry("560x660")
        dialog.configure(bg="#0F172A")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        # Center the dialog
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 560) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 660) // 2
        dialog.geometry(f"+{max(0, x)}+{max(0, y)}")

        # --- Glass‑morphism container --------------------------------------------
        container = tk.Frame(dialog, bg="#1E293B", bd=0, relief="flat")
        container.place(relx=0.05, rely=0.05, relwidth=0.90, relheight=0.90)

        # Header with icon
        tk.Label(
            container,
            text="📖 Reglas del Juego",
            font=("Segoe UI", 20, "bold"),
            fg="#FBBF24",
            bg="#1E293B"
        ).pack(pady=(20, 10))

        # Scrollable text area (styled)
        txt_frame = tk.Frame(container, bg="#1E293B")
        txt_frame.pack(fill="both", expand=True, padx=20, pady=10)

        scrollbar = tk.Scrollbar(txt_frame)
        scrollbar.pack(side="right", fill="y")

        rules = tk.Text(
            txt_frame,
            wrap="word",
            font=("Segoe UI", 11),
            fg="#F8FAFC",
            bg="#0F172A",
            bd=0,
            relief="flat",
            yscrollcommand=scrollbar.set,
            spacing3=4,
            highlightthickness=0,
            insertbackground="#F8FAFC",
        )
        rules.pack(fill="both", expand=True)
        scrollbar.config(command=rules.yview)

        # ------------------------------------------------------------
        #  Graphic‑rich rules (emoji + short bullet)
        # ------------------------------------------------------------
        rules_content = """
    🧭 **Objetivo**  
    Coloca una reina (👑) en cada fila y columna sin que se amenacen entre sí.  
    Cada región debe contener al menos una casilla coloreada.

    ❌ **Cruces (✕)**  
    Pueden marcarse en cualquier celda vacía.  
    Si la opción *Auto‑cruces* está activada, al colocar una reina se añaden cruces automáticamente a:
    - La fila y columna de la reina.
    - Todas las celdas de la región.
    - Las casillas adyacentes a la reina.

    🖱️ **Controles**  
    - **Clic izquierdo** → Alterna cruz (❌) / vacío.  
    Arrastra mientras mantienes pulsado para dibujar varias cruces.  
    - **Clic derecho** → Coloca / quita una reina (👑).  
    - **Botón “Nuevo Mapa”** → Genera otro tablero con solución única.  

    ⏱️ **Cronómetro**  
    Se inicia al primer movimiento y se detiene al lograr la victoria.

    🏆 **Récords**  
    Los mejores tiempos quedan guardados en el Scoreboard y muestran su posición al ganar.

    🚀 **Consejo**  
    Usa la pista (💡) para que el juego resalte una celda que pueda ayudar a avanzar.  
    """

        rules.insert("1.0", rules_content)
        rules.configure(state="disabled")

        # Close button with subtle hover animation
        def _on_enter(e):
            close_btn.configure(bg="#475569")

        def _on_leave(e):
            close_btn.configure(bg="#334155")

        close_btn = tk.Button(
            container,
            text="✖ Cerrar",
            font=("Segoe UI", 11, "bold"),
            bg="#334155",
            fg="#F8FAFC",
            activebackground="#475569",
            activeforeground="#FFFFFF",
            relief="flat",
            bd=0,
            padx=14,
            pady=8,
            cursor="hand2",
            command=dialog.destroy,
        )
        close_btn.pack(pady=(0, 20))
        close_btn.bind("<Enter>", _on_enter)
        close_btn.bind("<Leave>", _on_leave)


    def _start_timer(self) -> None:
        if not self.timer_running:
            self.timer_running = True
            self.start_time = time.time() - self.elapsed_seconds
            self._timer_tick()

    def _timer_tick(self) -> None:
        if self.timer_running:
            self.elapsed_seconds = int(time.time() - self.start_time)
            mins, secs = divmod(self.elapsed_seconds, 60)
            self.time_lbl.config(text=f"⏱️ {mins:02d}:{secs:02d}")
            self.root.after(1000, self._timer_tick)

    def _stop_timer(self) -> None:
        self.timer_running = False

    def _reset_timer(self) -> None:
        self._stop_timer()
        self.elapsed_seconds = 0
        self.time_lbl.config(text="⏱️ 00:00")

    def _set_status(self, text: str, color: str = "#94A3B8") -> None:
        self.status_lbl.config(text=text, fg=color)

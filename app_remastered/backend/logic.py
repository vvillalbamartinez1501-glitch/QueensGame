"""
Módulo de lógica pura y reglas de juego para Queens (Star Battle).
Soporta dimensiones arbitrarias de tablero (desde 4x4 hasta 12x12)
y autocompletado inteligente de cruces (Auto-X).
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Tuple, Set, Optional, Dict
from .levels import PRESET_LEVELS, generate_board


class CellState(Enum):
    """Representa el contenido de una celda en el tablero."""
    EMPTY = 0   # Celda vacía
    QUEEN = 1   # Celda con Reina (👑)
    CROSS = 2   # Celda marcada con Cruz (❌)


@dataclass
class ValidationResult:
    """Resultado del diagnóstico de la solución propuesta por el jugador."""
    is_valid: bool
    message: str
    error_type: str = "ok"  # 'ok', 'count', 'row', 'col', 'region', 'touching'
    error_cells: Set[Tuple[int, int]] = field(default_factory=set)


class GameLogic:
    """
    Controla el estado interno del tablero, la interacción con las celdas,
    la validación estricta de las reglas y el autocompletado de cruces.
    """

    def __init__(self, size: int = 8, regions: Optional[List[List[int]]] = None):
        """
        Inicializa el motor de juego.
        :param size: Dimensión N de la cuadrícula NxN (entre 4 y 12).
        :param regions: Matriz NxN opcional con las regiones.
        """
        self.size = max(4, min(12, size))
        if regions is not None:
            self.regions = [row[:] for row in regions]
            self.size = len(self.regions)
        else:
            new_grid, _ = generate_board(self.size)
            self.regions = new_grid

        self.board = [[CellState.EMPTY for _ in range(self.size)] for _ in range(self.size)]
        # Cada elemento del historial almacena un lote de cambios: lista de (r, c, old_state, new_state)
        self.history: List[List[Tuple[int, int, CellState, CellState]]] = []
        self.move_count = 0
        self.auto_cross_enabled = True  # Activado por defecto según requerimiento

    def load_level(self, regions: List[List[int]]) -> None:
        """Carga una nueva matriz de regiones y reinicia el estado del tablero."""
        self.size = len(regions)
        self.regions = [row[:] for row in regions]
        self.reset()

    def create_new_random_level(self, size: Optional[int] = None) -> None:
        """Crea y carga un mapa totalmente nuevo y único."""
        if size is not None:
            self.size = max(4, min(12, size))
        new_grid, _ = generate_board(self.size)
        self.load_level(new_grid)

    def cycle_cell(self, row: int, col: int) -> CellState:
        """
        Cicla el estado de una celda:
          Vacía -> Reina (👑) -> Cruz (❌) -> Vacía
        Si se coloca una Reina y auto_cross_enabled está activo,
        coloca automáticamente cruces en su fila, columna, región y casillas adyacentes.
        """
        old_state = self.board[row][col]
        batch_changes: List[Tuple[int, int, CellState, CellState]] = []

        if old_state == CellState.EMPTY:
            new_state = CellState.QUEEN
            self.board[row][col] = new_state
            batch_changes.append((row, col, old_state, new_state))

            # Auto-completado de cruces en fila, columna, color y casillas adyacentes
            if self.auto_cross_enabled:
                cross_cells = self._get_blocked_cells_for_queen(row, col)
                for cr, cc in cross_cells:
                    if self.board[cr][cc] == CellState.EMPTY:
                        self.board[cr][cc] = CellState.CROSS
                        batch_changes.append((cr, cc, CellState.EMPTY, CellState.CROSS))

        elif old_state == CellState.QUEEN:
            new_state = CellState.CROSS
            self.board[row][col] = new_state
            batch_changes.append((row, col, old_state, new_state))
        else:
            new_state = CellState.EMPTY
            self.board[row][col] = new_state
            batch_changes.append((row, col, old_state, new_state))

        self.history.append(batch_changes)
        self.move_count += 1
        return new_state

    def _get_blocked_cells_for_queen(self, row: int, col: int) -> Set[Tuple[int, int]]:
        """
        Calcula el conjunto de casillas bloqueadas por una reina:
        - Toda su fila
        - Toda su columna
        - Toda su región de color
        - Todas las 8 casillas adyacentes (ortogonales y diagonales)
        """
        blocked = set()
        queen_region = self.regions[row][col]

        # 1. Fila y Columna
        for c in range(self.size):
            if c != col:
                blocked.add((row, c))
        for r in range(self.size):
            if r != row:
                blocked.add((r, col))

        # 2. Región de Color
        for r in range(self.size):
            for c in range(self.size):
                if (r != row or c != col) and self.regions[r][c] == queen_region:
                    blocked.add((r, c))

        # 3. Adyacencia en 8 direcciones (ortogonales y diagonales)
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = row + dr, col + dc
                if 0 <= nr < self.size and 0 <= nc < self.size:
                    blocked.add((nr, nc))

        return blocked

    def toggle_cross(self, row: int, col: int) -> CellState:
        """Atajo para marcar o desmarcar rápidamente una Cruz (❌)."""
        old_state = self.board[row][col]
        new_state = CellState.EMPTY if old_state == CellState.CROSS else CellState.CROSS
        self.board[row][col] = new_state
        self.history.append([(row, col, old_state, new_state)])
        self.move_count += 1
        return new_state

    def set_cell(self, row: int, col: int, state: CellState) -> None:
        """Establece directamente el estado de una celda."""
        old_state = self.board[row][col]
        if old_state != state:
            batch = [(row, col, old_state, state)]
            self.board[row][col] = state

            if state == CellState.QUEEN and self.auto_cross_enabled:
                for cr, cc in self._get_blocked_cells_for_queen(row, col):
                    if self.board[cr][cc] == CellState.EMPTY:
                        self.board[cr][cc] = CellState.CROSS
                        batch.append((cr, cc, CellState.EMPTY, CellState.CROSS))

            self.history.append(batch)
            self.move_count += 1

    def undo(self) -> bool:
        """Revierte el último lote de cambios (incluyendo cruces automáticas)."""
        if not self.history:
            return False
        batch = self.history.pop()
        # Revertir en orden inverso
        for r, c, old_state, _ in reversed(batch):
            self.board[r][c] = old_state
        if self.move_count > 0:
            self.move_count -= 1
        return True

    def reset(self) -> None:
        """Limpia las marcas del tablero y el historial."""
        self.board = [[CellState.EMPTY for _ in range(self.size)] for _ in range(self.size)]
        self.history.clear()
        self.move_count = 0

    def get_queens(self) -> List[Tuple[int, int]]:
        """Retorna las coordenadas (fila, columna) de todas las reinas colocadas."""
        queens = []
        for r in range(self.size):
            for c in range(self.size):
                if self.board[r][c] == CellState.QUEEN:
                    queens.append((r, c))
        return queens

    def count_queens(self) -> int:
        """Retorna el número de reinas actualmente en el tablero."""
        return len(self.get_queens())

    def validate_solution(self) -> ValidationResult:
        """
        Verifica el cumplimiento de las 4 condiciones de victoria:
          1. Exactamente UNA reina por fila.
          2. Exactamente UNA reina por columna.
          3. Exactamente UNA reina por región de color.
          4. Dos reinas NUNCA pueden tocarse (ni ortogonal ni diagonalmente).
        """
        queens = self.get_queens()
        total_queens = len(queens)

        if total_queens < self.size:
            return ValidationResult(
                is_valid=False,
                message=f"Faltan reinas por colocar ({total_queens}/{self.size}).",
                error_type="count"
            )
        if total_queens > self.size:
            return ValidationResult(
                is_valid=False,
                message=f"Hay demasiadas reinas ({total_queens}/{self.size}).",
                error_type="count"
            )

        # Regla 4: Adyacencia
        touching_conflicts = set()
        for i in range(total_queens):
            r1, c1 = queens[i]
            for j in range(i + 1, total_queens):
                r2, c2 = queens[j]
                if abs(r1 - r2) <= 1 and abs(c1 - c2) <= 1:
                    touching_conflicts.add((r1, c1))
                    touching_conflicts.add((r2, c2))

        if touching_conflicts:
            return ValidationResult(
                is_valid=False,
                message="¡Hay reinas que se tocan! No pueden ser adyacentes (ni ortogonal ni diagonalmente).",
                error_type="touching",
                error_cells=touching_conflicts
            )

        # Regla 1: Fila
        row_map: Dict[int, List[Tuple[int, int]]] = {r: [] for r in range(self.size)}
        for r, c in queens:
            row_map[r].append((r, c))

        for r, q_list in row_map.items():
            if len(q_list) > 1:
                return ValidationResult(
                    is_valid=False,
                    message=f"Conflicto en la Fila {r + 1}: contiene {len(q_list)} reinas.",
                    error_type="row",
                    error_cells=set(q_list)
                )

        # Regla 2: Columna
        col_map: Dict[int, List[Tuple[int, int]]] = {c: [] for c in range(self.size)}
        for r, c in queens:
            col_map[c].append((r, c))

        for c, q_list in col_map.items():
            if len(q_list) > 1:
                return ValidationResult(
                    is_valid=False,
                    message=f"Conflicto en la Columna {c + 1}: contiene {len(q_list)} reinas.",
                    error_type="col",
                    error_cells=set(q_list)
                )

        # Regla 3: Región de color
        region_map: Dict[int, List[Tuple[int, int]]] = {}
        for r, c in queens:
            reg = self.regions[r][c]
            region_map.setdefault(reg, []).append((r, c))

        all_unique_regions = set(cell for row in self.regions for cell in row)
        for reg in all_unique_regions:
            q_list = region_map.get(reg, [])
            if len(q_list) > 1:
                return ValidationResult(
                    is_valid=False,
                    message=f"Conflicto en la Región #{reg + 1}: contiene {len(q_list)} reinas.",
                    error_type="region",
                    error_cells=set(q_list)
                )

        return ValidationResult(
            is_valid=True,
            message="¡ENHORABUENA! ¡Has resuelto el puzzle perfectamente!",
            error_type="ok"
        )

    def solve(self) -> Optional[List[Tuple[int, int]]]:
        """
        Resuelve el tablero mediante backtracking.
        Retorna la lista de coordenadas de las reinas o None si no hay solución.
        """
        n = self.size
        grid = self.regions
        solutions: List[List[int]] = []

        def backtrack(row: int, current_cols: List[int], used_regions: Set[int]):
            if row == n:
                solutions.append(list(current_cols))
                return
            for col in range(n):
                if col in current_cols:
                    continue
                reg = grid[row][col]
                if reg in used_regions:
                    continue
                if row > 0 and abs(current_cols[-1] - col) <= 1:
                    continue

                current_cols.append(col)
                used_regions.add(reg)
                backtrack(row + 1, current_cols, used_regions)
                current_cols.pop()
                used_regions.remove(reg)
                if len(solutions) >= 1:
                    return

        backtrack(0, [], set())
        if solutions:
            return [(r, solutions[0][r]) for r in range(n)]
        return None

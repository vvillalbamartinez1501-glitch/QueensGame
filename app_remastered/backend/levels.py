"""
Módulo de definición de niveles, paleta de colores extendida y generación
de mapas para el juego Queens (desde 4x4 hasta 12x12).
"""

from typing import List, Tuple, Dict, Any, Optional, Set
import random

def count_alternative_solutions(grid: List[List[int]], known: List[int], limit: int = 2) -> int:
    """Counts alternative solutions different from known queen columns."""
    solutions = 0
    N = len(grid)
    def backtrack(row: int, current_cols: List[int], used_regions: Set[int]):
        nonlocal solutions
        if solutions >= limit:
            return
        if row == N:
            if current_cols != known:
                solutions += 1
            return
        for col in range(N):
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
    backtrack(0, [], set())
    return solutions

# ==============================================================================
# PALETA DE COLORES EXTENDIDA (Mínimo 12 colores distintivos y armoniosos)
# ==============================================================================
REGION_COLORS: List[str] = [
    "#A7F3D0",  # 0: Menta suave (Emerald pastel)
    "#FDE68A",  # 1: Ámbar luminoso
    "#BAE6FD",  # 2: Azul cielo
    "#DDD6FE",  # 3: Lavanda suave
    "#FBCFE8",  # 4: Rosa empolvado
    "#FED7AA",  # 5: Melocotón cálido
    "#C7D2FE",  # 6: Índigo perla
    "#E2E8F0",  # 7: Pizarra pastel
    "#D9F99D",  # 8: Lima suave
    "#FCA5A5",  # 9: Coral pastel
    "#99F6E4",  # 10: Turquesa suave
    "#F5D0FE"   # 11: Fucsia / Orquídea pastel
]

# ==============================================================================
# BANCO DE NIVELES PRECONFIGURADOS CLÁSICOS (8x8)
# ==============================================================================
PRESET_LEVELS: Dict[str, Dict[str, Any]] = {
    "Nivel 1 (Clásico 8x8)": {
        "size": 8,
        "regions": [
            [0, 0, 0, 0, 1, 1, 1, 1],
            [0, 2, 2, 0, 1, 3, 3, 1],
            [0, 0, 2, 2, 3, 3, 4, 1],
            [0, 0, 0, 5, 3, 4, 4, 1],
            [0, 0, 6, 6, 6, 6, 4, 1],
            [0, 0, 6, 7, 7, 6, 4, 1],
            [4, 4, 6, 6, 6, 6, 4, 1],
            [4, 4, 4, 4, 4, 4, 4, 1]
        ],
        "solution": [(0, 7), (1, 1), (2, 5), (3, 3), (4, 0), (5, 4), (6, 2), (7, 6)]
    },
    "Nivel 2 (Intermedio 8x8)": {
        "size": 8,
        "regions": [
            [3, 3, 1, 1, 1, 1, 1, 1],
            [3, 3, 2, 2, 2, 2, 2, 1],
            [3, 3, 0, 0, 0, 4, 1, 1],
            [3, 3, 5, 5, 4, 4, 4, 4],
            [3, 3, 3, 3, 6, 6, 4, 4],
            [3, 3, 3, 6, 6, 6, 7, 4],
            [3, 6, 6, 6, 6, 6, 7, 4],
            [3, 3, 7, 7, 7, 7, 7, 7]
        ],
        "solution": [(0, 3), (1, 6), (2, 4), (3, 2), (4, 0), (5, 7), (6, 1), (7, 5)]
    },
    "Nivel 3 (Avanzado 8x8)": {
        "size": 8,
        "regions": [
            [0, 0, 0, 0, 0, 0, 0, 1],
            [0, 2, 2, 3, 4, 4, 0, 1],
            [0, 2, 3, 3, 3, 4, 1, 1],
            [0, 2, 2, 3, 4, 4, 1, 1],
            [0, 5, 5, 6, 6, 1, 1, 1],
            [0, 5, 6, 6, 7, 7, 1, 1],
            [0, 5, 5, 6, 7, 7, 7, 1],
            [0, 0, 7, 7, 7, 7, 1, 1]
        ],
        "solution": [(0, 7), (1, 3), (2, 5), (3, 2), (4, 4), (5, 1), (6, 6), (7, 0)]
    }
}


def generate_board(n: int = 8) -> Tuple[List[List[int]], List[Tuple[int, int]]]:
    """Genera un tablero NxN con regiones conectadas y garantiza una solución única.
    Se intentan generar tableros (máximo 5 veces) y se verifica que no exista
    una solución alternativa diferente a la solución conocida. Si después de los
    intentos no se logra unicidad, se devuelve el último tablero generado.
    """
    n = max(4, min(12, n))
    max_attempts = 20
    for attempt in range(max_attempts):
        # 1. Encontrar una disposición válida de reinas (1 por fila, 1 por col, sin tocarse)
        queens: Optional[List[Tuple[int, int]]] = None
        for _ in range(10000):
            cols = list(range(n))
            random.shuffle(cols)
            valid = True
            for r1 in range(n):
                for r2 in range(r1 + 1, n):
                    if abs(r1 - r2) <= 1 and abs(cols[r1] - cols[r2]) <= 1:
                        valid = False
                        break
                if not valid:
                    break
            if valid:
                queens = [(r, cols[r]) for r in range(n)]
                break
        if not queens:
            queens = [(r, (r * 2 + 1) % n) for r in range(n)]
        # Reservar algunas regiones pequeñas y repartir el resto entre varios colores.
        small_count = random.randint(1, max(1, n // 3))
        small_regions = set(random.sample(range(n), k=small_count))
        region_sizes = [1] * n
        for reg in small_regions:
            region_sizes[reg] = random.choices(
                [1, 2, 3, 4], weights=[1, 2, 3, 3], k=1
            )[0]
        large_regions = [reg for reg in range(n) if reg not in small_regions]
        remaining = n * n - sum(region_sizes)
        for _ in range(remaining):
            region_sizes[random.choice(large_regions)] += 1

        # 3. Inicializar regiones en cada celda origen de reina
        grid = [[-1 for _ in range(n)] for _ in range(n)]
        frontiers: Dict[int, List[Tuple[int, int]]] = {i: [queens[i]] for i in range(n)}
        for i in range(n):
            r, c = queens[i]
            grid[r][c] = i
        region_counts = [1] * n

        # Algunas regiones pequeñas se reservan como segmentos de una fila o columna.
        line_regions: Set[int] = set()
        eligible = [
            reg for reg in small_regions if 2 <= region_sizes[reg] < n
        ]
        line_count = int(bool(eligible) and random.random() < 0.4)
        random.shuffle(eligible)
        for reg in eligible:
            if len(line_regions) >= line_count:
                break
            row, col = queens[reg]
            size = region_sizes[reg]
            options = []
            for start in range(max(0, col - size + 1), min(col, n - size) + 1):
                cells = [(row, c) for c in range(start, start + size)]
                if all(grid[r][c] in (-1, reg) for r, c in cells):
                    options.append(cells)
            for start in range(max(0, row - size + 1), min(row, n - size) + 1):
                cells = [(r, col) for r in range(start, start + size)]
                if all(grid[r][c] in (-1, reg) for r, c in cells):
                    options.append(cells)
            if options:
                for r, c in random.choice(options):
                    grid[r][c] = reg
                    region_counts[reg] += 1
                line_regions.add(reg)

        frontiers = {
            reg: [(r, c) for r in range(n) for c in range(n) if grid[r][c] == reg]
            for reg in range(n)
        }

        # 4. Crecimiento aleatorio con límites para favorecer tamaños pequeños
        unassigned = n * n - n
        unassigned -= sum(region_sizes[reg] - 1 for reg in line_regions)
        while unassigned > 0:
            active_regions = []
            for reg in range(n):
                if reg in line_regions:
                    continue
                if region_counts[reg] >= region_sizes[reg]:
                    continue
                cands = []
                for r, c in frontiers[reg]:
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < n and 0 <= nc < n and grid[nr][nc] == -1:
                            cands.append((nr, nc))
                if cands:
                    active_regions.append((reg, cands))
            if active_regions:
                reg, cands = random.choice(active_regions)
                nr, nc = random.choice(cands)
                grid[nr][nc] = reg
                frontiers[reg].append((nr, nc))
                region_counts[reg] += 1
                unassigned -= 1
            else:
                # Si las cuotas bloquean el crecimiento, completar regiones conectadas.
                fallback_regions = []
                for reg in range(n):
                    if reg in line_regions:
                        continue
                    cands = []
                    for r, c in frontiers[reg]:
                        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < n and 0 <= nc < n and grid[nr][nc] == -1:
                                cands.append((nr, nc))
                    if cands:
                        fallback_regions.append((reg, cands))
                if fallback_regions:
                    reg, cands = random.choice(fallback_regions)
                    nr, nc = random.choice(cands)
                    grid[nr][nc] = reg
                    frontiers[reg].append((nr, nc))
                    region_counts[reg] += 1
                    unassigned -= 1
                    continue
                for r in range(n):
                    for c in range(n):
                        if grid[r][c] == -1:
                            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                                nr, nc = r + dr, c + dc
                                if 0 <= nr < n and 0 <= nc < n and grid[nr][nc] != -1:
                                    grid[r][c] = grid[nr][nc]
                                    unassigned -= 1
                                    break
                break
        # 5. Verificar unicidad
        known_cols = [c for _, c in queens]
        if count_alternative_solutions(grid, known_cols, limit=2) == 0:
            return grid, queens
        # Could not guarantee uniqueness after attempts; returning last generated board

    return grid, queens

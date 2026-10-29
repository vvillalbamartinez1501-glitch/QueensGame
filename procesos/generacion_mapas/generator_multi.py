import random
import json
import time
from multiprocessing import Pool, cpu_count

# --- 1. GENERACIÓN DE REINAS VALIDADAS ---

def es_posicion_valida_reinas(queens, row, col):
    for r, c in enumerate(queens):
        if c == col or (abs(r - row) <= 1 and abs(c - col) <= 1):
            return False
    return True

def generar_posicion_reinas(size):
    queens = []
    def resolver(row):
        if row == size:
            return True
        cols = list(range(size))
        random.shuffle(cols)
        for col in cols:
            if es_posicion_valida_reinas(queens, row, col):
                queens.append(col)
                if resolver(row + 1):
                    return True
                queens.pop()
        return False

    if resolver(0):
        return [[r, queens[r]] for r in range(size)]
    return None

# --- 2. GENERACIÓN Y CONEXIDAD DE REGIONES ---

def generar_regiones_iniciales(size, queen_coords):
    grid = [[-1] * size for _ in range(size)]
    frontiers = [[] for _ in range(size)]

    for region_id, (r, c) in enumerate(queen_coords):
        grid[r][c] = region_id
        frontiers[region_id].append((r, c))

    unassigned = size * size - size

    while unassigned > 0:
        region_ids = [i for i in range(size) if frontiers[i]]
        if not region_ids:
            return None
        
        reg = random.choice(region_ids)
        r, c = random.choice(frontiers[reg])
        
        neighbors = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < size and 0 <= nc < size and grid[nr][nc] == -1:
                neighbors.append((nr, nc))

        if not neighbors:
            frontiers[reg].remove((r, c))
        else:
            nr, nc = random.choice(neighbors)
            grid[nr][nc] = reg
            frontiers[reg].append((nr, nc))
            unassigned -= 1

    return grid

def region_sigue_conectada(grid, size, r_remove, c_remove, region_id):
    """Verifica mediante BFS que una región siga siendo contigua si le quitamos una casilla."""
    cells = [(r, c) for r in range(size) for c in range(size) 
             if grid[r][c] == region_id and (r, c) != (r_remove, c_remove)]
    if not cells:
        return False
    
    visited = {cells[0]}
    queue = [cells[0]]
    while queue:
        curr_r, curr_c = queue.pop(0)
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = curr_r + dr, curr_c + dc
            if 0 <= nr < size and 0 <= nc < size:
                if (nr, nc) not in visited and grid[nr][nc] == region_id and (nr, nc) != (r_remove, c_remove):
                    visited.add((nr, nc))
                    queue.append((nr, nc))
                    
    return len(visited) == len(cells)

# --- 3. RESOLVEDOR ULTRA-RÁPIDO ---

def buscar_soluciones(grid, size, target_queens, max_limite=1):
    """Busca soluciones alternativas a target_queens."""
    soluciones = []
    target_tuple = tuple(c for r, c in target_queens)

    cols_usadas = [False] * size
    regiones_usadas = [False] * size

    def backtrack(r, current_queens):
        if len(soluciones) >= max_limite:
            return
        if r == size:
            sol_tuple = tuple(current_queens)
            if sol_tuple != target_tuple:
                soluciones.append([[row, col] for row, col in enumerate(current_queens)])
            return

        for c in range(size):
            reg = grid[r][c]
            if not cols_usadas[c] and not regiones_usadas[reg]:
                # Validación O(1) de adyacencia
                if r > 0 and abs(c - current_queens[-1]) <= 1:
                    continue
                cols_usadas[c] = True
                regiones_usadas[reg] = True

                backtrack(r + 1, current_queens + [c])

                cols_usadas[c] = False
                regiones_usadas[reg] = False

    backtrack(0, [])
    return soluciones

# --- 4. MUTACIÓN GUIADA DE REGIONES ---

def mutar_para_destruir_solucion(grid, size, target_queens, alt_queens):
    """Cambia el mapa para invalidar una solución alternativa sin romper la principal."""
    target_map = {r: c for r, c in target_queens}
    alt_map = {r: c for r, c in alt_queens}

    bad_cells = []
    for r in range(size):
        c_alt = alt_map[r]
        if c_alt != target_map[r]:
            bad_cells.append((r, c_alt))

    random.shuffle(bad_cells)

    for r, c in bad_cells:
        region_actual = grid[r][c]

        vecinos_regiones = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < size and 0 <= nc < size:
                reg_vecina = grid[nr][nc]
                if reg_vecina != region_actual:
                    vecinos_regiones.append(reg_vecina)

        random.shuffle(vecinos_regiones)

        for reg_nueva in vecinos_regiones:
            if region_sigue_conectada(grid, size, r, c, region_actual):
                grid[r][c] = reg_nueva
                return True

    return False

def generar_mapa_unico(size, max_mutaciones=60):
    """Genera un mapa garantizando solución única mediante mutación guiada."""
    queens = generar_posicion_reinas(size)
    if not queens:
        return None

    grid = generar_regiones_iniciales(size, queens)
    if not grid:
        return None

    for _ in range(max_mutaciones):
        alt_sols = buscar_soluciones(grid, size, target_queens=queens, max_limite=1)
        if not alt_sols:
            return {
                "regions": grid,
                "solution": queens
            }

        exito = mutar_para_destruir_solucion(grid, size, queens, alt_sols[0])
        if not exito:
            break

    return None

# --- 5. EJECUCIÓN PARALELA ---

def generar_categoria_paralelo(size, cantidad_deseada):
    mapas = []
    num_cores = cpu_count()
    print(f"\n[+] Generando {cantidad_deseada} mapas de {size}x{size} usando {num_cores} núcleos CPU...")

    with Pool(processes=num_cores) as pool:
        while len(mapas) < cantidad_deseada:
            lote = [size] * (num_cores * 4)
            resultados = pool.map(generar_mapa_unico, lote)

            for res in resultados:
                if res is not None and len(mapas) < cantidad_deseada:
                    mapas.append(res)

            print(f" -> Progreso {size}x{size}: {len(mapas)}/{cantidad_deseada} mapas listos...")

    return mapas

if __name__ == "__main__":
    # Configuración de prueba o masiva (ajusta los números a lo que necesites)
    CONFIGURACION = {
        "4": 200,
        "5": 200,
        "6": 200,
        "7": 1000,
        "8": 2000,
        "9": 2000,
        "10": 2000,
        "11": 2000,
        "12": 2000
    }

    inicio = time.time()
    base_datos_completa = {}

    for size_str, cantidad in CONFIGURACION.items():
        base_datos_completa[size_str] = generar_categoria_paralelo(int(size_str), cantidad)

    archivo_salida = "mapas_masivos.json"
    with open(archivo_salida, "w", encoding="utf-8") as f:
        json.dump(base_datos_completa, f, ensure_ascii=False)

    tiempo_total = round(time.time() - inicio, 2)
    print(f"\n==========================================")
    print(f"¡PROCESO COMPLETADO EN {tiempo_total} SEGUNDOS!")
    print(f"Generados {sum(len(v) for v in base_datos_completa.values())} mapas correctamente.")
    print(f"Archivo guardado como: {archivo_salida}")
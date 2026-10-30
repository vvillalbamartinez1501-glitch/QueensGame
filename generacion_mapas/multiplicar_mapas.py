import json

def rotate_matrix(matrix):
    """Gira una matriz 90 grados en sentido horario."""
    return [list(row) for row in zip(*matrix[::-1])]

def flip_matrix(matrix):
    """Invierte una matriz horizontalmente."""
    return [row[::-1] for row in matrix]

def coords_to_grid(size, solution):
    """Convierte lista de coordenadas [[r,c], ...] en matriz N x N."""
    grid = [[0] * size for _ in range(size)]
    for r, c in solution:
        grid[r][c] = 1
    return grid

def grid_to_coords(grid):
    """Convierte matriz N x N de vuelta a coordenadas [[r,c], ...]."""
    coords = []
    for r in range(len(grid)):
        for c in range(len(grid[r])):
            if grid[r][c] == 1:
                coords.append([r, c])
    return coords

def multiplicar_mapas(input_file="mapas.json", output_file="mapas_ampliados.json"):
    with open(input_file, "r") as f:
        data = json.load(f)

    nuevo_data = {}

    for size_str, map_list in data.items():
        size = int(size_str)
        mapas_unicos = set()
        lista_final = []

        for m in map_list:
            regions = m["regions"]
            solution_grid = coords_to_grid(size, m["solution"])

            # 8 transformaciones posibles (4 rotaciones x 2 reflejos)
            curr_reg = regions
            curr_sol = solution_grid

            for _ in range(2): # Normal y Volteado
                for _ in range(4): # 4 giros de 90 deg
                    # Serializar para detectar duplicados exactos
                    reg_tuple = tuple(tuple(r) for r in curr_reg)
                    if reg_tuple not in mapas_unicos:
                        mapas_unicos.add(reg_tuple)
                        lista_final.append({
                            "regions": curr_reg,
                            "solution": grid_to_coords(curr_sol)
                        })

                    curr_reg = rotate_matrix(curr_reg)
                    curr_sol = rotate_matrix(curr_sol)

                curr_reg = flip_matrix(curr_reg)
                curr_sol = flip_matrix(curr_sol)

        nuevo_data[size_str] = lista_final
        print(f"Tamaño {size}x{size}: pasado de {len(map_list)} a {len(lista_final)} mapas.")

    with open(output_file, "w") as f:
        json.dump(nuevo_data, f)

if __name__ == "__main__":
    multiplicar_mapas()
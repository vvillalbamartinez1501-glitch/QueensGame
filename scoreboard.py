"""
Módulo de gestión del marcador y tiempos récord (Scoreboard).
Guarda y carga los mejores tiempos persistidos en un archivo JSON local,
con registros independientes para cada tamaño de cuadrícula (4x4, 5x5, ..., 12x12).
"""

import os
import json
import time
from typing import Dict, List, Any


SCOREBOARD_FILE = "scoreboard.json"


class ScoreboardManager:
    """Administra la persistencia y consulta de tiempos por tamaño de cuadrícula."""

    def __init__(self, filename: str = SCOREBOARD_FILE):
        self.filename = filename
        self.data: Dict[str, List[Dict[str, Any]]] = self._load()

    def _load(self) -> Dict[str, List[Dict[str, Any]]]:
        """Carga los registros desde el archivo JSON si existe."""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save(self) -> None:
        """Guarda los registros actuales en el archivo JSON."""
        try:
            with open(self.filename, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error al guardar el marcador: {e}")

    def add_record(self, grid_size: int, elapsed_seconds: int, moves: int) -> int:
        """
        Registra una nueva victoria para el tamaño de cuadrícula dado.
        Ordena automáticamente por menor tiempo y retorna la posición obtenida (1-based).
        """
        key = f"{grid_size}x{grid_size}"
        if key not in self.data:
            self.data[key] = []

        mins, secs = divmod(elapsed_seconds, 60)
        record = {
            "time_seconds": elapsed_seconds,
            "time_formatted": f"{mins:02d}:{secs:02d}",
            "moves": moves,
            "date": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        self.data[key].append(record)
        # Ordenar por menor tiempo primero, luego por menor cantidad de movimientos
        self.data[key].sort(key=lambda r: (r["time_seconds"], r.get("moves", 9999)))

        self._save()

        # Calcular posición en el ranking (1-based)
        position = self.data[key].index(record) + 1
        return position

    def get_top_records(self, grid_size: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Retorna los mejores registros para un tamaño específico de tablero."""
        key = f"{grid_size}x{grid_size}"
        return self.data.get(key, [])[:limit]

    def get_all_records(self) -> Dict[str, List[Dict[str, Any]]]:
        """Retorna todos los registros agrupados por tamaño."""
        return self.data

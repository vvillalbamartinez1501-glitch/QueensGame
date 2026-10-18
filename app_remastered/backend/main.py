"""FastAPI service for Queens Remastered."""

from __future__ import annotations

import json
import random
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .logic import CellState, GameLogic


SCOREBOARD_PATH = Path(__file__).with_name("scoreboard.json")
GAME_RULES = {
    "objective": "Coloca una reina en cada fila, columna y región.",
    "constraints": [
        "Debe haber exactamente una reina por fila.",
        "Debe haber exactamente una reina por columna.",
        "Debe haber exactamente una reina por región.",
        "Dos reinas no pueden tocarse, ni ortogonal ni diagonalmente.",
    ],
    "controls": [
        "Toca una casilla para colocar o quitar una reina.",
        "Activa el modo Cruz para marcar o desmarcar casillas vacías.",
        "La pista coloca una reina que pertenece a una solución.",
    ],
}


class NewGameRequest(BaseModel):
    size: int = Field(default=8, ge=4, le=12)
    auto_cross: bool = True


class CellActionRequest(BaseModel):
    row: int = Field(ge=0)
    col: int = Field(ge=0)
    action: Literal["queen", "cross"]


class AutoCrossRequest(BaseModel):
    enabled: bool


class ValidationResponse(BaseModel):
    is_valid: bool
    message: str
    error_type: str
    error_cells: list[list[int]]


class Record(BaseModel):
    time_seconds: int
    time_formatted: str
    moves: int
    date: str


class GameResponse(BaseModel):
    game_id: str
    size: int
    regions: list[list[int]]
    board: list[list[int]]
    queen_count: int
    move_count: int
    elapsed_seconds: int
    timer_running: bool
    auto_cross: bool
    is_won: bool
    last_message: str
    validation: ValidationResponse | None = None
    rank_position: int | None = None


class HintResponse(BaseModel):
    game: GameResponse
    message: str


@dataclass
class GameSession:
    logic: GameLogic
    auto_cross: bool
    game_id: str
    elapsed_seconds: int = 0
    started_at: float | None = None
    is_won: bool = False
    last_message: str = "¡Encuentra la solución!"
    rank_position: int | None = None

    def elapsed(self) -> int:
        if self.started_at is None:
            return self.elapsed_seconds
        return int(time.monotonic() - self.started_at)

    def start_timer(self) -> None:
        if self.started_at is None and not self.is_won:
            self.started_at = time.monotonic() - self.elapsed_seconds

    def stop_timer(self) -> None:
        if self.started_at is not None:
            self.elapsed_seconds = self.elapsed()
            self.started_at = None


class ScoreboardManager:
    """Maintains per-board records in this remastered app's private data file."""

    def __init__(self, filename: Path) -> None:
        self.filename = filename
        if filename.exists():
            loaded = json.loads(filename.read_text(encoding="utf-8"))
            if not isinstance(loaded, dict):
                raise ValueError("El archivo del marcador debe contener un objeto JSON.")
            self.data: dict[str, list[dict[str, object]]] = loaded
        else:
            self.data = {}
        self._lock = threading.Lock()

    def add_record(self, grid_size: int, elapsed_seconds: int, moves: int) -> int:
        key = f"{grid_size}x{grid_size}"
        mins, secs = divmod(elapsed_seconds, 60)
        record: dict[str, object] = {
            "time_seconds": elapsed_seconds,
            "time_formatted": f"{mins:02d}:{secs:02d}",
            "moves": moves,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        with self._lock:
            records = self.data.setdefault(key, [])
            records.append(record)
            records.sort(
                key=lambda item: (
                    int(item["time_seconds"]),
                    int(item.get("moves", 9999)),
                )
            )
            self.filename.write_text(
                json.dumps(self.data, indent=4, ensure_ascii=False),
                encoding="utf-8",
            )
            return records.index(record) + 1

    def top_records(self, grid_size: int, limit: int = 10) -> list[dict[str, object]]:
        with self._lock:
            return list(self.data.get(f"{grid_size}x{grid_size}", []))[:limit]

    def all_records(self) -> dict[str, list[dict[str, object]]]:
        with self._lock:
            return {key: list(records) for key, records in self.data.items()}


app = FastAPI(
    title="Queens Remastered API",
    description="Motor de reglas, niveles y récords para el juego Queens.",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "OPTIONS"],
    allow_headers=["*"],
)

scoreboard = ScoreboardManager(SCOREBOARD_PATH)
games: dict[str, GameSession] = {}
games_lock = threading.RLock()


def get_session(game_id: str) -> GameSession:
    session = games.get(game_id)
    if session is None:
        raise HTTPException(status_code=404, detail="No se encontró la partida.")
    return session


def serialize_validation(session: GameSession) -> ValidationResponse:
    result = session.logic.validate_solution()
    return ValidationResponse(
        is_valid=result.is_valid,
        message=result.message,
        error_type=result.error_type,
        error_cells=[[row, col] for row, col in sorted(result.error_cells)],
    )


def maybe_finish_game(session: GameSession) -> None:
    if session.is_won or session.logic.count_queens() != session.logic.size:
        return
    result = session.logic.validate_solution()
    if not result.is_valid:
        return
    session.is_won = True
    session.stop_timer()
    session.rank_position = scoreboard.add_record(
        session.logic.size, session.elapsed_seconds, session.logic.move_count
    )
    session.last_message = (
        f"¡Victoria! Récord #{session.rank_position} "
        f"en el tablero {session.logic.size}x{session.logic.size}."
    )


def serialize_game(session: GameSession) -> GameResponse:
    validation = serialize_validation(session) if session.is_won else None
    return GameResponse(
        game_id=session.game_id,
        size=session.logic.size,
        regions=session.logic.regions,
        board=[[cell.value for cell in row] for row in session.logic.board],
        queen_count=session.logic.count_queens(),
        move_count=session.logic.move_count,
        elapsed_seconds=session.elapsed(),
        timer_running=session.started_at is not None,
        auto_cross=session.auto_cross,
        is_won=session.is_won,
        last_message=session.last_message,
        validation=validation,
        rank_position=session.rank_position,
    )


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/rules")
def get_rules() -> dict[str, object]:
    return GAME_RULES


@app.post("/api/games", response_model=GameResponse)
def create_game(request: NewGameRequest) -> GameResponse:
    logic = GameLogic(size=request.size)
    session = GameSession(
        logic=logic,
        auto_cross=request.auto_cross,
        game_id=str(uuid.uuid4()),
    )
    logic.auto_cross_enabled = request.auto_cross
    with games_lock:
        games[session.game_id] = session
    return serialize_game(session)


@app.get("/api/games/{game_id}", response_model=GameResponse)
def get_game(game_id: str) -> GameResponse:
    with games_lock:
        return serialize_game(get_session(game_id))


@app.post("/api/games/{game_id}/cells", response_model=GameResponse)
def update_cell(game_id: str, request: CellActionRequest) -> GameResponse:
    with games_lock:
        session = get_session(game_id)
        logic = session.logic
        if session.is_won:
            raise HTTPException(status_code=409, detail="La partida ya está completada.")
        if request.row >= logic.size or request.col >= logic.size:
            raise HTTPException(status_code=422, detail="La casilla está fuera del tablero.")
        if request.action == "queen":
            old_state = logic.board[request.row][request.col]
            new_state = CellState.EMPTY if old_state == CellState.QUEEN else CellState.QUEEN
            logic.set_cell(request.row, request.col, new_state)
        else:
            logic.toggle_cross(request.row, request.col)
        if logic.move_count:
            session.start_timer()
        maybe_finish_game(session)
        return serialize_game(session)


@app.post("/api/games/{game_id}/undo", response_model=GameResponse)
def undo_move(game_id: str) -> GameResponse:
    with games_lock:
        session = get_session(game_id)
        if session.is_won:
            raise HTTPException(status_code=409, detail="La partida ya está completada.")
        if session.logic.undo():
            session.last_message = "Movimiento deshecho."
        else:
            session.last_message = "No hay movimientos para deshacer."
        return serialize_game(session)


@app.post("/api/games/{game_id}/reset", response_model=GameResponse)
def reset_game(game_id: str) -> GameResponse:
    with games_lock:
        session = get_session(game_id)
        session.logic.reset()
        session.is_won = False
        session.rank_position = None
        session.elapsed_seconds = 0
        session.started_at = None
        session.last_message = "Tablero reiniciado. ¡Buena suerte!"
        return serialize_game(session)


@app.put("/api/games/{game_id}/settings/auto-cross", response_model=GameResponse)
def update_auto_cross(game_id: str, request: AutoCrossRequest) -> GameResponse:
    with games_lock:
        session = get_session(game_id)
        session.auto_cross = request.enabled
        session.logic.auto_cross_enabled = request.enabled
        return serialize_game(session)


@app.post("/api/games/{game_id}/hint", response_model=HintResponse)
def give_hint(game_id: str) -> HintResponse:
    with games_lock:
        session = get_session(game_id)
        if session.is_won:
            raise HTTPException(status_code=409, detail="La partida ya está completada.")
        solution = session.logic.solve()
        if not solution:
            raise HTTPException(
                status_code=409,
                detail="No se encontró solución para esta configuración.",
            )
        queens = set(session.logic.get_queens())
        missing = [position for position in solution if position not in queens]
        if missing:
            row, col = random.choice(missing)
            session.logic.set_cell(row, col, CellState.QUEEN)
            session.start_timer()
            session.last_message = (
                f"Pista: reina en la fila {row + 1}, columna {col + 1}."
            )
            maybe_finish_game(session)
            message = session.last_message
        else:
            message = "Todas las reinas de esta solución ya están colocadas."
            session.last_message = message
        return HintResponse(game=serialize_game(session), message=message)


@app.post(
    "/api/games/{game_id}/validate",
    response_model=ValidationResponse,
)
def validate_game(game_id: str) -> ValidationResponse:
    with games_lock:
        return serialize_validation(get_session(game_id))


@app.get("/api/scoreboard")
def get_scoreboard(
    size: int | None = Query(default=None, ge=4, le=12),
) -> dict[str, object]:
    if size is not None:
        return {
            "size": size,
            "records": scoreboard.top_records(size),
        }
    return {"records": scoreboard.all_records()}


@app.get("/api/scoreboard/{size}", response_model=list[Record])
def get_size_scoreboard(size: int) -> list[Record]:
    if not 4 <= size <= 12:
        raise HTTPException(status_code=422, detail="El tamaño debe estar entre 4 y 12.")
    return scoreboard.top_records(size)

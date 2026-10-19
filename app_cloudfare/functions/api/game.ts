import puzzleBank from "../../puzzles.json";
import type {
  Env,
  GameResponse,
  GameState,
  RecordEntry,
  Validation,
} from "./types";

const rules = {
  objective: "Coloca una reina en cada fila, columna y región.",
  constraints: [
    "Debe haber exactamente una reina por fila.",
    "Debe haber exactamente una reina por columna.",
    "Debe haber exactamente una reina por región.",
    "Dos reinas no pueden tocarse, ni ortogonal ni diagonalmente.",
  ],
  controls: [
    "Toca una casilla para colocar o quitar una reina.",
    "Activa el modo Cruz para marcar o desmarcar casillas vacías.",
    "La pista coloca una reina que pertenece a una solución.",
  ],
};

type Puzzle = { regions: number[][]; solution: number[][] };
const puzzles = puzzleBank as Record<string, Puzzle[]>;

type Change = [row: number, col: number, oldState: number, newState: number];

function fail(status: number, detail: string): Response {
  return Response.json({ detail }, { status });
}

function elapsedSeconds(game: GameState, now = Date.now()): number {
  return game.started_at_ms === null
    ? game.elapsed_seconds
    : Math.floor((now - game.started_at_ms) / 1000);
}

function queenCells(game: GameState): number[][] {
  const queens: number[][] = [];
  for (let row = 0; row < game.size; row++) {
    for (let col = 0; col < game.size; col++) {
      if (game.board[row][col] === 1) queens.push([row, col]);
    }
  }
  return queens;
}

function validate(game: GameState): Validation {
  const queens = queenCells(game);
  if (queens.length < game.size) {
    return {
      is_valid: false,
      message: `Faltan reinas por colocar (${queens.length}/${game.size}).`,
      error_type: "count",
      error_cells: [],
    };
  }
  if (queens.length > game.size) {
    return {
      is_valid: false,
      message: `Hay demasiadas reinas (${queens.length}/${game.size}).`,
      error_type: "count",
      error_cells: [],
    };
  }

  const touching = new Map<string, number[]>();
  for (let first = 0; first < queens.length; first++) {
    for (let second = first + 1; second < queens.length; second++) {
      const [r1, c1] = queens[first];
      const [r2, c2] = queens[second];
      if (Math.abs(r1 - r2) <= 1 && Math.abs(c1 - c2) <= 1) {
        touching.set(`${r1},${c1}`, [r1, c1]);
        touching.set(`${r2},${c2}`, [r2, c2]);
      }
    }
  }
  if (touching.size > 0) {
    return {
      is_valid: false,
      message:
        "¡Hay reinas que se tocan! No pueden ser adyacentes (ni ortogonal ni diagonalmente).",
      error_type: "touching",
      error_cells: [...touching.values()].sort(compareCells),
    };
  }

  for (let row = 0; row < game.size; row++) {
    const rowQueens = queens.filter(([queenRow]) => queenRow === row);
    if (rowQueens.length > 1) {
      return {
        is_valid: false,
        message: `Conflicto en la Fila ${row + 1}: contiene ${rowQueens.length} reinas.`,
        error_type: "row",
        error_cells: rowQueens.sort(compareCells),
      };
    }
  }

  for (let col = 0; col < game.size; col++) {
    const colQueens = queens.filter(([, queenCol]) => queenCol === col);
    if (colQueens.length > 1) {
      return {
        is_valid: false,
        message: `Conflicto en la Columna ${col + 1}: contiene ${colQueens.length} reinas.`,
        error_type: "col",
        error_cells: colQueens.sort(compareCells),
      };
    }
  }

  const regions = [...new Set(game.regions.flat())].sort((a, b) => a - b);
  for (const region of regions) {
    const regionQueens = queens.filter(
      ([row, col]) => game.regions[row][col] === region,
    );
    if (regionQueens.length > 1) {
      return {
        is_valid: false,
        message: `Conflicto en la Región #${region + 1}: contiene ${regionQueens.length} reinas.`,
        error_type: "region",
        error_cells: regionQueens.sort(compareCells),
      };
    }
  }

  return {
    is_valid: true,
    message: "¡ENHORABUENA! ¡Has resuelto el puzzle perfectamente!",
    error_type: "ok",
    error_cells: [],
  };
}

function compareCells(left: number[], right: number[]): number {
  return left[0] - right[0] || left[1] - right[1];
}

function blockedCells(game: GameState, row: number, col: number): number[][] {
  const blocked = new Map<string, number[]>();
  const region = game.regions[row][col];
  for (let index = 0; index < game.size; index++) {
    if (index !== col) blocked.set(`${row},${index}`, [row, index]);
    if (index !== row) blocked.set(`${index},${col}`, [index, col]);
  }
  for (let otherRow = 0; otherRow < game.size; otherRow++) {
    for (let otherCol = 0; otherCol < game.size; otherCol++) {
      if (
        (otherRow !== row || otherCol !== col) &&
        game.regions[otherRow][otherCol] === region
      ) {
        blocked.set(`${otherRow},${otherCol}`, [otherRow, otherCol]);
      }
    }
  }
  for (let rowOffset = -1; rowOffset <= 1; rowOffset++) {
    for (let colOffset = -1; colOffset <= 1; colOffset++) {
      const nextRow = row + rowOffset;
      const nextCol = col + colOffset;
      if (
        (rowOffset !== 0 || colOffset !== 0) &&
        nextRow >= 0 &&
        nextRow < game.size &&
        nextCol >= 0 &&
        nextCol < game.size
      ) {
        blocked.set(`${nextRow},${nextCol}`, [nextRow, nextCol]);
      }
    }
  }
  return [...blocked.values()];
}

function setCell(
  game: GameState,
  row: number,
  col: number,
  state: number,
): void {
  const oldState = game.board[row][col];
  if (oldState === state) return;
  const batch: Change[] = [[row, col, oldState, state]];
  game.board[row][col] = state;
  if (state === 1 && game.auto_cross) {
    for (const [blockedRow, blockedCol] of blockedCells(game, row, col)) {
      if (game.board[blockedRow][blockedCol] === 0) {
        game.board[blockedRow][blockedCol] = 2;
        batch.push([blockedRow, blockedCol, 0, 2]);
      }
    }
  }
  game.history.push(batch);
  game.move_count++;
}

function toggleCross(game: GameState, row: number, col: number): void {
  const oldState = game.board[row][col];
  const newState = oldState === 2 ? 0 : 2;
  game.board[row][col] = newState;
  game.history.push([[row, col, oldState, newState]]);
  game.move_count++;
}

function undo(game: GameState): boolean {
  const batch = game.history.pop();
  if (!batch) return false;
  for (const [row, col, oldState] of [...batch].reverse()) {
    game.board[row][col] = oldState;
  }
  game.move_count = Math.max(0, game.move_count - 1);
  return true;
}

function reset(game: GameState): void {
  game.board = Array.from({ length: game.size }, () =>
    Array.from({ length: game.size }, () => 0),
  );
  game.history = [];
  game.move_count = 0;
}

function startTimer(game: GameState): void {
  if (game.started_at_ms === null && !game.is_won) {
    game.started_at_ms = Date.now() - game.elapsed_seconds * 1000;
  }
}

function serializeGame(game: GameState): GameResponse {
  return {
    game_id: game.game_id,
    size: game.size,
    regions: game.regions,
    board: game.board,
    queen_count: queenCells(game).length,
    move_count: game.move_count,
    elapsed_seconds: elapsedSeconds(game),
    timer_running: game.started_at_ms !== null,
    auto_cross: game.auto_cross,
    is_won: game.is_won,
    last_message: game.last_message,
    validation: game.is_won ? validate(game) : null,
    rank_position: game.rank_position,
  };
}

async function loadGame(env: Env, gameId: string): Promise<GameState | null> {
  const row = await env.DB.prepare(
    "SELECT data_json FROM games WHERE game_id = ?",
  )
    .bind(gameId)
    .first<{ data_json: string }>();
  if (!row) return null;
  const game = JSON.parse(row.data_json) as GameState;
  if (!Array.isArray(game.board) || !Array.isArray(game.regions)) {
    throw new Error(`Stored game ${gameId} has invalid state.`);
  }
  return game;
}

async function saveGame(env: Env, game: GameState): Promise<void> {
  await env.DB.prepare(
    `INSERT INTO games (game_id, data_json, updated_at)
     VALUES (?, ?, CURRENT_TIMESTAMP)
     ON CONFLICT(game_id) DO UPDATE SET
       data_json = excluded.data_json,
       updated_at = CURRENT_TIMESTAMP`,
  )
    .bind(game.game_id, JSON.stringify(game))
    .run();
}

async function addRecord(env: Env, game: GameState): Promise<number> {
  const seconds = game.elapsed_seconds;
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  const formatted = `${String(minutes).padStart(2, "0")}:${String(remainingSeconds).padStart(2, "0")}`;
  const date = new Date().toISOString().replace("T", " ").slice(0, 19);
  const result = await env.DB.prepare(
    `INSERT INTO records
       (grid_size, time_seconds, time_formatted, moves, date)
     VALUES (?, ?, ?, ?, ?)`,
  )
    .bind(game.size, seconds, formatted, game.move_count, date)
    .run();
  const recordId = Number(result.meta.last_row_id);
  const rank = await env.DB.prepare(
    `SELECT COUNT(*) AS rank
     FROM records
     WHERE grid_size = ?
       AND (
         time_seconds < ?
         OR (time_seconds = ? AND moves < ?)
         OR (time_seconds = ? AND moves = ? AND id <= ?)
       )`,
  )
    .bind(
      game.size,
      seconds,
      seconds,
      game.move_count,
      seconds,
      game.move_count,
      recordId,
    )
    .first<{ rank: number }>();
  return Number(rank?.rank ?? 1);
}

async function maybeFinishGame(env: Env, game: GameState): Promise<void> {
  if (game.is_won || queenCells(game).length !== game.size) return;
  if (!validate(game).is_valid) return;
  game.is_won = true;
  game.elapsed_seconds = elapsedSeconds(game);
  game.started_at_ms = null;
  game.rank_position = await addRecord(env, game);
  game.last_message =
    `¡Victoria! Récord #${game.rank_position} en el tablero ${game.size}x${game.size}.`;
}

function recordFromRow(row: Record<string, unknown>): RecordEntry {
  return {
    time_seconds: Number(row.time_seconds),
    time_formatted: String(row.time_formatted),
    moves: Number(row.moves),
    date: String(row.date),
  };
}

async function topRecords(env: Env, size: number): Promise<RecordEntry[]> {
  const { results } = await env.DB.prepare(
    `SELECT time_seconds, time_formatted, moves, date
     FROM records
     WHERE grid_size = ?
     ORDER BY time_seconds ASC, moves ASC, id ASC
     LIMIT 10`,
  )
    .bind(size)
    .all<Record<string, unknown>>();
  return results.map(recordFromRow);
}

async function allRecords(
  env: Env,
): Promise<Record<string, RecordEntry[]>> {
  const { results } = await env.DB.prepare(
    `SELECT grid_size, time_seconds, time_formatted, moves, date
     FROM records
     ORDER BY grid_size ASC, time_seconds ASC, moves ASC, id ASC`,
  ).all<Record<string, unknown>>();
  const records: Record<string, RecordEntry[]> = {};
  for (const row of results) {
    const key = `${row.grid_size}x${row.grid_size}`;
    (records[key] ??= []).push(recordFromRow(row));
  }
  return records;
}

function validSize(value: unknown): value is number {
  return (
    typeof value === "number" &&
    Number.isInteger(value) &&
    value >= 4 &&
    value <= 12
  );
}

function parseJsonBody(request: Request): Promise<unknown> {
  return request.json().catch(() => {
    throw new HttpError(422, "El cuerpo de la solicitud debe ser JSON válido.");
  });
}

export class HttpError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
  }
}

function gameNotFound(): HttpError {
  return new HttpError(404, "No se encontró la partida.");
}

function parsePath(url: URL): string[] {
  return url.pathname.split("/").filter(Boolean).map(decodeURIComponent);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export async function handleApiRequest(
  request: Request,
  env: Env,
): Promise<Response> {
  const url = new URL(request.url);
  const path = parsePath(url);
  const method = request.method.toUpperCase();

  if (method === "OPTIONS") return new Response(null, { status: 204 });
  if (path[0] !== "api") return fail(404, "Not Found");
  if (method === "GET" && path.join("/") === "api/health") {
    return Response.json({ status: "ok" });
  }
  if (method === "GET" && path.join("/") === "api/rules") {
    return Response.json(rules);
  }

  if (path.length === 2 && path[1] === "games" && method === "POST") {
    const body = await parseJsonBody(request);
    if (!isRecord(body)) throw new HttpError(422, "El cuerpo debe ser un objeto.");
    const size = body.size === undefined ? 8 : body.size;
    const autoCross =
      body.auto_cross === undefined ? true : body.auto_cross;
    if (!validSize(size)) {
      throw new HttpError(422, "El tamaño debe estar entre 4 y 12.");
    }
    if (typeof autoCross !== "boolean") {
      throw new HttpError(422, "auto_cross debe ser un valor booleano.");
    }
    const options = puzzles[String(size)];
    if (!options || options.length === 0) {
      throw new Error(`No precomputed puzzles exist for size ${size}.`);
    }
    const puzzle = options[Math.floor(Math.random() * options.length)];
    const game: GameState = {
      game_id: crypto.randomUUID(),
      size,
      regions: puzzle.regions.map((row) => [...row]),
      board: Array.from({ length: size }, () =>
        Array.from({ length: size }, () => 0),
      ),
      history: [],
      solution: puzzle.solution.map((cell) => [...cell]),
      move_count: 0,
      elapsed_seconds: 0,
      started_at_ms: null,
      auto_cross: autoCross,
      is_won: false,
      last_message: "¡Encuentra la solución!",
      rank_position: null,
    };
    await saveGame(env, game);
    return Response.json(serializeGame(game));
  }

  if (path[1] === "scoreboard" && method === "GET") {
    const querySize = url.searchParams.get("size");
    if (querySize !== null) {
      const size = Number(querySize);
      if (!validSize(size)) {
        throw new HttpError(422, "El tamaño debe estar entre 4 y 12.");
      }
      return Response.json({ size, records: await topRecords(env, size) });
    }
    if (path.length === 3) {
      const size = Number(path[2]);
      if (!validSize(size)) {
        throw new HttpError(422, "El tamaño debe estar entre 4 y 12.");
      }
      return Response.json(await topRecords(env, size));
    }
    if (path.length === 2) {
      return Response.json({ records: await allRecords(env) });
    }
  }

  if (path[1] !== "games" || path.length < 3) {
    throw new HttpError(404, "Not Found");
  }

  const gameId = path[2];
  const game = await loadGame(env, gameId);
  if (!game) throw gameNotFound();

  if (path.length === 3 && method === "GET") {
    return Response.json(serializeGame(game));
  }

  if (path.length === 4 && path[3] === "cells" && method === "POST") {
    if (game.is_won) {
      throw new HttpError(409, "La partida ya está completada.");
    }
    const body = await parseJsonBody(request);
    if (!isRecord(body)) throw new HttpError(422, "El cuerpo debe ser un objeto.");
    const { row, col, action } = body;
    if (
      typeof row !== "number" ||
      !Number.isInteger(row) ||
      row < 0 ||
      typeof col !== "number" ||
      !Number.isInteger(col) ||
      col < 0 ||
      (action !== "queen" && action !== "cross")
    ) {
      throw new HttpError(422, "Los datos de la casilla no son válidos.");
    }
    const cellRow = row;
    const cellCol = col;
    if (cellRow >= game.size || cellCol >= game.size) {
      throw new HttpError(422, "La casilla está fuera del tablero.");
    }
    if (action === "queen") {
      const oldState = game.board[cellRow][cellCol];
      setCell(game, cellRow, cellCol, oldState === 1 ? 0 : 1);
    } else {
      toggleCross(game, cellRow, cellCol);
    }
    if (game.move_count > 0) startTimer(game);
    await maybeFinishGame(env, game);
    await saveGame(env, game);
    return Response.json(serializeGame(game));
  }

  if (path.length === 4 && path[3] === "undo" && method === "POST") {
    if (game.is_won) {
      throw new HttpError(409, "La partida ya está completada.");
    }
    game.last_message = undo(game)
      ? "Movimiento deshecho."
      : "No hay movimientos para deshacer.";
    await saveGame(env, game);
    return Response.json(serializeGame(game));
  }

  if (path.length === 4 && path[3] === "reset" && method === "POST") {
    reset(game);
    game.is_won = false;
    game.rank_position = null;
    game.elapsed_seconds = 0;
    game.started_at_ms = null;
    game.last_message = "Tablero reiniciado. ¡Buena suerte!";
    await saveGame(env, game);
    return Response.json(serializeGame(game));
  }

  if (
    path.length === 5 &&
    path[3] === "settings" &&
    path[4] === "auto-cross" &&
    method === "PUT"
  ) {
    const body = await parseJsonBody(request);
    if (!isRecord(body) || typeof body.enabled !== "boolean") {
      throw new HttpError(422, "enabled debe ser un valor booleano.");
    }
    game.auto_cross = body.enabled;
    await saveGame(env, game);
    return Response.json(serializeGame(game));
  }

  if (path.length === 4 && path[3] === "hint" && method === "POST") {
    if (game.is_won) {
      throw new HttpError(409, "La partida ya está completada.");
    }
    const queens = new Set(queenCells(game).map(([row, col]) => `${row},${col}`));
    const missing = game.solution.filter(
      ([row, col]) => !queens.has(`${row},${col}`),
    );
    let message: string;
    if (missing.length > 0) {
      const [row, col] = missing[Math.floor(Math.random() * missing.length)];
      setCell(game, row, col, 1);
      startTimer(game);
      game.last_message = `Pista: reina en la fila ${row + 1}, columna ${col + 1}.`;
      await maybeFinishGame(env, game);
      message = game.last_message;
    } else {
      message = "Todas las reinas de esta solución ya están colocadas.";
      game.last_message = message;
    }
    await saveGame(env, game);
    return Response.json({ game: serializeGame(game), message });
  }

  if (
    path.length === 4 &&
    path[3] === "validate" &&
    method === "POST"
  ) {
    return Response.json(validate(game));
  }

  throw new HttpError(404, "Not Found");
}

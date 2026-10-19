export interface Env {
  DB: D1Database;
}

export interface Validation {
  is_valid: boolean;
  message: string;
  error_type: "ok" | "count" | "row" | "col" | "region" | "touching";
  error_cells: number[][];
}

export interface RecordEntry {
  time_seconds: number;
  time_formatted: string;
  moves: number;
  date: string;
}

export interface GameState {
  game_id: string;
  size: number;
  regions: number[][];
  board: number[][];
  history: number[][][];
  solution: number[][];
  move_count: number;
  elapsed_seconds: number;
  started_at_ms: number | null;
  auto_cross: boolean;
  is_won: boolean;
  last_message: string;
  rank_position: number | null;
}

export interface GameResponse {
  game_id: string;
  size: number;
  regions: number[][];
  board: number[][];
  queen_count: number;
  move_count: number;
  elapsed_seconds: number;
  timer_running: boolean;
  auto_cross: boolean;
  is_won: boolean;
  last_message: string;
  validation: Validation | null;
  rank_position: number | null;
}

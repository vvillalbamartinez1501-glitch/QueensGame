CREATE TABLE IF NOT EXISTS games (
  game_id TEXT PRIMARY KEY,
  data_json TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  grid_size INTEGER NOT NULL CHECK (grid_size BETWEEN 4 AND 12),
  time_seconds INTEGER NOT NULL CHECK (time_seconds >= 0),
  time_formatted TEXT NOT NULL,
  moves INTEGER NOT NULL CHECK (moves >= 0),
  date TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS records_ranking
  ON records (grid_size, time_seconds, moves, id);

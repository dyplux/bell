CREATE TABLE IF NOT EXISTS dossiers (
  slug TEXT PRIMARY KEY,
  payload_json TEXT NOT NULL,
  observed_at TEXT,
  published_at TEXT NOT NULL,
  stale_after_seconds INTEGER NOT NULL DEFAULT 3600,
  receipt_url TEXT,
  status TEXT NOT NULL DEFAULT 'published'
);

CREATE INDEX IF NOT EXISTS dossiers_published_at_idx ON dossiers(published_at);

CREATE TABLE IF NOT EXISTS refresh_jobs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  slug TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'queued',
  requested_at TEXT NOT NULL,
  leased_at TEXT,
  finished_at TEXT,
  error TEXT
);

CREATE INDEX IF NOT EXISTS refresh_jobs_queue_idx ON refresh_jobs(status, requested_at);
CREATE INDEX IF NOT EXISTS refresh_jobs_slug_idx ON refresh_jobs(slug, status, requested_at);

CREATE TABLE IF NOT EXISTS integrity_receipts (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  payload_json TEXT NOT NULL,
  observed_at TEXT,
  published_at TEXT NOT NULL,
  stale_after_seconds INTEGER NOT NULL DEFAULT 900,
  status TEXT NOT NULL DEFAULT 'published'
);

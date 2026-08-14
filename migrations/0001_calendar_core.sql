CREATE TABLE IF NOT EXISTS marker_types (
    marker_id INTEGER PRIMARY KEY CHECK (marker_id BETWEEN 1 AND 5),
    title TEXT NOT NULL CHECK (length(trim(title)) BETWEEN 1 AND 80),
    short_title TEXT NOT NULL CHECK (length(trim(short_title)) BETWEEN 1 AND 12),
    color TEXT NOT NULL CHECK (substr(color, 1, 1) = '#'),
    symbol TEXT NOT NULL CHECK (length(trim(symbol)) BETWEEN 1 AND 8),
    description TEXT NOT NULL DEFAULT '',
    enabled INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0, 1)),
    sort_order INTEGER NOT NULL UNIQUE CHECK (sort_order BETWEEN 1 AND 5)
);

CREATE TABLE IF NOT EXISTS calendar_events (
    event_id TEXT PRIMARY KEY,
    title TEXT NOT NULL CHECK (length(trim(title)) BETWEEN 1 AND 200),
    description TEXT NOT NULL DEFAULT '',
    start_at TEXT NOT NULL,
    end_at TEXT,
    timezone TEXT NOT NULL CHECK (length(trim(timezone)) > 0),
    all_day INTEGER NOT NULL DEFAULT 0 CHECK (all_day IN (0, 1)),
    marker_id INTEGER REFERENCES marker_types(marker_id) ON UPDATE CASCADE ON DELETE SET NULL,
    status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'CANCELLED')),
    version INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deleted_at TEXT,
    CHECK (end_at IS NULL OR end_at >= start_at)
);

CREATE INDEX IF NOT EXISTS idx_calendar_events_start ON calendar_events(start_at);
CREATE INDEX IF NOT EXISTS idx_calendar_events_range ON calendar_events(start_at, end_at);
CREATE INDEX IF NOT EXISTS idx_calendar_events_deleted ON calendar_events(deleted_at);
CREATE INDEX IF NOT EXISTS idx_calendar_events_marker ON calendar_events(marker_id);

INSERT OR IGNORE INTO marker_types(marker_id, title, short_title, color, symbol, description, enabled, sort_order) VALUES
(1, 'Markierung 1', 'M1', '#C62828', '1', 'Frei anpassbare Markierung 1', 1, 1),
(2, 'Markierung 2', 'M2', '#1565C0', '2', 'Frei anpassbare Markierung 2', 1, 2),
(3, 'Markierung 3', 'M3', '#2E7D32', '3', 'Frei anpassbare Markierung 3', 1, 3),
(4, 'Markierung 4', 'M4', '#6A1B9A', '4', 'Frei anpassbare Markierung 4', 1, 4),
(5, 'Markierung 5', 'M5', '#EF6C00', '5', 'Frei anpassbare Markierung 5', 1, 5);

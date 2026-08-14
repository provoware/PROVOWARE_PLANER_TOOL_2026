CREATE TABLE IF NOT EXISTS todos (
    todo_id TEXT PRIMARY KEY,
    title TEXT NOT NULL CHECK (length(trim(title)) BETWEEN 1 AND 200),
    description TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'OPEN' CHECK (status IN ('OPEN', 'IN_PROGRESS', 'WAITING', 'DONE', 'CANCELLED')),
    priority TEXT NOT NULL DEFAULT 'NORMAL' CHECK (priority IN ('LOW', 'NORMAL', 'HIGH', 'URGENT')),
    progress INTEGER NOT NULL DEFAULT 0 CHECK (progress BETWEEN 0 AND 100),
    start_at TEXT,
    due_at TEXT,
    parent_id TEXT REFERENCES todos(todo_id) ON UPDATE CASCADE ON DELETE SET NULL,
    version INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deleted_at TEXT,
    CHECK (start_at IS NULL OR due_at IS NULL OR due_at >= start_at),
    CHECK (status <> 'DONE' OR progress = 100)
);

CREATE INDEX IF NOT EXISTS idx_todos_status ON todos(status);
CREATE INDEX IF NOT EXISTS idx_todos_priority ON todos(priority);
CREATE INDEX IF NOT EXISTS idx_todos_due ON todos(due_at);
CREATE INDEX IF NOT EXISTS idx_todos_parent ON todos(parent_id);
CREATE INDEX IF NOT EXISTS idx_todos_deleted ON todos(deleted_at);

CREATE TABLE IF NOT EXISTS todo_calendar_links (
    link_id TEXT PRIMARY KEY,
    todo_id TEXT NOT NULL REFERENCES todos(todo_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    event_id TEXT NOT NULL REFERENCES calendar_events(event_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    direction TEXT NOT NULL CHECK (direction IN ('TODO_TO_CALENDAR', 'CALENDAR_TO_TODO', 'BIDIRECTIONAL', 'MANUAL')),
    conflict_status TEXT NOT NULL DEFAULT 'CLEAN' CHECK (conflict_status IN ('CLEAN', 'TODO_CHANGED', 'CALENDAR_CHANGED', 'BOTH_CHANGED', 'DETACHED')),
    last_synced_at TEXT,
    todo_version_at_sync INTEGER NOT NULL CHECK (todo_version_at_sync >= 1),
    event_version_at_sync INTEGER NOT NULL CHECK (event_version_at_sync >= 1),
    version INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deleted_at TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_todo_calendar_links_active_pair
ON todo_calendar_links(todo_id, event_id) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_todo_calendar_links_todo ON todo_calendar_links(todo_id);
CREATE INDEX IF NOT EXISTS idx_todo_calendar_links_event ON todo_calendar_links(event_id);
CREATE INDEX IF NOT EXISTS idx_todo_calendar_links_conflict ON todo_calendar_links(conflict_status);
CREATE INDEX IF NOT EXISTS idx_todo_calendar_links_deleted ON todo_calendar_links(deleted_at);

CREATE TABLE IF NOT EXISTS sync_field_baselines (
    link_id TEXT NOT NULL REFERENCES todo_calendar_links(link_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    field_id TEXT NOT NULL CHECK (field_id IN ('TITLE','DESCRIPTION','START_AT','DUE_END')),
    baseline_json TEXT NOT NULL,
    baseline_sha256 TEXT NOT NULL CHECK (length(baseline_sha256) = 64),
    todo_sha256_at_baseline TEXT NOT NULL CHECK (length(todo_sha256_at_baseline) = 64),
    calendar_sha256_at_baseline TEXT NOT NULL CHECK (length(calendar_sha256_at_baseline) = 64),
    version INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (link_id, field_id)
);

CREATE INDEX IF NOT EXISTS idx_sync_field_baselines_link
ON sync_field_baselines(link_id);

CREATE TABLE IF NOT EXISTS sync_audit_receipts (
    receipt_id TEXT PRIMARY KEY,
    link_id TEXT NOT NULL REFERENCES todo_calendar_links(link_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    plan_id TEXT NOT NULL,
    precondition_sha256 TEXT NOT NULL CHECK (length(precondition_sha256) = 64),
    receipt_sha256 TEXT NOT NULL UNIQUE CHECK (length(receipt_sha256) = 64),
    result TEXT NOT NULL CHECK (result IN ('COMMITTED')),
    todo_version_before INTEGER NOT NULL CHECK (todo_version_before >= 1),
    todo_version_after INTEGER NOT NULL CHECK (todo_version_after >= todo_version_before),
    event_version_before INTEGER NOT NULL CHECK (event_version_before >= 1),
    event_version_after INTEGER NOT NULL CHECK (event_version_after >= event_version_before),
    link_version_before INTEGER NOT NULL CHECK (link_version_before >= 1),
    link_version_after INTEGER NOT NULL CHECK (link_version_after > link_version_before),
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sync_audit_receipts_link
ON sync_audit_receipts(link_id, created_at);
CREATE INDEX IF NOT EXISTS idx_sync_audit_receipts_plan
ON sync_audit_receipts(plan_id);

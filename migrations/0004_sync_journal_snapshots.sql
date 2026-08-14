CREATE TABLE IF NOT EXISTS sync_history_snapshots (
    receipt_id TEXT PRIMARY KEY REFERENCES sync_audit_receipts(receipt_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    link_id TEXT NOT NULL REFERENCES todo_calendar_links(link_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    snapshot_sha256 TEXT NOT NULL UNIQUE CHECK (length(snapshot_sha256) = 64),
    before_json TEXT NOT NULL,
    after_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sync_history_snapshots_link
ON sync_history_snapshots(link_id, created_at);

# CHANGELOG — PROVOWARE PLANER TOOL 2026

## 0.1.0-dev.1 — I000/I001
- Projektvertrag, globale Standards, Statusdateien, Repository-Inventar und Foundation-Autopilot.

## 0.2.0-dev.1 — I002
- Manifest-/Evidence-Kette, SHA-256-Inventar und Remote-Tree-Validierung.

## 0.3.0-dev.1 — I003
- Klick-&-Start-Orchestrator, Workspace-, Recovery- und Fault-Prüfung.

## 0.4.0-dev.1 — I004
- Kalender-Domainkern, Migration 0001, SQLite, Optimistic Locking, Soft Delete und Backup/Restore.

## 0.5.0-dev.1 — I005
- Kalender-Query/ViewModel, PySide6-GUI und 112er Offscreen-Matrix.

## 0.6.0-dev.1 — I006
- Todo-Domain, Migration 0002, Soft-Link, Konflikterkennung und Crash-/Rollback-Matrix.

## 0.7.0-dev.1 — I007
- TodoQueryService, TodoViewModel, fünf Ansichten und 140er GUI-Matrix.

## 0.8.0-dev.1 — I008
- ausschließlich lesende Synchronisationsvorschau und harte Konfliktblockaden.

## 0.9.0-dev.1 — I009
- Migration 0003, Feld-Baselines, typisierte SHA-256-Feldwerte, Drei-Wege-Vergleich, atomarer SyncPlan und Audit-Receipt.
- PRECHECK/COMMIT/POSTCHECK, Fault-Injection und echter Prozessabbruch innerhalb offener Transaktion.

## 0.10.0-dev.1 — I010
- SyncControlQuery/ViewModel und Synchronisations-Control-GUI.
- Neuer immutable ResolutionPlan; `TODO_WERT`, `KALENDER_WERT`, `BLOCKIERT_LASSEN` ausschließlich für `BOTH_DIFFERENT`.
- Source-Plan-SHA, Stale-/Manipulationsschutz und Wiederverwendung des I009-Commitkerns.

## 0.11.0-dev.1 — I011
- Migration `0004_sync_journal_snapshots.sql` ergänzt atomare, hashgebundene Vorher-/Nachher-Snapshots für neue Sync-/Resolution-/Recovery-Receipts.
- Ältere I009/I010-Receipts bleiben unverändert auditierbar und werden ohne erfundene Snapshots als `LEGACY_NO_SNAPSHOT` gekennzeichnet.
- Read-only Synchronisationsjournal mit Integritätsstatus, Feld-Diff und Recovery-Verfügbarkeit ergänzt.
- Neuer immutable `RecoveryPlan` bindet Source-Receipt, Source-Snapshot, aktuellen SyncPlan, Precondition, Versionen und Feld-Hashes.
- Historische Werte werden nie frei zurückgeschrieben; Recovery darf nur aktuell beweisbar vorhandene Zielwerte über den bestehenden I009-Transaktionskern übertragen.
- Snapshot-Manipulation, stale Current-State, divergente historische Zustände, Richtungsverstöße und DUE_END-Schreibbedarf blockieren fail-closed.
- Eigene Snapshot-Fault-/Crash-Matrix und 35er Journal-GUI-Matrix ergänzt.

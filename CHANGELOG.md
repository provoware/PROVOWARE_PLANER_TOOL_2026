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
- Neuer immutable ResolutionPlan und explizite Konfliktentscheidungen.

## 0.11.0-dev.1 — I011
- Migration 0004, hashgebundene Vorher-/Nachher-Snapshots, read-only Synchronisationsjournal und RecoveryPlan.
- Snapshot-Manipulation, stale Current-State und divergente historische Zustände blockieren fail-closed.

## 0.12.0-dev.1 — I012
- Read-only Diagnose-/Recovery-Zentrale mit Startzustand, SQLite-, Journal-, Backup- und Recovery-Prüfung.
- Keine neue Datenbankmigration; Schema bleibt Version 4.

## 0.13.0-dev.1 — I013
- Entwicklungsautopilot V2 mit Static-first, maschinenlesbarem Iterationsplan, planbasiertem Inventar, Gate-Deduplizierung und Exact-SHA-Promotion.

## 0.14.0-dev.1 — I014
- Entwicklungsrepository und normale Weitergabe technisch getrennt.
- `PROJEKTKERN`, `NUTZER`, `ENTWICKLER`, `EVIDENCE` als getrennte Profile eingeführt.
- Nutzdaten, Sicherungen, Restore-Kandidaten, Logs und temporäre Dateien sind in Code-Transportprofilen ausgeschlossen.
- Deterministischer profilbasierter ZIP-Builder, Paketmanifest/-inventar und Fresh-Unpack-Startprüfung eingeführt.
- Keine Datenbankmigration; Schema bleibt Version 4.

## 0.15.0-dev.1 — I015
- Verbindlichen `PROVOWARE-BACKUP-RESTORE 1.0.0` und `BACKUP_RESTORE_PLAN_CONTRACT` eingeführt.
- Backup-Kandidaten werden ausschließlich read-only innerhalb des expliziten Backup-Bereichs gegen Manifest, SHA-256, Größe, SQLite `quick_check` und Schema 4 qualifiziert.
- Neuer immutable `RestorePlan` bindet Backup, Manifest und den aktiven Zielzustand in einen kanonischen SHA-256-Planhash.
- Zielzustandsbindung umfasst Hauptdatenbank und WAL, damit nach Planerstellung erfolgte SQLite-Änderungen auch vor einem Checkpoint als stale erkannt werden.
- `storage.backup.restore_backup()` bleibt der einzige physische Dateiaustauschpfad; `RestoreService` besitzt keine eigene Replace-/Copy-Implementierung.
- Physischer Restorekern um letzten read-only Precheck und rollbackfähigen Postcheck erweitert.
- Fehler vor Schreibzugriff verändern nichts; Fehler nach atomarem Austausch stellen über den bestehenden Pre-Restore-Rollbackpfad den vorherigen Zustand wieder her.
- Plan-Tamper, Backup-/Manifest-Tamper, Stale-Zielzustand sowie Exception-/Prozessabbruch-Szenarien werden automatisiert geprüft.
- Backup-/Restore-Domainkern wird als Runtime benötigt, Sicherungsdaten selbst bleiben aus allen Code-Transportprofilen ausgeschlossen.
- Keine Datenbankmigration; Schema bleibt Version 4.

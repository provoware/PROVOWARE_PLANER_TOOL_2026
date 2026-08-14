# CHANGELOG — PROVOWARE PLANER TOOL 2026

## 0.1.0-dev.1 — I000/I001 Foundation
- Projektvertrag, globale Standards, Statusdateien, Repository-Inventar und Foundation-Autopilot eingeführt.

## 0.2.0-dev.1 — I002
- Manifest- und Evidence-Kette, SHA-256-Inventar, Remote-Tree-Validierung und zweistufige Remote-Prüfung ergänzt.

## 0.3.0-dev.1 — I003
- Klick-&-Start-Orchestrator, Workspace-Prüfung, Recovery, Fault-Injection und detailliertes Startfeedback ergänzt.

## 0.4.0-dev.1 — I004
- Kalender-Domainkern, SQLite-Persistenz, Migrationen, fünf Markierungen, Optimistic Locking, Soft Delete und Backup/Restore ergänzt.

## 0.5.0-dev.1 — I005
- CalendarQueryService und CalendarViewModel eingeführt.
- PySide6/Qt-Kalenderoberfläche mit Tag/Woche/Monat/Jahr, Design-Tokens, Barrierefreiheit und 112er Offscreen-Matrix ergänzt.

## 0.6.0-dev.1 — I006
- Todo-Domainkern, Migration 0002, TodoRepository/TodoService und eigenständigen Todo↔Kalender-Soft-Link ergänzt.
- Optimistic Locking, Soft Delete, Konfliktzustände, Löschschutz und Crash-/Rollback-Matrix eingeführt.

## 0.7.0-dev.1 — I007
- TodoQueryService, TodoViewModel und fünf Todo-Ansichten ergänzt.
- Todo-GUI mit Bearbeitung, Unteraufgaben, Kalender-Verknüpfung, Konflikterklärung und 140er Offscreen-Matrix eingeführt.
- automatische Inhalts-Synchronisation und Konfliktauflösung blieben deaktiviert.

## 0.8.0-dev.1 — I008
- `SynchronizationPreviewService` als ausschließlich lesende Synchronisationsvorschau eingeführt.
- immutable `SyncPreview`-/`SyncFieldPreview`-Modelle und Feldvertrag für Titel, Beschreibung, Startzeit sowie manuell prüfpflichtiges `due_at ↔ end_at` ergänzt.
- `BOTH_CHANGED`, `DETACHED` und abweichende `CLEAN`-Ausgangswerte als harte Blocker festgelegt.
- I008 besitzt absichtlich keine Schreibschnittstelle; Schema blieb Version 2.
- Zieltests, Contract-Guards, Fehlerkatalog, Validator, zweistufige Evidence-Prüfung und Main-Nachqualifikation ergänzt.

## 0.9.0-dev.1 — I009
- Migration `0003_sync_field_baseline.sql` mit `sync_field_baselines` und `sync_audit_receipts` eingeführt; keine Baseline wird für bestehende Links erfunden.
- typisierte kanonische Feldserialisierung mit UTC-Normalisierung für Zeitwerte und SHA-256-Feld-Hashes ergänzt.
- Drei-Wege-Zustände `UNCHANGED`, `TODO_ONLY`, `CALENDAR_ONLY`, `BOTH_SAME`, `BOTH_DIFFERENT` und `BASELINE_MISSING` eingeführt.
- disjunkte Änderungen an Todo und Kalender können trotz Objektzustand `BOTH_CHANGED` feldweise verlustfrei zu einem deterministischen `SyncPlan` zusammengeführt werden.
- `BOTH_DIFFERENT`, fehlende Baselines, getrennte Endpunkte, falsche Richtung und verletzte Zielinvarianten blockieren fail-closed.
- `due_at ↔ end_at` bleibt unabhängig von Hash-Eindeutigkeit semantisch manuell prüfpflichtig.
- `SyncPlan` bindet exakte Todo-/Termin-/Link-Versionen, Richtung, Baseline-/Todo-/Kalender-Hashes, Feldzustände und Aktionen an eine `precondition_sha256` und deterministische Plan-ID.
- PRECHECK, Nutzdatenwrite, Baseline-Fortschreibung, Link-Snapshot, POSTCHECK und Audit-Receipt laufen in einer `BEGIN IMMEDIATE`-Transaktion; Teilcommits sind verboten.
- Audit-Receipt enthält Vorher-/Nachher-Versionen, Feldzustände/Aktionen und einen SHA-256 des kanonischen Receipt-Payloads.
- POSTCHECK prüft Endwertgleichheit, Baseline-Hashes, Versions-Snapshots und Receipt-Hash vor Commit; danach folgt SQLite-`quick_check`.
- Fault-Injection nach Nutzdatenwrite, Baseline-Write, vor Receipt und nach Receipt sowie echter Prozessabbruch nach Nutzdatenwrite ergänzt.
- I008-Historienvalidator für legitime spätere Schema-Versionen vorwärtskompatibel gehärtet.
- I009-Vertrag, Fehlerkatalog, Tests, Fault-Matrix, unabhängiger Validator und Autopilot-Gate ergänzt.

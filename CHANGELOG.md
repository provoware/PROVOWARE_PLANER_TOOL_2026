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

## 0.12.0-dev.1 — I012
- Read-only Diagnose-/Recovery-Zentrale mit fünf Bereichen: Startzustand, SQLite-Integrität, Journal-Integrität, Backup-Nachweise und Recovery-Blockaden.
- Datenbank- und Backup-Prüfung verwendet explizit SQLite `mode=ro` und `PRAGMA query_only=ON`.
- Backup-Kandidaten werden zusätzlich gegen Manifest und SHA-256 geprüft; Manipulation wird sichtbar blockiert.
- Recovery-Diagnose verwendet ausschließlich neue I011-`RecoveryPlan`-Vorschauen und führt keinen Commit aus.
- Diagnose-GUI über `Ctrl+Shift+D` integriert; Symbol + Klartext bleiben verpflichtend, Farbe allein trägt keine Bedeutung.
- StartOrchestrator-Bericht wird standardmäßig atomar als `LETZTER_STARTBERICHT.json` im Arbeitsbereich gespeichert.
- I012-Service-/GUI-Zieltests, Autopilot-Gate und 35er Offscreen-Diagnosematrix ergänzt.
- Keine neue Datenbankmigration; Schema bleibt Version 4.

## 0.13.0-dev.1 — I013
- Entwicklungsarbeit anhand der realen I012-Qualifikation auf Effizienz, Präzision und unnötige Remote-Schleifen auditiert.
- Verbindlichen `PROVOWARE-DEVELOPMENT 2.0.0` mit `Ermittlung → Planung → P0 Static → Zielprüfung → Runtime → Regression → Evidence → Promotion → Optimierung` eingeführt.
- `ITERATION_PLAN.json` bindet Baseline-Commit/-Tree, Risikoklasse, acht Akzeptanzkriterien und explizite `add`/`modify`/`delete`-Differenz.
- Kandidateninventar berechnet das Repository-Soll aus qualifizierter Baseline plus deklarierter Differenz; ungeplante Pfade blockieren.
- P0-Preflight prüft JSON, Python-Syntax, Metadaten, Standardindex, Dokumentationsmarker, Pipelinevertrag und Dateidifferenz vor apt/pip/Qt.
- Dokumentationsstandard auf stabile semantische README-Marker umgestellt; exakter Überschriftentext ist nicht mehr Maschinenvertrag.
- Autopilot führt historische Gates pro Pass genau einmal aus und schreibt optionale Laufzeit-Evidence.
- CI-Referenzpipeline erhält Concurrency-Abbruch für veraltete Läufe, Lockdatei-gebundenen pip-Cache und Static-first-Reihenfolge.

## 0.14.0-dev.1 — I014
- Repository und normale Weitergabe technisch getrennt: vollständige Entwicklungsbasis bleibt auditierbar, Standardtransport ist jetzt das reduzierte `NUTZER`-Profil.
- Vier eindeutige Transportklassen eingeführt: `PRODUKTKERN`, `NUTZERDOKU`, `ENTWICKLUNG`, `EVIDENCE`.
- Vier Profile eingeführt: `PROJEKTKERN`, `NUTZER`, `ENTWICKLER`, `EVIDENCE`; Evidence wird weder in Nutzer- noch Entwicklerpakete gemischt.
- SQLite-Nutzdaten, Sicherungen, Restore-Kandidaten, Workspaces, Logs, Caches und temporäre Dateien sind in allen Code-Transportprofilen hart ausgeschlossen.
- `.gitignore` ergänzt als zweite Schutzschicht gegen versehentliches Einchecken lokaler Nutzdaten/Sicherungen.
- Deterministischer profilbasierter ZIP-Builder mit festen Zeitstempeln, sortierten Pfaden und normalisierten Dateimodi eingeführt.
- Jedes Paket erhält `PAKETMANIFEST.json` und `PAKET_INVENTAR.json`; lauffähige Profile zusätzlich ein paketbezogenes kompatibles `SHA256_DATEI_INVENTAR.json`.
- Paketbau bezieht seine Quelldateien ausschließlich aus dem registrierten Repository-Soll; ungetrackte lokale Arbeits-/Backupdaten werden nicht entdeckt oder eingesammelt.
- Fresh-Unpack-Nutzerstart, Profilgrenzen und byte-identischer Doppelbau werden als I014-Pflichtgates qualifiziert.
- Keine Datenbankmigration; Schema bleibt Version 4.

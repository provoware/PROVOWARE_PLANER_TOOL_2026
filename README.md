# PROVOWARE PLANER TOOL 2026

Privates, portables und vollständig offline ausgerichtetes Ein-Nutzer-Planungswerkzeug für Linux. Das Projekt wird als wartbarer modularer Monolith entwickelt und autonom qualifiziert.

## 1. Projektstatus
- **Version:** `0.9.0-dev.1`
- **Iteration:** `I009`
- **Checkpoint:** `C009-FIELD-BASELINE-TRANSACTIONAL-SYNC`
- **Status:** `IN_ARBEIT / GELB` bis zur vollständigen I009-Remotequalifikation
- **Zielplattform:** Linux, insbesondere Ubuntu-/Kubuntu-Derivate
- **Betrieb:** lokal und offline-first
- **Technische Nutzerabnahme:** nicht Bestandteil der Pflicht-Freigabekette

Die maschinenlesbare Wahrheit liegt in `VERSION.json`, `PROJEKTSTATUS.json` und `PROJECT_CONTRACT.json`.

## 2. Was ist das Tool?
PROVOWARE PLANER verbindet Kalender, Aufgabenplanung, Dashboard, Diagnose und spätere Zusatzmodule. Nutzerdaten bleiben lokal. Der Arbeitsordner wird real geprüft und dauerhaft über eine Workspace-ID zugeordnet.

## 3. Kernmodule
### Kalender
Tag, Woche, Monat und Jahr; Termine und fünf editierbare Markierungen. Markierungen verwenden Farbe plus Text oder Symbol.

### Todo
Aufgaben mit Status, Priorität, Fälligkeit, Unteraufgaben und Fortschritt. Die fünf Ansichten sind **Heute**, **Diese Woche**, **Überfällig**, **Ohne Datum** und **Erledigt**.

### Synchronisation
Todo und Termin bleiben eigenständige Objekte. Ihre Kopplung verwendet einen eigenen Soft-Link. I009 ergänzt beweisbare Feld-Baselines, SHA-256-Feldzustände und einen atomaren Synchronisationsplan.

### Dashboard
Heute, nächste Termine, fällige/überfällige Aufgaben sowie Sicherungs-, Modul- und Systemstatus.

### Diagnose und Logging
Probleme erhalten stabile IDs, maschinenlesbare Daten und laienverständliche Hinweise zu Ursache, Auswirkung und nächstem Schritt.

## 4. Oberfläche und globale Gestaltung
Alle Module verwenden zentrale Designregeln. Abstände basieren auf dem 4-Pixel-Raster; Schrift ist global in 90, 100, 110, 125, 150, 175 und 200 Prozent skalierbar. Farbe wird nie ohne Symbol oder Klartext als alleinige Bedeutung verwendet.

## 5. Ampelsystem
- 🟢 **GRÜN – BEREIT**
- 🟡 **GELB – EINGESCHRÄNKT**
- 🔴 **ROT – BLOCKIERT**

## 6. Klick-&-Start
Der Start-Orchestrator prüft Betriebssystem, Runtime, Programmdateien, Manifeste, Konfiguration, Workspace, Datenbank, Schema, Recovery, Module und GUI. Relevante Aktionen folgen `PRECHECK → AKTION → POSTCHECK`. Kalender, Todo und Synchronisation verwenden dieselbe Planner-Datenbank.

## 7. Daten und Sicherheit
SQLite arbeitet mit Foreign Keys, WAL, `synchronous=FULL`, Transaktionen, hashgebundenen Migrationen und Vor-Migrations-Sicherungen. Fachliches Löschen erfolgt als Soft Delete. Todo↔Termin verwendet keine kaskadierenden Löschungen.

I009 führt Migration `0003_sync_field_baseline.sql` ein. Schema-Version 3 ergänzt `sync_field_baselines` und `sync_audit_receipts`. Bestehende Links erhalten keine erfundene Baseline: Eine Baseline wird nur gebunden, wenn beide Feldwerte kanonisch identisch sind.

## 8. Globale Standards
Verbindliche Standards liegen unter `standards/` und sind über `standards/STANDARD_INDEX.json` registriert. Der Vorrang lautet `PROVOWARE_GLOBAL_STANDARD → PROJECT_CONTRACT → Modulvertrag → konkrete Konfiguration`.

## 9. Repository-Vollständigkeit
`REPOSITORY_MANIFEST.json` ist das Soll-Inventar des vollständigen Entwicklungsbaums. Jede Iteration prüft fehlende und unerwartete Dateien, Projekt-/Versionskonsistenz, Manifeste, SHA-256-Nachweise sowie relevante Dateimodi.

## 10. Autonomer Entwicklungs- und Prüfautopilot
`tools/autopilot/autopilot.py qualifizieren` führt globale Standards und alle historischen Pflichtgates bis zur aktuellen Iteration aus. `FAIL` und `NOT_RUN` blockieren Freigaben. Remote-Prüfungen laufen zusätzlich in GitHub Actions und werden mit einem exakten Evidence-SHA-Zweitpass abgeschlossen.

## 11. Historische Entwicklung
- **I002:** Manifest-/Evidence-Kette, SHA-256-Inventar und Remote-Tree-Receipt.
- **I003:** Klick-&-Start-Orchestrator, Workspace-Prüfung, Recovery und Fault-Injection.
- **I004:** Kalender-Domainkern, Migration 0001, Optimistic Locking, Soft Delete, Backup/Restore.
- **I005:** Kalender-GUI + ViewModel, vier Ansichten und 112 Offscreen-Konfigurationen.
- **I006:** Todo-Domainkern, Migration 0002, Soft-Link, Konflikterkennung und Crash-Matrix.
- **I007:** TodoQueryService, TodoViewModel, fünf Todo-Ansichten und 140er Todo-GUI-Matrix.
- **I008:** ausschließlich lesende Synchronisationsvorschau mit Feldvertrag und harten Konfliktblockaden.
- **I009:** Feld-Baselines, Feld-Hashes, Drei-Wege-Vergleich, atomarer SyncPlan und Audit-Receipt.

## 12. Kalender↔Todo-Kopplungsvertrag
`todo_calendar_links` ist ein eigenes versioniertes Soft-Link-Objekt mit `link_id`, Todo-/Termin-ID, Synchronisationsrichtung und Versions-Snapshots. Physische Endpunktlöschung ist geschützt; Entkoppeln löscht nur den Link weich.

## 13. I008 — Read-only Synchronisationsvorschau
`SynchronizationPreviewService` bleibt unverändert als reine Vorschau bestehen. Er besitzt keine `apply()`, `execute()` oder `synchronize()`-Schreibschnittstelle. Damit bleibt die frühere sichere Diagnoseebene auch neben I009 verfügbar.

## 14. I009 — Feld-Baseline und Drei-Wege-Vergleich
Für `TITLE`, `DESCRIPTION`, `START_AT` und `DUE_END` wird eine gemeinsame Baseline mit kanonischem SHA-256 gespeichert. Zeitpunkte werden vor der Hashbildung nach UTC normalisiert.

Jedes Feld erhält exakt einen Zustand:
- `UNCHANGED`: beide Seiten entsprechen der Baseline.
- `TODO_ONLY`: nur Todo wurde seit der Baseline geändert.
- `CALENDAR_ONLY`: nur Kalender wurde geändert.
- `BOTH_SAME`: beide Seiten änderten sich auf denselben neuen Wert.
- `BOTH_DIFFERENT`: dasselbe Feld wurde unterschiedlich geändert; harter Blocker.
- `BASELINE_MISSING`: keine beweisbare Ausgangsbasis; harter Blocker.

Dadurch kann ein Link auf Objektebene `BOTH_CHANGED` sein und dennoch verlustfrei synchronisierbar bleiben, wenn unterschiedliche Felder auf unterschiedlichen Seiten verändert wurden.

`due_at ↔ end_at` bleibt weiterhin semantisch prüfpflichtig und wird nicht automatisch geschrieben.

## 15. Transaktionaler SyncPlan, Audit und Evidence
Ein deterministischer `SyncPlan` bindet Todo-, Termin- und Link-Version, Richtung, Baseline-Hash, Todo-Hash und Kalender-Hash je Feld an eine `precondition_sha256` und eine deterministische Plan-ID.

Die Ausführung lautet verbindlich:

`PRECHECK → atomarer COMMIT → POSTCHECK → Audit-Receipt`.

Beim PRECHECK werden innerhalb derselben `BEGIN IMMEDIATE`-Transaktion alle Versionen und Hash-Vorbedingungen erneut geprüft. Teilcommits sind verboten. Nutzdaten, Baselines, Link-Snapshots und `sync_audit_receipts` werden gemeinsam geschrieben oder gemeinsam zurückgerollt.

Der POSTCHECK prüft noch vor dem SQLite-Commit Endwerte, Baseline-Hashes, Versions-Snapshots und Receipt-Hash. Danach folgt `PRAGMA quick_check`.

Die I009-Fault-Matrix injiziert Fehler nach Nutzdatenwrite, nach Baseline-Write, vor Receipt, nach Receipt vor Commit und einen echten Prozessabbruch nach Nutzdatenwrite. Jeder Pfad muss vollständig auf den Vorzustand zurückrollen.

Die historische Pflichtkette lautet `I002 → I003 → I004 → I005 → I006 → I007 → I008 → I009`; die 140er Todo-GUI- und 112er Kalender-GUI-Matrix bleiben Pflichtregressionen.

## 16. Aktueller Checkpoint
**C009 — FIELD-BASELINE-TRANSACTIONAL-SYNC.** Migration, Baseline-/Hashmodell, Drei-Wege-Planung, atomare Ausführung, POSTCHECK, Audit-Receipt, Fault-Matrix und Validator sind angelegt. `IN_ARBEIT / GELB` bleibt verbindlich, bis Zieltests, Vollregression, historische Gates, Remote-Tree und exakter Evidence-SHA-Zweitpass vollständig bestanden sind.

## 17. Nächster logischer Schritt
Nach erfolgreicher I009-Qualifikation: **I010 — Synchronisations-Control-GUI + explizite Konfliktentscheidung.** Die Oberfläche darf ausschließlich qualifizierte `SyncPlan`-Objekte anzeigen und committen; sie darf weder SQL ausführen noch Konfliktlogik duplizieren.

## 18. Weiterführende Verbesserung
Für I010 `BOTH_DIFFERENT` ausschließlich über eine explizite manuelle Feldentscheidung behandeln: Todo-Wert übernehmen, Kalender-Wert übernehmen oder unverändert lassen. Jede Entscheidung sollte einen neuen immutable Plan erzeugen und separat im Audit-Receipt nachweisbar sein; keine automatische Heuristik darf Daten überschreiben.

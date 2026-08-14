# PROVOWARE PLANER TOOL 2026

Privates, portables und vollständig offline ausgerichtetes Ein-Nutzer-Planungswerkzeug für Linux. Das Projekt wird als wartbarer modularer Monolith entwickelt und autonom qualifiziert.

## 1. Projektstatus
- **Version:** `0.8.0-dev.1`
- **Iteration:** `I008`
- **Checkpoint:** `C008-SYNC-CONFLICT-PREVIEW`
- **Status:** `IN_ARBEIT / GELB` bis zur vollständigen I008-Remotequalifikation
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

### Dashboard
Heute, nächste Termine, fällige/überfällige Aufgaben sowie Sicherungs-, Modul- und Systemstatus.

### Diagnose und Logging
Probleme erhalten stabile IDs, maschinenlesbare Daten und laienverständliche Hinweise zu Ursache, Auswirkung und nächstem Schritt.

## 4. Oberfläche und globale Gestaltung
Alle Module verwenden zentrale Designregeln. Abstände basieren auf dem 4-Pixel-Raster; Schrift ist global in 90, 100, 110, 125, 150, 175 und 200 Prozent skalierbar. Die Todo-GUI verwendet dasselbe Designsystem wie der Kalender.

## 5. Ampelsystem
- 🟢 **GRÜN – BEREIT**
- 🟡 **GELB – EINGESCHRÄNKT**
- 🔴 **ROT – BLOCKIERT**

Farbe wird nie ohne Symbol und Klartext verwendet.

## 6. Klick-&-Start
Der Start-Orchestrator prüft Betriebssystem, Runtime, Programmdateien, Manifeste, Konfiguration, Workspace, Datenbank, Schema, Recovery, Module und GUI. Relevante Aktionen folgen `PRECHECK → AKTION → POSTCHECK`. Das Aufgabenmodul nutzt dieselben Planner-Services und dieselbe SQLite-Datenbank wie der Kalender.

## 7. Daten und Sicherheit
SQLite arbeitet mit Foreign Keys, WAL, Transaktionen, hashgebundenen Migrationen und Vor-Migrations-Sicherungen. Fachliches Löschen erfolgt als Soft Delete. Todo↔Termin verwendet keine kaskadierenden Löschungen. I008 benötigt keine neue Migration; Schema-Version 2 bleibt maßgeblich.

## 8. Globale Standards
Verbindliche Standards liegen unter `standards/` und sind über `standards/STANDARD_INDEX.json` registriert. Der Vorrang lautet `PROVOWARE_GLOBAL_STANDARD → PROJECT_CONTRACT → Modulvertrag → konkrete Konfiguration`.

## 9. Repository-Vollständigkeit
`REPOSITORY_MANIFEST.json` ist das Soll-Inventar des vollständigen Entwicklungsbaums. Jede Iteration prüft fehlende und unerwartete Dateien, Projekt-/Versionskonsistenz, Manifeste sowie relevante Dateimodi und Hash-Nachweise.

## 10. Autonomer Entwicklungs- und Prüfautopilot
`tools/autopilot/autopilot.py qualifizieren` führt globale Standards und alle historischen Pflichtgates bis zur aktuellen Iteration aus. `FAIL` und `NOT_RUN` blockieren Freigaben. Remote-Prüfungen laufen zusätzlich in GitHub Actions.

## 11. Historische Entwicklung
- **I002:** Manifest-/Evidence-Kette, SHA-256-Inventar und Remote-Tree-Receipt.
- **I003:** Klick-&-Start-Orchestrator, Workspace-Prüfung, Recovery und Fault-Injection.
- **I004:** Kalender-Domainkern, Migration 0001, Optimistic Locking, Soft Delete, Backup/Restore.
- **I005:** Kalender-GUI + ViewModel, vier Ansichten, sieben Schriftstufen und 112 Offscreen-Konfigurationen.
- **I006:** Todo-Domainkern, Migration 0002, Unteraufgaben, Soft-Link und Konflikterkennung.
- **I007:** TodoQueryService, TodoViewModel, fünf Todo-Ansichten und 140er Todo-GUI-Matrix.

## 12. Kalender↔Todo-Kopplungsvertrag
`todo_calendar_links` ist ein eigenes versioniertes Soft-Link-Objekt mit `link_id`, Todo-/Termin-ID, Synchronisationsrichtung und Versions-Snapshots. Konfliktzustände sind `CLEAN`, `TODO_CHANGED`, `CALENDAR_CHANGED`, `BOTH_CHANGED` und `DETACHED`.

`ON DELETE CASCADE` zwischen Todo, Termin und Link ist verboten. Ein explizites Entkoppeln löscht nur den Link weich.

## 13. I007 — Todo-GUI + Todo-ViewModel
Die Schichtfolge lautet `TodoService → TodoQueryService → TodoViewModel → Darstellungsmodelle → PySide6/Qt`. GUI und ViewModel importieren weder Repository-Code noch SQLite. Konflikte werden sichtbar erklärt, aber nicht automatisch aufgelöst.

## 14. I008 — Read-only Synchronisationsvorschau
I008 ergänzt `SynchronizationPreviewService` und immutable Vorschauobjekte. Diese Schicht besitzt absichtlich **keine Schreibschnittstelle**. `SyncPreview.write_permitted` bleibt immer `False`.

Feldregeln:
- `title ↔ title`: gerichteter Vorschaukandidat.
- `description ↔ description`: gerichteter Vorschaukandidat.
- `start_at ↔ start_at`: gerichteter Vorschaukandidat.
- `due_at ↔ end_at`: nur manuelle semantische Prüfung.

Status, Priorität, Fortschritt, Elternaufgabe, Terminstatus, Zeitzone, Ganztägigkeit und Markierung werden nicht still ineinander übersetzt.

## 15. Konfliktregeln I008
- `CLEAN`: Abweichende Werte ohne belastbare Feld-Baseline werden blockiert.
- `TODO_CHANGED`: Vorschlag Todo→Kalender nur bei erlaubter Richtung.
- `CALENDAR_CHANGED`: Vorschlag Kalender→Todo nur bei erlaubter Richtung.
- `BOTH_CHANGED`: immer hart blockiert.
- `DETACHED`: immer hart blockiert.
- `MANUAL`: keine automatische Richtung.

Der Grund für die strikte Behandlung von `BOTH_CHANGED`: Der Link kennt bisher Objektversionen, aber keine Feld-Baseline oder Feld-Hashes. Eine verlustfreie automatische Zusammenführung ist deshalb noch nicht beweisbar.

## 16. Evidence-Kette
Die Pflichtkette für I008 lautet `I002 → I003 → I004 → I005 → I006 → I007 → I008`. Zusätzlich bleiben die 140er Todo-GUI-Matrix, die 112er Kalender-GUI-Matrix, die I006-Crash-/Rollback-Matrix, Vollregression, Repository-Inventar und exakter Evidence-SHA-Zweitpass Pflicht.

## 17. Aktueller Checkpoint
**C008 — SYNC-CONFLICT-PREVIEW.** Feldvertrag, Vorschau-Domain und Zieltests sind angelegt. Der Stand bleibt GELB, bis die Remotequalifikation vollständig grün ist.

## 18. Nächster logischer Schritt
Nach erfolgreicher I008-Qualifikation: **I009 — Feld-Baseline / Feld-Hashes + transaktionaler Synchronisationsplan.** Erst diese Iteration darf die Voraussetzungen für reale Schreibsynchronisation schaffen.

## 19. Weiterführende Verbesserung
Für I009 jede synchronisierbare Feldpaarung mit einem gespeicherten Baseline-Hash oder Baseline-Wert versehen. Dadurch kann bei `BOTH_CHANGED` erkannt werden, ob tatsächlich dasselbe Feld beidseitig geändert wurde oder ob sich unabhängige Änderungen verlustfrei zusammenführen lassen.

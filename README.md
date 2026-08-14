# PROVOWARE PLANER TOOL 2026

Privates, portables und vollständig offline ausgerichtetes Ein-Nutzer-Planungswerkzeug für Linux. Das Projekt wird als wartbarer modularer Monolith entwickelt und autonom qualifiziert.

## 1. Projektstatus
- **Version:** `0.7.0-dev.1`
- **Iteration:** `I007`
- **Checkpoint:** `C007-TODO-GUI-VIEWMODEL`
- **Status:** `QUALIFIZIERT / GRÜN` nach erfolgreicher I007-Remotequalifikation
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
Aufgaben mit Status, Priorität, Fälligkeit, Unteraufgaben und Fortschritt. I007 ergänzt die fünf Ansichten **Heute**, **Diese Woche**, **Überfällig**, **Ohne Datum** und **Erledigt**. Todo und Termin bleiben eigenständige Datenobjekte; ihre Kopplung besitzt eine eigene Identität.

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
Der Start-Orchestrator prüft Betriebssystem, Runtime, Programmdateien, Manifeste, Konfiguration, Workspace, Datenbank, Schema, Recovery, Module und GUI. Relevante Aktionen folgen `PRECHECK → AKTION → POSTCHECK`. Das Aufgabenmodul wird über **Module → Aufgaben öffnen** aus dem vorhandenen Kalenderfenster gestartet und nutzt dieselben Planner-Services.

## 7. Daten und Sicherheit
SQLite arbeitet mit Foreign Keys, WAL, Transaktionen, hashgebundenen Migrationen und Vor-Migrations-Sicherungen. Fachliches Löschen erfolgt als Soft Delete. Todo↔Termin verwendet keine kaskadierenden Löschungen. I007 benötigt keine neue Migration; Schema-Version 2 bleibt maßgeblich.

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
- **I006:** Todo-Domainkern, Migration 0002, Unteraufgaben, Soft-Link und konfliktrobuste Kalenderkopplung.

## 12. I006 — Todo-Domainkern
`TodoItem` unterstützt Status, Priorität, Fortschritt, Start, Fälligkeit und Unteraufgaben. Eine erledigte Aufgabe besitzt 100 Prozent Fortschritt. Änderungen verwenden Optimistic Locking; fachliches Löschen ist Soft Delete.

## 13. Kalender↔Todo-Kopplungsvertrag
`todo_calendar_links` ist ein eigenes versioniertes Soft-Link-Objekt mit `link_id`, Todo-/Termin-ID, Synchronisationsrichtung und Versions-Snapshots. Konfliktzustände sind `CLEAN`, `TODO_CHANGED`, `CALENDAR_CHANGED`, `BOTH_CHANGED` und `DETACHED`.

`ON DELETE CASCADE` zwischen Todo, Termin und Link ist verboten. Ein explizites Entkoppeln löscht nur den Link weich. I007 zeigt Konflikte über eine reine Vorschau an und führt weder automatische Inhalts-Synchronisation noch automatische Konfliktauflösung aus.

## 14. I007 — Todo-GUI + Todo-ViewModel
Die neue Schichtfolge lautet `TodoService → TodoQueryService → TodoViewModel → Darstellungsmodelle → PySide6/Qt`. Die GUI und das ViewModel importieren weder Repository-Code noch SQLite und führen kein SQL aus.

Bedienbar sind Erstellen, Bearbeiten, Status, Priorität, Fortschritt, Unteraufgaben, Kalender-Verknüpfung, Entkoppeln und Soft Delete. Konflikte werden mit Symbol, Klartext und Erklärung sichtbar gemacht.

## 15. Evidence-Kette
Die Pflichtkette lautet für I007 `I002 → I003 → I004 → I005 → I006 → I007`. Dazu kommen 140 Todo-GUI-Offscreen-Konfigurationen, die bestehende 112er Kalender-GUI-Matrix, Neustartpersistenz, I006-Crash-/Rollback-Regression und ein exakter Evidence-SHA-Zweitpass.

## 16. Aktueller Checkpoint
**C007 — TODO-GUI-VIEWMODEL.** Implementierung und Verträge sind angelegt. Der qualifizierte Evidence-Kandidat ist `GRÜN`; eine Promotion nach `main` erfolgt erst nach erfolgreichem exakten Evidence-SHA-Zweitpass.

## 17. Nächster logischer Schritt
Nach erfolgreicher I007-Qualifikation: **I008 — Kalender↔Todo-Synchronisations- und Konfliktauflösungsvertrag.** Erst dort werden erlaubte Feldzuordnungen, Synchronisationsrichtungen und eine verlustfreie Behandlung von `BOTH_CHANGED` festgelegt.

## 18. Weiterführende Verbesserung
I008 sollte zunächst eine **Vorschau/Simulation jeder Synchronisation** erzeugen: Quelle, Ziel, betroffene Felder, alte/neue Werte, Konfliktgrund und erwartete Version. Erst nach bestandenem Precheck darf eine atomare Änderung erfolgen; `BOTH_CHANGED` bleibt ohne explizite qualifizierte Regel blockiert.

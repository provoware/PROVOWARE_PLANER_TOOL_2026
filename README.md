# PROVOWARE PLANER TOOL 2026

Privates, portables und vollständig offline ausgerichtetes Ein-Nutzer-Planungswerkzeug für Linux. Das Projekt wird als wartbarer modularer Monolith entwickelt und autonom qualifiziert.

## 1. Projektstatus
- **Version:** `0.6.0-dev.1`
- **Iteration:** `I006`
- **Checkpoint:** `C006-TODO-DOMAIN-LINK`
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
Aufgaben mit Status, Priorität, Fälligkeit, Unteraufgaben und Fortschritt. Todo und Termin bleiben eigenständige Datenobjekte; ihre Kopplung besitzt eine eigene Identität.

### Dashboard
Heute, nächste Termine, fällige/überfällige Aufgaben sowie Sicherungs-, Modul- und Systemstatus.

### Diagnose und Logging
Probleme erhalten stabile IDs, maschinenlesbare Daten und laienverständliche Hinweise zu Ursache, Auswirkung und nächstem Schritt.

## 4. Oberfläche und globale Gestaltung
Alle Module verwenden zentrale Designregeln. Abstände basieren auf dem 4-Pixel-Raster; Schrift ist global in 90, 100, 110, 125, 150, 175 und 200 Prozent skalierbar.

## 5. Ampelsystem
- 🟢 **GRÜN – BEREIT**
- 🟡 **GELB – EINGESCHRÄNKT**
- 🔴 **ROT – BLOCKIERT**

Farbe wird nie ohne Symbol und Klartext verwendet.

## 6. Klick-&-Start
Der Start-Orchestrator prüft Betriebssystem, Runtime, Programmdateien, Manifeste, Konfiguration, Workspace, Datenbank, Schema, Recovery, Module und GUI. Relevante Aktionen folgen `PRECHECK → AKTION → POSTCHECK`.

## 7. Daten und Sicherheit
SQLite arbeitet mit Foreign Keys, WAL, Transaktionen, hashgebundenen Migrationen und Vor-Migrations-Sicherungen. Fachliches Löschen erfolgt als Soft Delete. Todo↔Termin verwendet keine kaskadierenden Löschungen.

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

## 12. I006 — Todo-Domainkern
`TodoItem` unterstützt Status, Priorität, Fortschritt, Start, Fälligkeit und Unteraufgaben. Eine erledigte Aufgabe besitzt 100 Prozent Fortschritt. Änderungen verwenden Optimistic Locking; fachliches Löschen ist Soft Delete.

## 13. Kalender↔Todo-Kopplungsvertrag
`todo_calendar_links` ist ein eigenes versioniertes Soft-Link-Objekt mit `link_id`, Todo-/Termin-ID, Synchronisationsrichtung und Versions-Snapshots. Konfliktzustände sind `CLEAN`, `TODO_CHANGED`, `CALENDAR_CHANGED`, `BOTH_CHANGED` und `DETACHED`.

`ON DELETE CASCADE` zwischen Todo, Termin und Link ist verboten. Link-Endpunkte verwenden `ON DELETE RESTRICT`. Ein explizites Entkoppeln löscht nur den Link weich. Automatische Inhalts-Synchronisation ist in I006 ausdrücklich deaktiviert.

## 14. Crash- und Rollback-Prüfung
I006 simuliert kontrollierte Schreibabbrüche vor Commit und zusätzlich einen echten separaten Prozess, der während einer offenen SQLite-Transaktion per `os._exit()` endet. Danach müssen Rollback, Wiederöffnung und `quick_check` bestehen.

## 15. Evidence-Kette
Die historische Pflichtkette lautet `I002 → I003 → I004 → I005 → I006`. Der qualifizierte Evidence-Commit wird in einem zweiten Remote-Pass anhand einer exakten Commit-SHA erneut geprüft.

## 16. Aktueller Checkpoint
**C006 — TODO-DOMAIN-LINK.** Implementierung ist angelegt; die Remote-Qualifikation entscheidet verbindlich über die Promotion nach `main`.

## 17. Nächster logischer Schritt
**I007 — Todo-GUI + Todo-ViewModel.** Die sichtbare Oberfläche darf ausschließlich `TodoService` und `TodoCalendarLinkService` verwenden. Konfliktzustände werden zunächst angezeigt; automatische Konfliktauflösung bleibt gesperrt, bis ein eigener Vertrag sie qualifiziert.

## 18. Weiterführende Verbesserung
Für I007 den TodoQueryService als reine Leseschicht zwischen Service und ViewModel einführen. So bleiben Filter wie Heute, Diese Woche, Überfällig und Ohne Datum von Qt entkoppelt und können unabhängig getestet werden.

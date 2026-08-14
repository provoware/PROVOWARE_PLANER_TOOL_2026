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
- PySide6/Qt-Kalenderoberfläche mit Tag/Woche/Monat/Jahr ergänzt.
- fünf editierbare Markierungen mit atomarer Batch-Speicherung ergänzt.
- Design-Tokens, Schriftskalierung, Ampelstatus, Tastatur und Accessible Names ergänzt.
- native GUI-Abhängigkeiten vor Qt-Import geprüft.
- 112er Offscreen-Matrix, Screenshots und Neustartpersistenz ergänzt.
- Aktionsbuttons werden bei jeder Schriftstufe zentral neu vermessen; Schriftbasis kann sich nicht aufschaukeln.
- zweiter Evidence-Pass an exakte `verify_sha` gebunden.

## 0.6.0-dev.1 — I006
- GUI-unabhängigen Todo-Domainkern mit Status, Priorität, Fortschritt, Start, Fälligkeit und Unteraufgaben eingeführt.
- Migration `0002_todo_domain_links.sql` mit `todos` und `todo_calendar_links` ergänzt.
- TodoRepository, TodoService und TodoCalendarLinkService eingeführt.
- Todo und Termin als unabhängige Entitäten mit Soft Delete und Optimistic Locking abgesichert.
- Kalender↔Todo-Kopplung als eigenes versioniertes Soft-Link-Objekt mit Synchronisationsrichtung eingeführt.
- Konfliktzustände für einseitige, beidseitige und getrennte Änderungen ergänzt.
- `ON DELETE CASCADE` zwischen Todo, Termin und Link verboten; physische Endpunktlöschung per `RESTRICT` geschützt.
- Entkoppeln löscht ausschließlich den Link weich und erhält Todo sowie Termin.
- automatische Inhalts-Synchronisation in I006 ausdrücklich deaktiviert.
- deterministische Fault-Injection und echten Prozessabbruch während offener SQLite-Transaktion ergänzt.
- historische Pflichtkette um I006 erweitert.

## 0.7.0-dev.1 — I007
- `TodoService` um eine kontrollierte Read-API ergänzt; keine neue Datenbankmigration erforderlich.
- `TodoCalendarLinkService.preview_conflict()` als reine, nicht schreibende Konfliktvorschau eingeführt.
- `TodoQueryService`, `TodoViewModel` und immutable Darstellungsmodelle eingeführt.
- fünf Todo-Ansichten umgesetzt: Heute, Diese Woche, Überfällig, Ohne Datum und Erledigt.
- PySide6/Qt-Todo-Fenster mit Erstellen, Bearbeiten, Status, Priorität, Fortschritt, Unteraufgaben, Kalender-Verknüpfung, Entkoppeln und Soft Delete ergänzt.
- Todo-Modul über `Module → Aufgaben öffnen` in den vorhandenen Planner-Start integriert und an dieselben Planner-Services gebunden.
- Konfliktzustände einschließlich `BOTH_CHANGED` sichtbar und laienverständlich erklärt; Anzeige verändert Linkzustand und Versions-Snapshots nicht.
- automatische Inhalts-Synchronisation und automatische Konfliktauflösung bleiben ausdrücklich deaktiviert.
- Tastaturreihenfolge, Kurzbefehle, Accessible Names, High-Contrast-Klartexte und sieben Schriftstufen ergänzt.
- Todo-GUI-Einstellungen sowie Todo-/Link-Daten auf Neustartpersistenz geprüft.
- 140er Todo-Offscreen-Matrix angelegt; 112er I005-Kalender-Matrix bleibt Pflichtregression.
- I006-Historienvalidator für nachfolgende Iterationen vorwärtskompatibel gehärtet.
- I007-Vertrag, Fehlerkatalog, unabhängiger Validator und Autopilot-Gate ergänzt.

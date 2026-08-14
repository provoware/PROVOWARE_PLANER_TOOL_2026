# CHANGELOG — PROVOWARE PLANER TOOL 2026

## 0.1.0-dev.1 — I000/I001 Foundation

- neuer maschinenlesbarer `PROJECT_CONTRACT.json`
- globale, versionierte PROVOWARE-Standards eingeführt
- zentrale UI-Abstände, Typografie-Rollen und flexible Schriftskalierung festgeschrieben
- barrierefreies Ampelsystem als Farbe + Symbol + Text standardisiert
- `VERSION.json` und `PROJEKTSTATUS.json` als kanonische Statusquellen eingeführt
- vollständiges `REPOSITORY_MANIFEST.json` für jede Iteration eingeführt
- unabhängigen `standard_validator` ohne Drittanbieter-Abhängigkeiten angelegt
- minimalen Entwicklungs- und Prüfautopiloten angelegt
- GitHub-Actions-Foundation-Qualifikation hinzugefügt
- README und TODO auf den neuen Foundation-Stand synchronisiert

## 0.2.0-dev.1 — I002
- Manifest- und Evidence-Kette ergänzt
- SHA-256-Inventar und Remote-Tree-Validierung ergänzt
- Fehlerbehandlungsstandard und Fehlerkatalog ergänzt
- qualifizierte Evidence wird vollautomatisch persistiert und nachgeprüft
- vollständige Repositoryprüfung je Iteration als Pflicht bestätigt
- gespeicherter Evidence-Stand erhält eine abschließende unabhängige Remote-Nachqualifikation ohne weitere automatische Repository-Änderung

## 0.3.0-dev.1 — I003
- Klick-&-Start-Orchestrator als deterministische Zustandsmaschine eingeführt
- verbindliche PRECHECK/ACTION/POSTCHECK-Kette implementiert
- reale Workspace-, Konfigurations- und SQLite-Prüfungen ergänzt
- sichere Recovery- und Quarantänepfade ergänzt
- Fault-Injection-Matrix mit Schutz vor realen Nutzerdaten eingeführt
- detailliertes maschinen- und laienlesbares Startfeedback ergänzt
- zweistufige Remote-Qualifikation mit automatischer Verifikation des Evidence-Commits eingeführt

## 0.4.0-dev.1 — I004
- GUI-unabhängigen Kalender-Domainkern eingeführt
- SQLite-Persistenz mit Constraints, Foreign Keys, WAL und Transaktionen ergänzt
- UTC-Zeitpersistenz und IANA-Zeitzonenvertrag ergänzt
- fünf editierbare Markierungstypen als Datenmodell eingeführt
- hashgebundene Migrationen mit automatischem Vor-Migrations-Backup eingeführt
- Optimistic Locking und Soft Delete ergänzt
- atomisches, SHA-256-validierbares Backup/Restore mit WAL-Schutz ergänzt
- modularen Kalender-Fehlerkatalog und globale Fehlercode-Eindeutigkeit ergänzt
- Autopilot um historische Pflichtgates erweitert
- zweistufige I004-Remotequalifikation ergänzt

## 0.5.0-dev.1 — I005
- CalendarQueryService und CalendarViewModel eingeführt
- PySide6/Qt-Kalenderoberfläche mit Tag/Woche/Monat/Jahr ergänzt
- fünf editierbare Markierungen mit atomarer Batch-Speicherung ergänzt
- Termin-Erstellung/-Bearbeitung ausschließlich über CalendarService angebunden
- Design-Tokens, Schriftskalierung, Ampelstatus, Tastatur und Accessible Names ergänzt
- native GUI-Abhängigkeiten explizit vertraglich gebunden und vor Qt-Import geprüft
- Offscreen-Matrix mit 112 GUI-Konfigurationen, Screenshots und Neustartpersistenz ergänzt
- historische Qualifikationskette um I005 erweitert

# CHANGELOG

## [Unreleased]

## [0.3.1-plan] - 2026-08-09

### Added
- ausführbarer Rollenprompt „ProvoWare Release Architect & Orchestrator PRO“ Version 2.0.
- `PROJEKTSTATUS.json` als zentrale maschinenlesbare Projektidentität.
- JSON-Schemas für Anforderungen, Tests, Evidence und Traceability Registry.
- erste maschinenlesbare Registry für `TODO-1.2`.
- Spezifikation des späteren Plan-Consistency-Gates.
- Prompt-Ausführungsbericht.

### Changed
- Entwicklungsprozess fordert jetzt Definition of Ready vor Produktimplementierung.
- Scope-Guard und Stopregel wurden verschärft.
- TODO 1.9 für Consistency-Gate nach Testgrundgerüst/Statusvertrag aufgenommen.
- Planversion auf 0.3.1-plan erhöht.

### Fixed
- „geplant“, „implementiert“, „verifiziert“ und „releasebereit“ sind in der Steuerung explizit getrennt.

### Security
- Evidence darf keine erfundenen Hashes/Commit-SHAs/Testresultate enthalten.

## [0.3.0-plan] - 2026-08-09

### Added
- PRO-Softwareentwicklungs-Masterplan.
- Traceability von Anforderung bis Release-Evidence.
- getrennte Fortschrittswerte für Umsetzung, Verifikation, Sicherheit, Dokumentation und Releasebereitschaft.
- Quellen-/Standardmatrix und Release-Checkliste.
- Failure-Injection-, SBOM-, Provenance- und Reproduzierbarkeitsplanung.
- präziser Vertrag für TODO 1.2.

### Changed
- Planungsmodell auf Software-Engineering-Governance für ein privates Offline-Tool fokussiert.

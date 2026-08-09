# AGENTS.md

## Steuerung
Vor jeder Änderung lesen: `PROJEKTSTATUS.json`, `DEVELOPMENT_STATUS.json`, `TODO.md`, aktive Traceability-Registry, relevante ADRs und `docs/EXPERTEN_ROLLENPROMPT_PRO_2.0.md`.

## Aktueller Produktstand
TODO 1.2 ist qualifiziert abgeschlossen. Nächster erlaubter Produkt-TODO ist **1.3 Frontend-Minimalstart**, noch nicht begonnen. Keine Punkte 1.4+ vorziehen.

## Traceability
Jeder aktive TODO benötigt `REQ → TEST → EVD`. Geplante Evidence darf nie als bestanden/verifiziert dargestellt werden.

## Backup
Vor Veränderung vorherige Datei unter `Backup/<vorherige-version>/` sichern.

## Architektur
`UI → validierter Tauri Command → Service → Core/OS`. Kein freier System-/Dateisystemzugriff aus der UI.

## Qualität
- Quelldatei <1000 Zeilen; Warnung ab 600.
- Bugfix → Regressionstest.
- Doku/Status/Manifest/Changelog sind Teil von Done.
- Entwicklungs-ZIP + Inventar + SHA-256 je Iteration.
- Keine 100-%-Behauptung ohne reale Evidence.

## Plan-Consistency-Gate
Nur spezifiziert. Implementierung erst TODO 1.9 nach 1.7 und 1.8.

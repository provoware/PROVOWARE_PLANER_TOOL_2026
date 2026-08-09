# AGENTS.md

## Steuerung
Vor jeder Änderung zuerst lesen:
1. `PROJEKTSTATUS.json`
2. `DEVELOPMENT_STATUS.json`
3. `TODO.md`
4. aktive Registry unter `manifests/traceability/`
5. `docs/EXPERTEN_ROLLENPROMPT_PRO_2.0.md`

## Aktueller Produkt-Scope
Nur **TODO 1.2 – Tauri-Minimalapp offline starten**.

Keine späteren Fachmodule, SQLite-Produktpersistenz, Plugins, Updates, Backupengine oder vollständiges Dashboard vorziehen.

## Traceability
Jeder aktive TODO benötigt `REQ → TEST → EVD`.
Geplante Tests/Evidence niemals als bestanden oder verifiziert darstellen.

## Backup
Vor Veränderung vorherige Datei nach `Backup/<vorherige-version>/` sichern.

## Architektur
`UI → validierter Tauri Command → Service → Core/OS`.
Kein freier System-/Dateisystemzugriff aus der UI.

## Qualität
- Quelldatei <1000 Zeilen; Warnung ab 600.
- Bugfix → Regressionstest.
- Doku/Status/Manifest/Changelog sind Teil von Done.
- ZIP + Inventar + SHA-256 je Iteration.
- Keine 100-%-Behauptung ohne reale Evidence.

## Plan-Consistency-Gate
Nur Spezifikation vorhanden. Implementierung erst TODO 1.9 nach 1.7 und 1.8.

## Vollständiger Ausführungsvertrag
Siehe `docs/EXPERTEN_ROLLENPROMPT_PRO_2.0.md`.

# Teil 1 — Anforderungen, Architektur, Tauri und Dateisystem

## 1. Anforderungsengineering
Anforderungen werden in Klassen geführt: `FUNK`, `UI`, `ACC`, `SEC`, `DATA`, `FS`, `PERF`, `OBS`, `REC`, `REL`, `COMP`, `MAINT`. Jede freigegebene Anforderung besitzt ID, Titel, Beschreibung, Quelle, Begründung, Priorität P0–P3, Status, messbare Akzeptanzkriterien, Abhängigkeiten, Risiken, betroffene Module, Test-IDs, Evidence-IDs und früheste Releasezuordnung.

### Priorität
- P0: Datenverlust, Security-Grenze, Startfähigkeit, Releaseintegrität.
- P1: Kernworkflow.
- P2: Produktivität/Komfort.
- P3: spätere Verbesserung.

### Änderungsimpact
Jede geänderte Anforderung wird auf `ADR → Code/Module → Tests → Migration → Dokumentation → Releaseversion` zurückverfolgt. Verwaiste Anforderungen ohne Tests und Bugfixe ohne Regressionstest blockieren das jeweilige Qualitätsgate.

## 2. Architekturentscheidungen
Ein ADR ist Pflicht bei Datenformaten, öffentlichen internen APIs, Sicherheitsgrenzen, Plugin-/Updateverträgen, Dateisystemstrategien, Build-/Releasearchitektur, Frameworkwechsel oder Migrationsstrategie.

Mindestfelder: ID, Status, Kontext, Entscheidung, Alternativen, Begründung, Risiken, Folgen, Migrations-, Test- und Security-Auswirkung sowie Vorgänger/Nachfolger.

## 3. Zielarchitektur
```text
ui/
  app/
  components/
  modules/
  styles/
  accessibility/
core/
  domain/
  validation/
  events/
  migrations/
services/
  filesystem/
  logging/
  backup/
  export/
  updater/
  plugins/
manifests/
  schemas/
  plugins/
  error-catalog/
  defaults/
src-tauri/
  src/
  capabilities/
tests/
  unit/
  integration/
  smoke/
  ui/
  fixtures/
```
Abhängigkeit: `UI → Commands/Services → Core`; Core kennt UI nicht.

## 4. Tauri-/Rust-Vertrauensgrenze
```text
HTML/TypeScript
  → validierter Tauri Command
  → Rust Command Boundary
  → Eingabevalidierung + Scopeprüfung
  → Service
  → Dateisystem / SQLite / OS
```
Jeder native Command ist klein, typisiert, validiert und scoped. Keine Shellstrings aus UI-Eingaben. Fachlogik wird außerhalb des Command-Adapters testbar gehalten. Nutzertexte enthalten keine unnötigen technischen Interna; technische Ursache und Korrelations-ID bleiben im Diagnosepfad.

## 5. CSP und lokale Assets
Die Offlinefassung startet mit möglichst restriktiver CSP. Remote-Skripte/CDNs/Fonts sind nicht Teil des Kernbetriebs. Jede CSP-Lockerung benötigt fachlichen Grund und bei Sicherheitsrelevanz ADR. Automatische Tests durchsuchen Runtime-Assets auf unerwartete `http://`, `https://` oder CDN-Referenzen.

## 6. Linux-WebView-Risiko
Tauri nutzt auf Linux die System-WebView-/WebKitGTK-Realität. Browser-Vorprüfungen in Firefox/Chromium sind nützlich, ersetzen aber keine reale Tauri-WebView-Abnahme. Deshalb früh minimale Webplattformfeatures, reale Zielsystemtests und dokumentierte WebKitGTK-Kompatibilitätsgrenzen.

## 7. AppImage-Portabilität
AppImage-Inhalt ist nicht der Nutzdatenbereich. Laufzeitdaten liegen im expliziten Projektroot. Der AppImage-Pfad kann als Anker genutzt werden; ein benachbarter Projektordner wird nur verwendet, wenn er gültig und beschreibbar ist. FUSE-/Extract-and-run-Fälle werden später in der Linux-Matrix geprüft.

## 8. Projektroot-Auflösung
Priorität:
1. explizit für die Session bestätigter Root,
2. gültiger portabler Root neben AppImage,
3. erreichbarer letzter Root nach Bestätigung,
4. Ordnerdialog.

Nie still in einen unerwarteten Ort schreiben.

## 9. Bootstrap-Schreibprobe
Prüfen: Existenz, Verzeichnistyp, Lesen, temporäre Datei anlegen, Inhalt schreiben, flush/sync soweit sinnvoll, zurücklesen, löschen, freien Speicher und Projekt-/Schema-Version. Das Ergebnis ist ein strukturiertes Checkobjekt, das später als Evidence gespeichert werden kann.

## 10. Pfadsicherheit
- Pfade normalisieren/canonicalisieren, soweit sicher möglich.
- Keine naive String-Präfixprüfung.
- `..`/Traversal blockieren.
- Symlinkfälle explizit behandeln.
- TOCTOU zwischen Prüfung und Nutzung berücksichtigen.
- Für kritische Writes wenn möglich Handle-/Descriptor-orientierte Verfahren bevorzugen.
- Ziel muss innerhalb erlaubter Wurzel bleiben.

## 11. I/O-Fehlerdomänen
Mindestens: `EACCES`, `EROFS`, `ENOSPC`, `ENOENT`, `EIO`, `EBUSY`, Lockfehler, Datenträgerentfernung, Zielwechsel und Teilwrite. Diese werden in stabile PROVOWARE-Fehlercodes übersetzt.

## 12. Sicherer Replace-Write
```text
validieren
→ temporäre Datei im selben Ziel-Dateisystem
→ schreiben
→ flush
→ optional fsync
→ atomar ersetzen/rename
→ Metadaten/Hash oder Rückleseprüfung
→ Event + UI-Bestätigung
```
Erfolg wird erst angezeigt, nachdem der Write bestätigt wurde. Append-TXT behält die Eingabe bei Fehlschlag im UI.

## 13. Single Writer / Locking
Pro Projekt standardmäßig eine schreibende Instanz. Lock besitzt Prozess-/Sessioninformationen und Zeit. Stale Locks werden nicht blind gelöscht; Wiederanlauf prüft, ob der Besitzer noch plausibel aktiv ist. Read-only-Zweitinstanz kann später separat spezifiziert werden.

## 14. Dateigrößen- und Modulregel
Hart <1000 Quellzeilen, Warnung ab 600, Ziel meist 100–400. Große Module werden vor dem Limit fachlich geschnitten. Split nicht nur nach Dateigröße, sondern nach Verantwortlichkeit, Stabilitätsgrenze und Testbarkeit.

## 15. Definition of Ready für Architektur-/I/O-TODOs
- Ziel eindeutig.
- Pfad-/Datenrisiko bekannt.
- Architekturgrenze benannt.
- Akzeptanzkriterien messbar.
- Positiv- und Fehlerfall vorhanden.
- keine offene Produktentscheidung.
- erforderliche Toolchain verfügbar.

## 16. Definition of Done
Implementierung, statische Checks, Funktionstest, Fehlerfall, Retest, Regression, Dateigrößenprüfung, Doku, Status/Changelog/Manifest, Evidence und Entwicklungsartefakt.

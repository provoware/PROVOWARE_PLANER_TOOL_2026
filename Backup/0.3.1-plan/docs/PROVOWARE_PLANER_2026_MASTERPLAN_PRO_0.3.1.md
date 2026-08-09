# PROVOWARE PLANER 2026 — MASTERPLAN PRO 0.3.1

**Planversion:** 0.3.1-plan  
**Stand:** 09.08.2026  
**Kanonisches Repository:** https://github.com/provoware/PROVOWARE_PLANER_TOOL_2026  
**Aktueller Produkt-TODO:** 1.2 – Tauri-Minimalapp offline starten

## 1. Einordnung
Dieser Stand erweitert die vollständige PRO-Basis `PROVOWARE_PLANER_2026_MASTERPLAN_PRO_0.3.0.md`. Die technischen Architektur-, Security-, Recovery-, Accessibility-, Test-, Supply-Chain- und Releaseentscheidungen aus 0.3.0 bleiben bestehen, soweit sie hier nicht ausdrücklich präzisiert werden.

0.3.1 ergänzt vor der ersten Produktimplementierung eine **maschinenlesbare Steuerungs- und Nachweisschicht**.

## 2. Neue kanonische Steuerung
Vor jeder Produktiteration werden in dieser Reihenfolge geprüft:
1. `PROJEKTSTATUS.json`
2. `DEVELOPMENT_STATUS.json`
3. `TODO.md`
4. aktive Registry unter `manifests/traceability/`
5. angenommene ADRs
6. dieser Masterplan
7. `AGENTS.md` und Entwicklerhandbuch

Bei Widersprüchen wird nicht still geraten; der Widerspruch wird sichtbar gemacht und nach der festgelegten Informationsrangfolge aufgelöst.

## 3. Projektidentität
`PROJEKTSTATUS.json` ist ab 0.3.1-plan Pflicht. Mindestfelder:
- kanonischer Projektname,
- Aliasnamen,
- Version,
- Repository,
- Hauptdatei,
- Status,
- aktueller TODO,
- nächster erlaubter Implementierungsschritt,
- letztes validiertes Plan-/Releaseartefakt.

Ziel ist eine automatische, konsistente und widerspruchsfreie Gesamtübersicht über den Projektzustand.

## 4. Traceability-Vertrag
Ab 0.3.1 gilt für den aktiven technischen TODO:

`REQ → TEST → EVD`

Später vollständig:

`Produktziel → REQ → ADR/Design → TODO → Implementierung → TEST → EVD → Gate → ART/REL`

### 4.1 Objektklassen
- `REQ-*` Anforderung
- `ADR-*` Architekturentscheidung
- `TODO-*` Umsetzung
- `TEST-*` Test
- `EVD-*` Evidence
- `BUG-*` Fehler
- `RISK-*` Risiko
- `MIG-*` Migration
- `ART-*` Artefakt
- `REL-*` Release

### 4.2 Harte Regeln
Unzulässig sind:
- TEST ohne existente REQ,
- EVD ohne existente TEST-/REQ-Bezüge,
- erledigter TODO ohne erforderliche verifizierte Evidence,
- Releaseartefakt ohne SHA-256,
- Bugfix ohne Regressionstest,
- erfundene Testresultate, Hashes, Commit-SHAs oder Screenshots.

`geplant` ist nicht `bestanden`.  
`implementiert` ist nicht `verifiziert`.  
`verifiziert` ist nicht automatisch `releasebereit`.

## 5. JSON-Schemas
Kanonische Schemas:
- `manifests/schemas/anforderung.schema.json`
- `manifests/schemas/test.schema.json`
- `manifests/schemas/evidenz.schema.json`
- `manifests/schemas/traceability-registry.schema.json`

Schemaformat: JSON Schema Draft 2020-12.

## 6. Erste Registry: TODO 1.2
Datei:
`manifests/traceability/TODO_1_2.registry.json`

### 6.1 Anforderungen
- `REQ-1.2-001` Tauri-Minimalapp lokal startbar — P0.
- `REQ-1.2-002` Offline- und Local-Asset-Start — P0.
- `REQ-1.2-003` sauberer Exit und Restart — P1.
- `REQ-1.2-004` Artefakt/Nachweis eindeutig bindbar — P1.

### 6.2 Geplante Tests
- `TEST-1.2-001` Rust/Tauri Compile Check.
- `TEST-1.2-002` lokaler Fenster-Start-Smoke.
- `TEST-1.2-003` Offline-Start-Smoke.
- `TEST-1.2-004` Remote-Ressourcen-Prüfung.
- `TEST-1.2-005` Exit-und-Restart-Smoke.
- `TEST-1.2-006` Paketinventar-und-Hash-Prüfung.

Alle Tests bleiben bis zur realen 1.2-Ausführung `geplant`.

### 6.3 Geplante Evidence
- `EVD-1.2-001` Toolchain-/Buildprüfbericht.
- `EVD-1.2-002` Start-/Offline-/Restart-Nachweis.
- `EVD-1.2-003` Paketinventar und SHA-256.

Alle Evidence bleibt bis zur realen Prüfung `geplant` und enthält vorab keine erfundenen Hashes oder Commit-SHAs.

## 7. Definition of Ready für TODO 1.2
1. Ziel eindeutig — erfüllt.
2. In-Scope/Out-of-Scope eindeutig — erfüllt.
3. Akzeptanzkriterien definiert — erfüllt.
4. REQ-IDs vorhanden — erfüllt.
5. TEST-IDs geplant — erfüllt.
6. EVD-IDs geplant — erfüllt.
7. Architekturgrenzen bekannt — erfüllt.
8. P0/P1-Risiken benannt — erfüllt.
9. Toolchain/Dependencies werden zu Beginn von 1.2 real erfasst.
10. keine offene Produktentscheidung blockiert.

Damit ist TODO 1.2 planungsseitig **bereit**, aber noch nicht implementiert oder verifiziert.

## 8. Scope TODO 1.2
### In Scope
- minimale Tauri-2-App,
- lokale HTML/CSS/TS-Seite,
- lokale Ressourcen,
- restriktive CSP-Grundlage,
- Compile-/Startprüfung,
- Offline-Start,
- Exit/Restart,
- Dokumentations-/Statusupdate,
- Entwicklungs-ZIP, Inventar, SHA-256,
- reale TEST-/EVD-Aktualisierung.

### Out of Scope
- SQLite-Produktpersistenz,
- Fachmodule,
- Pluginmanager,
- Updateengine,
- Backupengine,
- Projektroot-Schreiblogik,
- vollständiges Dashboard,
- Reminder.

## 9. Plan-Consistency-Gate
Der automatische Validator wird **noch nicht implementiert**.

Künftiger TODO:
**1.9 – Plan-Consistency-Gate v0**

Voraussetzungen:
- 1.7 Testgrundgerüst abgeschlossen,
- 1.8 maschinenlesbarer Build-/Statusvertrag abgeschlossen.

Spezifikation:
`docs/PLAN_CONSISTENCY_GATE_SPEZIFIKATION_0.1.md`

Der spätere Gate muss mindestens Schema-, Referenz-, Status- und Release-/Evidence-Widersprüche blockieren.

## 10. Backup-Vertrag
Vor Änderungen wird der vorherige Dateistand unter `Backup/<vorherige-version>/` gesichert. Der Rückfallstand wird nicht entfernt, bevor ein neuer validierter Nachrücker existiert.

Für die Umstellung auf 0.3.1-plan liegt die vorherige Steuerbasis unter `Backup/0.3.0-plan/`.

## 11. Rollenprompt
Der ausführbare Steuerprompt ist:
`docs/EXPERTEN_ROLLENPROMPT_PRO_2.0.md`

Er ergänzt insbesondere:
- Informationsrangfolge,
- Scope-Guard,
- Definition of Ready,
- Traceability-Pflicht,
- Evidence-Ehrlichkeit,
- Backupregel,
- Stopregel,
- mehrdimensionale Fortschrittsbewertung,
- verbindlichen Abschluss-/Releasebericht.

## 12. Fortschrittsmodell
Projektzustand wird getrennt bewertet:
- Planungsgrad,
- Umsetzungsgrad,
- Verifikationsgrad,
- Sicherheitsqualifikation,
- Dokumentationsgrad,
- Releasebereitschaft.

Ein hoher Planungsgrad darf keinen Produktfortschritt vortäuschen.

Aktuell:
- Planung: 98 %.
- Produktimplementierung: 0 %.
- Produktverifikation: 0 %.
- Security-Qualifikation: 0 %.
- Dokumentation: 98 %.
- Releasebereitschaft: 0 %.

## 13. Phase-1-Erweiterung
- [x] 1.1 Repository-/Schichtstruktur konzeptionell/lokal vorbereitet.
- [ ] **1.2 Tauri-Minimalapp offline starten.**
- [ ] 1.3 Frontend-Minimalstart.
- [ ] 1.4 lokale Assets/CSP vervollständigen.
- [ ] 1.5 Toolchain/Lockfiles.
- [ ] 1.6 Format/Lint/Typecheck/Rust Checks.
- [ ] 1.7 Testgrundgerüst.
- [ ] 1.8 maschinenlesbarer Build-/Statusvertrag.
- [ ] **1.9 Plan-Consistency-Gate v0.**

## 14. Direkt folgender technischer Schritt
Ausschließlich **TODO 1.2 – Tauri-Minimalapp offline starten**.

## 15. Stopregel
Sobald 1.2 implementiert, getestet, verifiziert, dokumentiert und als Entwicklungsartefakt paketiert ist, endet diese Produktiteration. 1.3 beginnt erst in einer neuen Iteration.

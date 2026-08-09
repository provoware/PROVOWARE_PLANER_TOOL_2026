# PROVOWARE PLANER 2026 — MASTERPLAN PRO 0.3.1

**Planversion:** 0.3.1-plan  
**Stand:** 09.08.2026  
**Kanonisches Repository:** https://github.com/provoware/PROVOWARE_PLANER_TOOL_2026  
**Statusnachtrag:** TODO 1.2 in Software 0.4.0-dev.1 qualifiziert abgeschlossen; nächster erlaubter TODO 1.3 ist noch nicht begonnen

## 1. Einordnung
Dieser Stand erweitert die vollständige PRO-Basis 0.3.0 um eine **maschinenlesbare Steuerungs- und Nachweisschicht**. Die ausführliche konsolidierte Fassung liegt zusätzlich in `PROVOWARE_PLANER_2026_MASTERPLAN_PRO_0.3.1_VOLLSTAND.md`.

## 2. Neue kanonische Steuerung
Vor jeder Produktiteration:
1. `PROJEKTSTATUS.json`
2. `DEVELOPMENT_STATUS.json`
3. `TODO.md`
4. aktive Registry unter `manifests/traceability/`
5. angenommene ADRs
6. Masterplan
7. `AGENTS.md` / Entwicklerhandbuch

Widersprüche werden sichtbar gemacht und nicht still übergangen.

## 3. Projektidentität
`PROJEKTSTATUS.json` ist Pflicht und hält Projektname, Aliasse, Version, Repository, Hauptdatei, Status, aktuellen TODO und letztes validiertes Plan-/Releaseartefakt.

## 4. Traceability-Vertrag
`REQ → TEST → EVD`

Später vollständig:
`Produktziel → REQ → ADR/Design → TODO → Implementierung → TEST → EVD → Gate → ART/REL`

Unzulässig:
- TEST ohne existente REQ,
- EVD ohne TEST-/REQ-Bezug,
- erledigter TODO ohne Required Evidence,
- Release ohne SHA-256,
- Bugfix ohne Regressionstest,
- erfundene Testresultate/Hashes/Commit-SHAs.

## 5. JSON-Schemas
- `manifests/schemas/anforderung.schema.json`
- `manifests/schemas/test.schema.json`
- `manifests/schemas/evidenz.schema.json`
- `manifests/schemas/traceability-registry.schema.json`

## 6. TODO 1.2 Registry
`manifests/traceability/TODO_1_2.registry.json`

Anforderungen:
- REQ-1.2-001 Tauri-Minimalapp lokal startbar — P0.
- REQ-1.2-002 Offline-/Local-Asset-Start — P0.
- REQ-1.2-003 Exit/Restart — P1.
- REQ-1.2-004 Artefakt/Nachweis bindbar — P1.

Geplante Tests:
- TEST-1.2-001 Compile Check.
- TEST-1.2-002 Fenster-Start-Smoke.
- TEST-1.2-003 Offline-Smoke.
- TEST-1.2-004 Remote-Ressourcen-Prüfung.
- TEST-1.2-005 Exit/Restart.
- TEST-1.2-006 Paket/Hash.

Geplante Evidence:
- EVD-1.2-001 Toolchain-/Buildbericht.
- EVD-1.2-002 Start-/Offline-/Restart-Nachweis.
- EVD-1.2-003 Paketinventar/SHA-256.

Alle Tests/Evidence bleiben bis realer Ausführung ausdrücklich `geplant`.

## 7. Definition of Ready
Planungsseitig erfüllt: Ziel, Scope, Akzeptanzkriterien, REQ-, TEST- und EVD-IDs sowie Architekturgrenzen sind definiert. Toolchain/Dependencies werden zu Beginn der realen 1.2-Implementierung erfasst.

## 8. Scope TODO 1.2
In Scope: minimale Tauri-2-App, lokale Ressourcen, restriktive CSP-Grundlage, Compile/Start, Offline, Exit/Restart, Status/Doku, ZIP/Inventar/SHA-256, reale Evidence.

Out of Scope: SQLite-Produktpersistenz, Fachmodule, Plugins, Update, Backupengine, Projektroot-Schreiblogik, vollständiges Dashboard, Reminder.

## 9. Plan-Consistency-Gate
Nur spezifiziert. Implementierung als **TODO 1.9**, erst nach:
- 1.7 Testgrundgerüst,
- 1.8 maschinenlesbarer Build-/Statusvertrag.

## 10. Backup-Vertrag
Vor Änderungen vorherigen Stand nach `Backup/<vorherige-version>/` sichern. Für 0.3.1 liegt die 0.3.0-Basis unter `Backup/0.3.0-plan/`.

## 11. Rollenprompt
`docs/EXPERTEN_ROLLENPROMPT_PRO_2.0.md`

## 12. Fortschritt
- Planung 98 %
- Produktimplementierung 0 %
- Produktverifikation 0 %
- Security-Qualifikation 0 %
- Dokumentation 98 %
- Releasebereitschaft 0 %

## 13. Phase 1
- [x] 1.1 Repository-/Schichtstruktur vorbereitet.
- [x] **1.2 Tauri-Minimalapp offline starten.** — qualifiziert in 0.4.0-dev.1
- [ ] 1.3 Frontend-Minimalstart.
- [ ] 1.4 lokale Assets/CSP.
- [ ] 1.5 Toolchain/Lockfiles.
- [ ] 1.6 Qualitätschecks.
- [ ] 1.7 Testgrundgerüst.
- [ ] 1.8 Build-/Statusvertrag.
- [ ] **1.9 Plan-Consistency-Gate v0.**

## 14. Nächster Schritt
Ausschließlich **TODO 1.3 – Frontend-Minimalstart**; noch nicht begonnen.

## 15. Stopregel
Nach vollständigem Done von 1.2 endet die Iteration. 1.3 beginnt separat.

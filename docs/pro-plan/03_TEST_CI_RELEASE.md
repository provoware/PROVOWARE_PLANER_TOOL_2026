# Teil 3 — Tests, CI, Supply Chain und Release

## 1. Testarchitektur
Die Qualitätspyramide wird um Desktop-, Daten- und Releaseprüfungen erweitert:
1. Format.
2. Frontend-Lint.
3. Frontend-Typecheck.
4. Rust fmt/check.
5. Clippy.
6. Unit.
7. Property-/Invariant-Tests, wo sinnvoll.
8. Integration.
9. Dateisystem-/SQLite-Tests.
10. Tauri Mock Runtime.
11. UI-Komponententests.
12. E2E/WebDriver.
13. Paket-Smoke-Test.
14. Offline-Test.
15. Failure Injection.
16. reale Linux-Abnahme.

Tauri dokumentiert Mock-Runtime-Unterstützung sowie End-to-End über WebDriver; deshalb wird beides gezielt eingesetzt statt ausschließlich Browser-Tests zu verwenden.

## 2. Positiv-, Negativ- und Regressionstest
P0/P1-Funktionen brauchen mindestens Happy Path, definierten Fehlerpfad und Wiederanlauf. Jeder behobene Bug erhält nach Möglichkeit einen Regressionstest, der vor dem Fix rot und danach grün wäre.

## 3. Failure-Injection-Matrix
Pflichtfälle über die Entwicklung verteilt:
- Projektroot fehlt/read-only.
- `ENOSPC`.
- `EIO`/simulierter I/O-Fehler.
- Datenträger verschwindet.
- Datei gesperrt.
- ungültiges JSON.
- SQLite beschädigt.
- DB-Lock.
- Prozesskill während Write.
- Prozesskill während Migration.
- Prozesskill während Backup.
- Logziel read-only/voll.
- defektes Pluginmanifest.
- Pluginfehler.
- Traversal/Symlink.
- lange/Unicode-Pfade.
- zweiter Start.
- FUSE-/AppImage-Startproblem.
- DST-/Zeitzonenrandfall.

## 4. Test-Evidence
Qualifizierende Testläufe speichern: `test_run_id`, Commit, Umgebung, Start/Ende, Gesamt/Pass/Fail/Skip, Artefakte, Loghash und Ergebnis. Dadurch wird ein grüner Status später einem konkreten Quell- und Artefaktstand zugeordnet.

## 5. CI-Pipeline PRO
```text
00 Metadata/Manifest
01 Format
02 Frontend Lint
03 Frontend Typecheck
04 Rust fmt
05 Rust check
06 Clippy
07 Unit
08 Integration
09 Security Static
10 Dependency Review/Audit
11 Tauri Mock Tests
12 UI Smoke
13 Build
14 AppImage Package
15 AppImage Starttest
16 Offline-Test
17 Failure-Smoke
18 SBOM
19 SHA-256
20 Provenance/Attestation
21 Docs/Schema Validation
22 Release-Evidence Bundle
23 Stable Gate
```
Jobnamen bleiben eindeutig, damit Required Status Checks nicht mehrdeutig werden.

## 6. GitHub-Governance
Für das Privatprojekt genügt: `main` als qualifizierte Basis und kurze `agent/*`, `feature/*`, `fix/*`, `docs/*`-Branches. Kein langlebiger develop-Branch ohne konkreten Nutzen.

Nach Aufbau der CI: PR vor Merge, Required Checks, Force-Push-Schutz, Schutz vor Branchlöschung und optional signierte Commits. GitHub Rulesets können zusätzlich Code-Scanning- und Quality-Anforderungen einbeziehen.

## 7. Pull-Request-Vertrag
PR beschreibt: Was? Warum? TODO/REQ-ID? Risiken? Tests? Evidence? Migration? Doku? Rollback? Damit wird die Änderung selbst zum auditierbaren Entwicklungsobjekt.

## 8. Dependency-Aufnahmevertrag
Neue Abhängigkeit dokumentiert Zweck, Alternative, Lizenz, Version, Quelle, Wartungsaktivität, Security-Historie, transitive Abhängigkeiten, Größen-/Buildauswirkung und Offline-Verfügbarkeit. Lockfiles werden committed und im Release-Evidence berücksichtigt.

## 9. Dependency Security
Spätere CI nutzt je nach Verfügbarkeit GitHub Dependency Review, CodeQL für unterstützte Sprachen/Rust, RustSec/cargo-audit oder geeignete Alternative und optional OpenSSF Scorecard zur Vorbewertung kritischer OSS-Komponenten. Ein neuer kritischer bekannter Vulnerability-Befund blockiert das Release-Gate.

## 10. GitHub Actions Security
Drittanbieter-Actions auf vollständige Commit-SHAs pinnen. Tags allein gelten nicht als unveränderliche Referenz. Workflow-Berechtigungen nach Least Privilege vergeben; unnötige Schreibrechte vermeiden.

## 11. Reproduzierbarer Build
Buildmanifest pro Release: Source-Commit, Source-Tree/Hash, Toolchain, Rust-/Node-/Package-Manager-Version, Lockfile-Hashes, Tauri-Version, Target, Buildbefehle, relevante Umgebung, `SOURCE_DATE_EPOCH` soweit genutzt und Artefakt-Hashes.

Reifestufen:
- R0 dokumentierter Build.
- R1 definierte Toolchain reproduzierbar buildbar.
- R2 deterministische relevante Metadaten.
- R3 Zweitbuild in sauberer Umgebung + Vergleich.
- R4 reproduzierbarer Release als Gate, soweit technisch praktikabel.

Keine 100-%-Behauptung, bevor reale Zweitbuilds dies tragen.

## 12. SBOM
Releasekandidat erhält maschinenlesbare SBOM. Bevorzugte Standards abhängig von Toolunterstützung: SPDX 3.0 oder CycloneDX 1.7. SBOM wird an das konkrete Artefakt/Release gebunden, nicht nur lose im Repository abgelegt.

## 13. Provenance/SLSA
SLSA 1.2 ist die aktuelle freigegebene Referenz. PROVOWARE übernimmt zunächst Provenance-Grunddaten und erweitert Build-/Source-Garantien schrittweise. Kein SLSA-Level als Claim, solange dessen Kriterien nicht nachweisbar erfüllt sind.

## 14. GitHub Artifact Attestations
Bei GitHub Actions können Build-Provenance und SBOM-Nachweise kryptografisch attestiert werden. Attestierung allein ist kein Nutzen; Verifikation wird deshalb Bestandteil des Release-Gates. Releasekette: `Commit → Build Run → Tests → Artefakt → SHA-256 → SBOM → Provenance/Attestation → Verify → Qualification Receipt → Stable`.

## 15. Releaseklassen
- Development: unvollständig erlaubt, kein Stable-Claim.
- Alpha: Kernpfade vorhanden, Verträge noch veränderlich.
- Beta: Featureumfang weitgehend geschlossen, Migration/Recovery intensiv geprüft.
- RC: kein bekannter P0/P1-Blocker; vollständiger Qualifikationslauf.
- Stable: qualifiziertes RC-Artefakt wird promoviert, nicht ungeprüft neu gebaut, soweit die Pipeline dies unterstützt.

## 16. Stable-Promotion-Prinzip
Der größte Releasefehler wäre, ein grünes RC zu testen und danach für Stable einen anderen Binärstand neu zu bauen. Ziel: Stable-Promotion übernimmt exakt das qualifizierte Artefakt, aktualisiert nur zulässige externe Metadaten und prüft Hash/Signatur erneut.

## 17. Release-Gate
Build: Toolchain/Lockfiles/Build/AppImage/Start. Funktion: Kern-E2E/Persistenz. Daten: Migration/Backup/Restore/Integrität. Security: kein P0, CSP/Dependency-/Codeprüfung. A11y: Tastatur/Fokus/Contrast/Schrift. Supply Chain: Hash/Manifest/SBOM/Provenance gemäß Phase. Doku: README/Handbook/Status/TODO/Changelog/Manifest/Notes. Evidence: Testbericht/Umgebung/Commit/Artefakt/Restunsicherheiten.

## 18. Qualitätsmetriken
Nicht eine Zahl entscheidet: offene P0/P1, Requirement-Test-Coverage, Regression-Coverage, relevante Passrate, A11y-Core-Flow, Backup/Restore, Dependency Risk, Docs Drift und Artifact Traceability. Codecoverage bleibt Hilfsmetrik und darf nicht durch wertlose Tests künstlich optimiert werden.

## 19. Changelog/Versionierung
SemVer 2.0.0 als Versionsvertrag, sobald öffentliche API/Datenverträge definiert sind. Während 0.x ist Breaking Change möglich, aber Migration/Doku bleiben Pflicht. Changelog menschenlesbar nach Kategorien `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`; Commitlog ist kein Ersatz.

## 20. Wartung nach 1.0
Incidentprozess, Bug→Regression, Dependencyupdates, Migrationen, Deprecation, Backupkompatibilität, Supportmatrix, technische Schulden als `DEBT-*` und Langzeit-Evidence. Persistente Datenformate werden nie still in unbekannte Zukunftsversionen umgeschrieben.

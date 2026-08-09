# PROVOWARE PLANER 2026 — RELEASE-CHECKLISTE PRO

## P0 Stop-Gates
- [ ] Kein offener Datenverlust-/Korruptionsblocker.
- [ ] Kein offener Security-P0.
- [ ] Kein ungeklärter Migrationsfehler.
- [ ] Backup/Restore gemäß Releaseumfang bestanden.
- [ ] Kern-E2E bestanden.
- [ ] Offline-Start bestanden.
- [ ] AppImage-Start bestanden.
- [ ] Artefakt-Hash vorhanden.
- [ ] Commit ↔ Build ↔ Artefakt ↔ Evidence eindeutig.

## Qualität
- [ ] Format/Lint/Typecheck.
- [ ] Rust check/clippy.
- [ ] Unit.
- [ ] Integration.
- [ ] Fehlerfälle.
- [ ] Regression.
- [ ] UI/E2E.
- [ ] Accessibility-Kernflow.
- [ ] Linux-Matrix entsprechend Releasephase.

## Supply Chain
- [ ] Lockfiles.
- [ ] Dependency Review/Audit.
- [ ] Code Scanning gemäß Phase.
- [ ] SBOM.
- [ ] Buildmanifest.
- [ ] Provenance/Attestation gemäß Phase.
- [ ] Actions SHA-gepinnt.

## Dokumentation
- [ ] README.
- [ ] AGENTS.
- [ ] Handbook.
- [ ] Status.
- [ ] TODO.
- [ ] Changelog.
- [ ] Manifest.
- [ ] Release Notes.
- [ ] bekannte Restunsicherheiten.

## Stable
- [ ] RC vollständig qualifiziert.
- [ ] Stable verwendet qualifiziertes Artefakt statt ungeprüftem Neubuild.
- [ ] Hash/Signatur nach Promotion erneut geprüft.

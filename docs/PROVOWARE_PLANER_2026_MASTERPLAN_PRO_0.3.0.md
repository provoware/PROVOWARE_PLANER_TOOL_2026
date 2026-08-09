# PROVOWARE PLANER 2026 — SOFTWAREENTWICKLUNGS-MASTERPLAN PRO

**Version:** 0.3.0-plan  
**Stand:** 2026-08-09  
**Status:** kanonische Planungs-/Architekturbaseline; keine Produktimplementierung  
**Nächster Produkt-TODO:** ausschließlich **1.2 Tauri-Minimalapp offline starten**.

## Zweck
Dieser PRO-Plan konsolidiert die bisherigen Masterdokumente und erweitert sie um einen vollständigen Software-Engineering-Lebenszyklus für ein privates, offline-first Linux-Desktop-Tool.

## Kanonische Entwicklungskette
`Produktziel → Anforderung → ADR/Design → TODO → Implementierung → statische Prüfung → Funktionstest → Fehler-/Negativtest → Regression → Evidence → Release-Gate → Artefakt + Hash + SBOM + Provenance → Stable → Wartung/Migration`

## Fünf getrennte Fortschrittswerte
Ein einzelner Prozentwert ist nicht ausreichend. Das Projekt führt getrennt:
1. Umsetzungsgrad,
2. Verifikationsgrad,
3. Sicherheitsgrad,
4. Dokumentationsgrad,
5. Releasebereitschaft.

P0-Blocker können die Releasebereitschaft unabhängig vom Umsetzungsgrad auf 0 setzen.

## Traceability
Projektobjekte erhalten stabile IDs: `REQ-*`, `NFR-*`, `ADR-*`, `RISK-*`, `THREAT-*`, `CTRL-*`, `TODO-*`, `TEST-*`, `BUG-*`, `MIG-*`, `REL-*`, `ART-*`, `EVD-*`, `INC-*`, `DEBT-*`.

Beispiel: `REQ-FS-004 → ADR-0007 → TODO-3.5 → TEST-FS-021/022 → EVD-3.5-001 → REL-0.5.0`.

## Harte Produktgrenzen
- offline/local-first,
- keine Konto-/Cloudpflicht,
- keine Runtime-CDNs,
- kein automatisches sudo,
- Least Privilege,
- UI ohne freien Systemzugriff,
- Never-Crash-UX für erwartbare Fehler,
- Accessibility ab Fundament,
- versionierte Migrationen und validierte Backups,
- keine Datei >1000 Zeilen; Warnung ab 600,
- exakt ein primärer TODO pro Iteration,
- keine späteren Features vorziehen.

## Rollenmodell für das Privatprojekt
Keine künstliche Unternehmens-RACI. Stattdessen getrennte Prüfperspektiven: Produkt, Architektur, Implementierung, QA, Security, Accessibility, Datenintegrität, Release und Wartung. Eine Person kann alle Rollen ausfüllen; die Prüffragen und Nachweise bleiben getrennt.

## Dokumentteile
- [Teil 1 — Anforderungen, Architektur, Tauri und Dateisystem](pro-plan/01_GRUNDLAGEN_ARCHITEKTUR.md)
- [Teil 2 — Persistenz, Security, Recovery und Accessibility](pro-plan/02_SICHERHEIT_DATEN_RECOVERY.md)
- [Teil 3 — Tests, CI, Supply Chain und Release](pro-plan/03_TEST_CI_RELEASE.md)
- [Teil 4 — Roadmap, Gates und TODO 1.2](pro-plan/04_ROADMAP_TODO_1_2.md)
- [Quellen- und Standardmatrix](PROVOWARE_PLANER_2026_QUELLEN_STANDARDMATRIX_0.3.0.md)
- [Release-Checkliste](PROVOWARE_PLANER_2026_RELEASE_CHECKLISTE_0.3.0.md)

## Kanonische Architekturentscheidungen
- ADR-0001: Tauri 2 Hauptpfad; Electron nur validierter Fallback.
- ADR-0002: SQLite für strukturierten Kernzustand; TXT nur für bewusst einfache Listen.
- ADR-0003: Projektroot als primäre Schreibgrenze.
- ADR-0004: UI besitzt keinen freien Dateisystemzugriff.
- ADR-0005: AppImage + externer portabler Datenbereich.
- ADR-0006: ein Ereignismodell → JSONL + menschenlesbare Sicht.
- ADR-0007: Plugins zunächst deklarativ/registriert, keine freie Shell.
- ADR-0008: Release-Evidence an Commit und Artefakt-Hash binden.

## Quellenstatus 2026
- NIST SSDF 1.1 ist stabile Basis; SSDF 1.2 ist Draft.
- SLSA 1.2 ist freigegeben/aktuell.
- SPDX 3.0 und CycloneDX 1.7 sind aktuelle SBOM-Referenzen.
- OWASP ASVS 5.0.0 ist aktuelle stabile ASVS-Fassung.
- WCAG 2.2 ist W3C Recommendation.
- Tauri 2 dokumentiert Mock-Runtime-Tests und WebDriver-E2E.
- GitHub Artifact Attestations können signierte Build-Provenance und SBOM-Nachweise erzeugen.

## Direkt folgender technischer Entwicklungsschritt
**TODO 1.2 – Tauri-Minimalapp offline starten.** Keine SQLite-, Plugin-, Backup-, Update- oder Fachmodulfunktion vorziehen.

## Alternative Verbesserung mit hohem Nutzen und geringem Risiko
Vor dem ersten 1.2-Code einen minimalen `REQ/TEST/EVIDENCE`-Datensatz für 1.2 anlegen. Das ändert keine Runtime-Funktion, macht aber den ersten Build bereits vollständig rückverfolgbar.

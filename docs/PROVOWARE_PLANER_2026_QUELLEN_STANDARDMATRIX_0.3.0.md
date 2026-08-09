# PROVOWARE PLANER 2026 — QUELLEN- UND STANDARDMATRIX

Version: 0.3.0-plan  
Stand: 2026-08-09

| Quelle | Status 2026 | Verwendung im Projekt |
|---|---|---|
| [NIST SSDF 1.1 (final)](https://csrc.nist.gov/pubs/sp/800/218/final) | externe Referenz | Secure-SDLC-Grundstruktur; sichere Entwicklungspraktiken in den SDLC integrieren. |
| [NIST SSDF 1.2 (Draft, Stand 2026)](https://csrc.nist.gov/pubs/sp/800/218/r1/ipd) | externe Referenz | Nur Beobachtungsquelle; nicht als verbindliche Norm behandeln, solange Draft. |
| [OWASP SAMM](https://owaspsamm.org/model/) | externe Referenz | Governance, Design, Implementation, Verification, Operations als Security-Reifeachsen. |
| [OWASP ASVS 5.0](https://owasp.org/www-project-application-security-verification-standard/) | externe Referenz | Technische Sicherheitsanforderungen und verifizierbare Controls. |
| [OWASP Threat Modeling](https://cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html) | externe Referenz | Threat Modeling früh und wiederkehrend im SDLC. |
| [Tauri 2 CSP](https://v2.tauri.app/security/csp/) | externe Referenz | Restriktive CSP; keine Remote-Skripte/CDNs. |
| [Tauri 2 Tests](https://v2.tauri.app/develop/tests/) | externe Referenz | Mock Runtime sowie End-to-End über WebDriver auf Linux/Windows. |
| [SQLite WAL](https://sqlite.org/wal.html) | externe Referenz | WAL nur nach Dateisystem-/Portabilitätsprüfung; kein Netzwerkdateisystem. |
| [SQLite Integrity PRAGMAs](https://www.sqlite.org/pragma.html) | externe Referenz | quick_check, integrity_check und foreign_key_check als Integritätsstufen. |
| [SQLite Backup API](https://www.sqlite.org/backup.html) | externe Referenz | Konsistente Live-Snapshots statt blindem Kopieren geöffneter DB. |
| [AppImage Environment](https://docs.appimage.org/packaging-guide/environment-variables.html) | externe Referenz | APPIMAGE als Pfadanker; Type-2 bevorzugen. |
| [AppImage User Guide](https://docs.appimage.org/user-guide/index.html) | externe Referenz | Portable Mode und FUSE-/Startprobleme berücksichtigen. |
| [WCAG 2.2](https://www.w3.org/TR/WCAG22/) | externe Referenz | AA-Ziel, Fokus nicht verdeckt, Drag-Alternative, Mindestzielgröße. |
| [WAI ARIA APG](https://www.w3.org/WAI/ARIA/apg/) | externe Referenz | Tastatur- und Komponentenverhalten für komplexe Widgets. |
| [GitHub Rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets) | externe Referenz | Required checks, PR-Pflicht, signierte Commits, Force-Push-Schutz. |
| [GitHub Secure Actions](https://docs.github.com/en/actions/reference/security/secure-use) | externe Referenz | Actions auf vollständige Commit-SHAs pinnen. |
| [GitHub Dependency Review](https://docs.github.com/en/pull-requests/how-tos/review-pull-requests/reviewing-dependency-changes-in-a-pull-request) | externe Referenz | Neue/aktualisierte Dependencies vor Merge bewerten. |
| [GitHub CodeQL](https://docs.github.com/en/code-security/concepts/code-scanning/codeql/codeql-code-scanning) | externe Referenz | Statische Sicherheitsanalyse; Rust wird unterstützt. |
| [GitHub Artifact Attestations](https://docs.github.com/en/actions/concepts/security/artifact-attestations) | externe Referenz | Signierte Build-Provenance und SBOM-Attestierungen via Sigstore. |
| [SLSA 1.2](https://slsa.dev/spec/v1.2/) | externe Referenz | Aktuelle freigegebene SLSA-Spezifikation; Build- und Source-Track. |
| [SPDX 3.0](https://spdx.dev/use/specifications/) | externe Referenz | Aktuelle SPDX-Spezifikation; ISO/IEC 5962:2021-Familie. |
| [CycloneDX 1.7](https://cyclonedx.org/specification/overview/) | externe Referenz | Aktuelle CycloneDX-Spezifikation für SBOM/weitere BOM-Typen. |
| [Reproducible Builds](https://reproducible-builds.org/de/docs/) | externe Referenz | Deterministische Builds; SOURCE_DATE_EPOCH, stabile Reihenfolge, Umgebung. |
| [OpenSSF Scorecard](https://openssf.org/projects/scorecard/) | externe Referenz | Bewertung von OSS-Abhängigkeiten und Repository-Sicherheitspraktiken. |
| [Rust Clippy](https://doc.rust-lang.org/stable/clippy/index.html) | externe Referenz | Korrektheits-, Suspicious-, Style-, Complexity- und Performance-Lints. |
| [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html) | externe Referenz | Versionsvertrag; 0.y.z vor stabiler öffentlicher API. |
| [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/) | externe Referenz | Menschenlesbares Änderungsprotokoll mit Unreleased/Added/Changed/Fixed/Security. |
| [CISA Product Security Bad Practices](https://www.cisa.gov/news-events/alerts/2025/01/17/cisa-and-fbi-release-updated-guidance-product-security-bad-practices) | externe Referenz | Security-by-Design über den gesamten Produktlebenszyklus. |

## Entscheidungsregel
- Finale/stabile Spezifikation darf als feste Referenz dienen.
- Drafts nur als Frühindikator; keine harte Compliance darauf aufbauen.
- Community-/Toolsignale sind Ergänzung, nicht normative Basis.
- Jede konkrete Toolversion wird erst beim Implementierungs-TODO gepinnt und im Buildmanifest festgehalten.

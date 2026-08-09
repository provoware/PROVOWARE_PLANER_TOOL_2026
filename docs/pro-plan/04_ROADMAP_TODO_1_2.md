# Teil 4 — Roadmap, Gates und TODO 1.2

## Phase 0 – Planungs- und Repository-Baseline
- [x] 0.1 Produktziele/Nicht-Ziele.
- [x] 0.2 Tauri-2-Hauptpfad.
- [x] 0.3 Datenklassifikation.
- [x] 0.4 Softwareentwicklungs-Masterplan PRO.
- [x] 0.5 Quellen-/Standardmatrix.
- [x] 0.6 Planungsbaseline auf GitHub-Dokumentationsbranch synchronisiert.

## Phase 1 – Walking Skeleton
- [x] 1.1 Repository-/Schichtstruktur konzeptionell/lokal vorbereitet.
- [ ] **1.2 Tauri-Minimalapp offline starten.**
- [ ] 1.3 Frontend-Minimalstart.
- [ ] 1.4 lokale Assets/CSP.
- [ ] 1.5 Toolchain/Lockfiles.
- [ ] 1.6 Format/Lint/Typecheck/Rust Checks.
- [ ] 1.7 Testgrundgerüst.
- [ ] 1.8 Build-/Statusvertrag.
Gate: lokales Tauri-Fenster startet reproduzierbar ohne Runtime-Netzwerk.

## Phase 2 – Bootstrap/Crashschutz
2.1 globaler Fehlerfänger; 2.2 Startup State Machine; 2.3 Checkpoints; 2.4 Fortschritt; 2.5 Statusmodell; 2.6 Fehlerkatalog; 2.7 Safe/Recovery Shell; 2.8 Start-Evidence.
Gate: simulierter Bootstrapfehler bleibt diagnostizierbar.

## Phase 3 – Projektroot/I-O
3.1 AppImage-Pfadanker; 3.2 Rootmanifest/Projekt-ID; 3.3 Rootauflösung; 3.4 Schreibprobe; 3.5 Scope; 3.6 Read-only; 3.7 Single-Writer-Lock; 3.8 Stale-Lock; 3.9 Disk-full; 3.10 Device-loss; 3.11 Traversal/Symlink.
Gate: erlaubter Pfad funktioniert, verbotener Pfad wird reproduzierbar blockiert.

## Phase 4 – Logging/Debug
4.1 Event-ID/Sequence; 4.2 Correlation; 4.3 JSONL; 4.4 TXT; 4.5 Rotation; 4.6 Maskierung; 4.7 Logger-Ausfall; 4.8 Debugbundle; 4.9 Fehlerkatalogbindung.

## Phase 5 – Persistenz/Integrität
5.1 SQLite-Abstraktion; 5.2 Journalmodus-Matrix; 5.3 Schema; 5.4 Migration Runner; 5.5 Pre-Migration Backup; 5.6 quick/integrity/foreign-key checks; 5.7 Recoverymarker; 5.8 Killtests; 5.9 Restorefixture.

## Phase 6 – Designsystem/Accessibility
6.1 Tokens; 6.2 Typografie; 6.3 Abstände; 6.4 Controls; 6.5 Fokus; 6.6 Dialoge; 6.7 Themes; 6.8 High Contrast; 6.9 Schriftgröße; 6.10 Reduced Motion; 6.11 A11y-Smoke.

## Phase 7 – Dashboard Shell
7.1 Header; 7.2 linkes 2er-Grid; 7.3 Hauptlayout; 7.4 rechte Sidebar; 7.5 Fußleiste; 7.6 globale Statuskarte; 7.7 Navigation; 7.8 Shortcuts; 7.9 responsive Mindestansicht.

## Phase 8 – Modulregistry
8.1 Modulvertrag; 8.2 Schema; 8.3 Registry; 8.4 Aktivstatus; 8.5 Reihenfolge; 8.6 Fehlerisolation; 8.7 Rechteanzeige; 8.8 Persistenz.

## Phase 9 – Einzeiler
9.1 Standardfelder; 9.2 Dateiregistry; 9.3 Normalisierung; 9.4 Append-Service; 9.5 Write-Verifikation; 9.6 Savefeedback; 9.7 eigene Felder; 9.8 Kollisionsschutz; 9.9 I/O-Recovery; 9.10 E2E.

## Phase 10 – Kalender/Reminder
10.1 Zeitmodell; 10.2 Monat; 10.3 CRUD; 10.4 Zeitzonenmodell; 10.5 DST; 10.6 Reminder-State; 10.7 In-App-Reminder; 10.8 verpasste Reminder; 10.9 Terminübersicht; 10.10 Tests.

## Phase 11 – To-Do
11.1 Modell; 11.2 CRUD; 11.3 Priorität; 11.4 Fälligkeit; 11.5 Filter; 11.6 Archiv; 11.7 Restore; 11.8 Dashboard; 11.9 Tests.

## Phase 12 – Notizen
12.1 Entwicklerinfo-TXT; 12.2 Schnellnotiz; 12.3 Dashboardauszug; 12.4 interne Toolnotiz; 12.5 Persistenz; 12.6 Trennungstest.

## Phase 13 – Einstellungen
13.1 Laie; 13.2 Profi; 13.3 Experte; 13.4 Defaultschema; 13.5 Theme/Schrift; 13.6 Pfad/Capability-Sicht; 13.7 Logging; 13.8 Import/Reset; 13.9 gefährliche Aktionen.

## Phase 14 – Backup/Restore PRO
14.1 Snapshotvertrag; 14.2 SQLite Backup; 14.3 Dateisnapshot; 14.4 Manifest; 14.5 Hash; 14.6 Rotation; 14.7 Restore; 14.8 Pre-Restore-Backup; 14.9 Restore-Verify; 14.10 Kill/Device-loss.

## Phase 15 – Export/Suche
15.1 TXT; 15.2 JSON; 15.3 CSV; 15.4 Projekt-ZIP; 15.5 Exportmanifest; 15.6 Suche; 15.7 Index; 15.8 Performance; 15.9 Fehlerfälle.

## Phase 16 – Plugins
16.1 API-Version; 16.2 Manifest; 16.3 Validator; 16.4 Permissionmodell; 16.5 Hash; 16.6 Signaturstatus; 16.7 Lifecycle; 16.8 Isolation; 16.9 Safe Mode; 16.10 Beispielplugin.

## Phase 17 – Update/Supply Chain
17.1 Offlinepaket; 17.2 Update-Manifest; 17.3 Signatur; 17.4 Key-ID; 17.5 Backup; 17.6 Kompatibilität; 17.7 Installation; 17.8 Healthcheck; 17.9 Rollback; 17.10 optionale Onlineprüfung; 17.11 SBOM; 17.12 Provenance.

## Phase 18 – Failure Engineering
18.1 Traversal; 18.2 Symlink; 18.3 TOCTOU-Review; 18.4 Disk-full; 18.5 I/O Error; 18.6 Device-loss; 18.7 Zweitstart; 18.8 DB-Korruption; 18.9 Plugincrash; 18.10 Loggingausfall; 18.11 DST; 18.12 Accessibility; 18.13 Performance.

## Phase 19 – Linux-Matrix
19.1 Ubuntu LTS KDE/GNOME; 19.2 Debian Stable; 19.3 Fedora; 19.4 XFCE-Stichprobe; 19.5 WebKitGTK-Varianten; 19.6 AppImage/FUSE; 19.7 exFAT/USB; 19.8 Unicode/Long Paths; 19.9 Offline; 19.10 reale Evidence.

## Phase 20 – CI-/Repository-Härtung
20.1 Required Checks; 20.2 Ruleset; 20.3 Actions SHA-Pinning; 20.4 Dependency Review; 20.5 CodeQL; 20.6 Rust Audit; 20.7 Docs Gate; 20.8 Schema Gate; 20.9 Artifact Retention.

## Phase 21 – Reproduzierbarkeit/Provenance
21.1 Buildmanifest; 21.2 Toolchain Capture; 21.3 SOURCE_DATE_EPOCH; 21.4 deterministische Archive; 21.5 Zweitbuild; 21.6 Diffanalyse; 21.7 GitHub Attestation; 21.8 Verifikation.

## Phase 22 – RC-Qualifikation
22.1 kompletter E2E; 22.2 Datenintegrität; 22.3 Backup/Restore; 22.4 Offline; 22.5 Security; 22.6 A11y; 22.7 Performance; 22.8 SBOM; 22.9 Hash/Attestation; 22.10 Dokumentationsaudit; 22.11 RC-Receipt.

## Phase 23 – Stable Promotion
23.1 RC-Identität; 23.2 kein ungeprüfter Neubuild; 23.3 Stable-Metadaten; 23.4 Signatur/Hash; 23.5 Archiv; 23.6 Release Notes; 23.7 Promotion; 23.8 Post-Promotion-Verify.

## Phase 24 – Wartung
24.1 Incidentprozess; 24.2 Bug→Regression; 24.3 Dependencyupdates; 24.4 Migrationen; 24.5 Deprecation; 24.6 Backupkompatibilität; 24.7 Supportmatrix; 24.8 technische Schulden; 24.9 Langzeit-Evidence.

# TODO 1.2 – Implementierungsvertrag

## Ziel
Kleinstmögliche Tauri-2-Anwendung im Repository initialisieren, sodass ein lokales Fenster auf Linux startet und der Kernstart zur Laufzeit keinerlei Netzwerk benötigt.

## In Scope
- Toolchain erfassen/pinnen soweit für 1.2 nötig.
- minimale `src-tauri`-Konfiguration.
- minimale lokale HTML/CSS/TS-Seite.
- restriktive CSP-Grundlage.
- lokaler Dev-/Buildstart.
- `cargo check`.
- Rust-Format/Clippy soweit ohne Scopeausweitung möglich.
- Frontendstatische Prüfung soweit bereits erforderlich.
- Start/Exit/Restart-Smoke.
- Offline-Smoke.
- Dokumentations-/Statusupdate.
- Entwicklungs-ZIP + SHA-256.

## Out of Scope
SQLite, Fachmodule, Pluginmanager, Updateengine, Backupengine, Projektroot-Schreiblogik, vollständiges Dashboard und Reminder.

## Akzeptanzkriterien
AC-1 Tauri 2 kompiliert.  
AC-2 lokales Fenster öffnet.  
AC-3 UI-Ressourcen lokal.  
AC-4 CSP ohne unnötige Remote-Quellen.  
AC-5 Start bei blockiertem Netzwerk.  
AC-6 normaler Exit.  
AC-7 Restart.  
AC-8 keine Datei >1000 Zeilen.  
AC-9 keine Fachfunktion vorgezogen.  
AC-10 Build-/Startbefehle dokumentiert.  
AC-11 ZIP-Inventar dokumentiert.  
AC-12 ZIP-SHA-256.  
AC-13 Commit/Version/Artefakt später eindeutig verknüpfbar.

## Testideen
`cargo check`, `cargo fmt --check`, Clippy nach verfügbarer Toolchain, Starttest, Exit/Restart, Netzwerk deaktiviert, Runtime-Assets nach externen URLs/CDNs durchsuchen, ZIP entpacken und Inventar prüfen.

## Evidence
`iteration_id`, `todo_id=1.2`, Commit-SHA, Toolchain, Befehle, Testergebnisse, Offline-Test, Artefakt, SHA-256, bekannte Restunsicherheiten, nächster TODO.

## Stopregel
Sobald 1.2 vollständig erfüllt und dokumentiert ist, Iteration beenden. 1.3 wird erst in einer neuen Iteration begonnen.

## Direkt folgender Schritt
**TODO 1.2 – Tauri-Minimalapp offline starten.**

## Alternative Verbesserung
Vor 1.2 einen rein dokumentierenden REQ/TEST/EVIDENCE-Datensatz anlegen. Keine Runtime-Funktion vorziehen.

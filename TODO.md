# TODO — PROVOWARE PLANER TOOL 2026

## I000 — Foundation
- [x] Projekt- und Architekturvertrag
- [x] Definition of Ready / Done
- [x] autonome Freigabe- und Repository-Regeln

## I001 — Globale Standards
- [x] Standardindex und Benennungsstandard
- [x] UI-, Barrierefreiheits-, Daten-, Logging-, Test-, Start-, Manifest- und Releasestandard
- [x] vollständige Repository-Dateiliste als Pflicht jeder Iteration
- [x] Version und Projektstatus als kanonische Metadaten

## Permanente Regeln
- [x] keine technische Nutzerabnahme als Pflicht
- [x] kein Release bei FAIL oder NOT_RUN eines Pflichtgates
- [x] kleine, klar begrenzte Patches
- [x] Status, Fortschritt, nächster Schritt und Verbesserungsempfehlung pflegen
- [x] kompletten Repository-Inhalt gegen das Soll-Inventar prüfen
- [x] lokale und Remote-Prüfung voneinander trennen
- [x] maschinenlesbarer Iterationsplan und explizite Repository-Differenz
- [x] statischer Fail-Fast-Preflight vor Runtime-Setup
- [x] Repository-Soll nur aus Baseline + deklarierter Differenz
- [x] vollständige Testsuite und historische Gate-Kette je Pass nur einmal
- [x] normale Weitergabe ist ab I014 kein vollständiger Repository-Abzug
- [x] Nutzdaten und Sicherungen sind in Code-Transportprofilen verboten
- [ ] Repository-Sichtbarkeit auf privat stellen
- [ ] `main` mit verbindlichen Statuschecks schützen
- [ ] Release-/Evidence-Commits signieren

## I002 bis I012 — qualifizierte Basis
- [x] I002 Manifest + Evidence Hardening
- [x] I003 Klick-&-Start-Orchestrator
- [x] I004 Kalender-Domainkern + SQLite
- [x] I005 Kalender-GUI + ViewModel
- [x] I006 Todo-Domain + Kalender↔Todo-Soft-Link
- [x] I007 Todo-GUI + ViewModel
- [x] I008 read-only Synchronisationsvorschau
- [x] I009 Feld-Baseline + transaktionaler SyncPlan
- [x] I010 Sync-Control-GUI + immutable ResolutionPlan
- [x] I011 Synchronisationsjournal + sichere Recovery
- [x] I012 Dashboard + Diagnose-/Recovery-Zentrale

## I013 — Entwicklungsautopilot V2
- [x] Prozessbaseline und vermeidbare Schleifen analysiert
- [x] Entwicklungsstandard 2.0 und Pipelinevertrag
- [x] `ITERATION_PLAN.json`, planbasiertes Kandidateninventar und P0 Static
- [x] stabile Dokumentationsmarker, Gate-Deduplizierung, Timing-Evidence und CI-Cache/Concurrency
- [x] zweistufige Exact-SHA-Qualifikation und Main-Nachqualifikation abgeschlossen

## I014 — Transportprofile und Artefakttrennung
- [x] Produktkern, Nutzerdoku, Entwicklung und Evidence als eindeutige Klassen definieren
- [x] `NUTZER` als Standardprofil festlegen
- [x] `PROJEKTKERN`, `ENTWICKLER` und `EVIDENCE` als getrennte explizite Profile definieren
- [x] Nutzer-/Backup-/Workspace-Dateien per Vertrag und `.gitignore` aus Codepaketen ausschließen
- [x] deterministischen profilbasierten ZIP-Builder implementieren
- [x] separates `PAKETMANIFEST.json` und `PAKET_INVENTAR.json` einführen
- [x] paketbezogenes Runtime-Inventar ohne Änderung des Produkt-Startkerns vorsehen
- [x] Profilgrenzen und deterministischen Doppelbau automatisiert testen
- [ ] Fresh-Unpack-Nutzerpaket remote gegen externen Workspace qualifizieren

Der endgültige Freigabestatus von I014 wird ausschließlich in `PROJEKTSTATUS.json`, `QUALIFICATION_REPORT.json` und `REMOTE_TREE_RECEIPT.json` geführt.

## I015 — nach I014
- [ ] immutable Backup-/RestorePlan mit Kandidatenqualifikation
- [ ] Restore-Vorschau strikt von tatsächlicher Ausführung trennen
- [ ] vorhandenen qualifizierten Backup-/Restore-Kern wiederverwenden
- [ ] Sicherungen ausschließlich im Workspace-/Backup-Bereich halten; niemals in Code-Transportprofile aufnehmen

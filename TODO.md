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
- [x] ab I013: maschinenlesbarer Iterationsplan und explizite Repository-Differenz
- [x] ab I013: statischer Fail-Fast-Preflight vor Runtime-Setup
- [x] ab I013: Repository-Soll nur aus Baseline + deklarierter Differenz
- [x] ab I013: vollständige Testsuite und historische Gate-Kette je Pass nur einmal
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
- [x] I002 → I003 → I004 → I005 → I006 → I007 → I008 → I009 → I010 → I011 → I012 historisch qualifiziert

## I013 — Entwicklungsautopilot V2
- [x] I012-Prozessbaseline und vermeidbare Schleifen maschinenlesbar analysieren
- [x] Entwicklungsstandard 2.0 und Pipelinevertrag definieren
- [x] `ITERATION_PLAN.json` mit Baseline, Risiko, Akzeptanzkriterien und Dateidifferenz einführen
- [x] planbasiertes Kandidateninventar implementieren
- [x] P0 Static Preflight ohne Qt/PySide6/Runtime implementieren
- [x] Dokumentationsvertrag auf stabile semantische Marker umstellen
- [x] Autopilot-Gates timingfähig und einmalig pro Pass ausführen
- [ ] Foundation-CI auf Static-first, Cache und Concurrency umstellen
- [ ] I013-Qualifikationsworkflow als neue Referenzpipeline aktivieren
- [ ] zweistufige Exact-SHA-Remotequalifikation PASS
- [ ] Fast-Forward nach `main` und unabhängige Main-Nachqualifikation PASS

## I014 — nach I013
- [ ] immutable Backup-/RestorePlan mit Kandidatenqualifikation
- [ ] Restore-Vorschau strikt von tatsächlicher Ausführung trennen
- [ ] vorhandenen qualifizierten Backup-/Restore-Kern wiederverwenden; kein paralleler Restore-Pfad

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
- [x] normale Weitergabe ist kein vollständiger Repository-Abzug
- [x] Nutzdaten und Sicherungen sind in Code-Transportprofilen verboten
- [x] physischer Restore darf nur einen zentralen Implementierungskern besitzen
- [ ] Repository-Sichtbarkeit auf privat stellen
- [ ] `main` mit verbindlichen Statuschecks schützen
- [ ] Release-/Evidence-Commits signieren

## I002 bis I014 — qualifizierte Basis
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
- [x] I013 Entwicklungsautopilot V2
- [x] I014 Transportprofile und Artefakttrennung

## I015 — Immutable Backup-/RestorePlan
- [x] Backup-/Restore-Standard und Vertrag definieren
- [x] Kandidaten ausschließlich read-only prüfen
- [x] Backup-Bereich als harte Pfadgrenze erzwingen
- [x] Backup + Manifest + SHA-256 + Größe + quick_check + Schema binden
- [x] immutable `RestorePlan` mit kanonischem SHA-256 einführen
- [x] aktiven Zielzustand inklusive WAL in die Precondition aufnehmen
- [x] finalen Stale-Precheck unmittelbar im physischen Restorekern ausführen
- [x] bestehenden `storage.backup.restore_backup()` als einzigen Dateiaustauschpfad wiederverwenden
- [x] rollbackfähigen Postcheck in denselben physischen Kern integrieren
- [x] Plan-Tamper, Backup-/Manifest-Tamper und Ziel-Stale automatisiert testen
- [x] Fault-/Crash-Matrix für Fehler vor Schreibzugriff und Fehler nach Austausch ergänzen
- [ ] I015 Remotequalifikation inkl. Vollregression und Transport-Fresh-Unpack PASS
- [ ] Exact-SHA-Zweitpass PASS
- [ ] Fast-Forward nach `main` und unabhängige Main-Nachqualifikation PASS

## I016 — nach I015
- [ ] Restore-Control-GUI ausschließlich auf `RestoreService`
- [ ] Vorschau, Risikoanzeige, explizite Bestätigung und Ausführung klar trennen
- [ ] keine direkte GUI-Nutzung von SQL, Dateiaustausch oder `storage.backup.restore_backup()`
- [ ] später optional: persistentes Restore-Intent für Crashnachweis nach atomarem Austausch

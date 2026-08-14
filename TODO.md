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
- [ ] Repository-Sichtbarkeit auf privat stellen
- [ ] `main` mit verbindlichen Statuschecks schützen
- [ ] Release-/Evidence-Commits signieren

## I002 bis I010 — qualifizierte Basis
- [x] I002 Manifest + Evidence Hardening
- [x] I003 Klick-&-Start-Orchestrator
- [x] I004 Kalender-Domainkern + SQLite
- [x] I005 Kalender-GUI + ViewModel
- [x] I006 Todo-Domain + Kalender↔Todo-Soft-Link
- [x] I007 Todo-GUI + ViewModel
- [x] I008 read-only Synchronisationsvorschau
- [x] I009 Feld-Baseline + transaktionaler SyncPlan
- [x] I010 Sync-Control-GUI + immutable ResolutionPlan
- [x] I002 → I003 → I004 → I005 → I006 → I007 → I008 → I009 → I010 historisch qualifiziert

## I011 — Synchronisationsjournal + sichere Recovery
- [x] Migration 0004 für hashgebundene Journal-Snapshots
- [x] neue Snapshots atomar mit Audit-Receipt und Sync-Commit schreiben
- [x] alte Receipts ohne Snapshot als `LEGACY_NO_SNAPSHOT` erhalten
- [x] Receipt- und Snapshot-Hash bei jedem Journal-Lesezugriff verifizieren
- [x] read-only JournalQuery und ViewModel
- [x] Vorher-/Nachher-Feldvergleich in der GUI
- [x] immutable RecoveryPlan mit Source-Receipt-, Snapshot- und Current-SyncPlan-Hash
- [x] kein freies Zurückschreiben historischer Werte
- [x] historische Zielwerte nur über aktuell beweisbare Endpoint-Werte übertragen
- [x] Link-Richtung und DUE_END-Semantik bleiben bindend
- [x] Stale-/Manipulationsschutz
- [x] Recovery nutzt denselben I009-Transaktionskern
- [x] Fault-/echte Crash-Matrix für Snapshotphase
- [x] 35er Offscreen-Journal-GUI-Matrix
- [x] zweistufige Remotequalifikation PASS
- [ ] finalen Evidence-Commit nach `main` fast-forward promoten

## I012 — nach I011
- [ ] Dashboard + Diagnose-/Recovery-Zentrale
- [ ] Journal-Integrität, Backup-Status, Datenbankprüfung und Startzustand read-only bündeln
- [ ] keine neue parallele Reparatur-/Schreiblogik

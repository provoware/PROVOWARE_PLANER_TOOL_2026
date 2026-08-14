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

## I002 bis I011 — qualifizierte Basis
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
- [x] I002 → I003 → I004 → I005 → I006 → I007 → I008 → I009 → I010 → I011 historisch qualifiziert

## I012 — Dashboard + Diagnose-/Recovery-Zentrale
- [x] fünf read-only Diagnosebereiche definieren
- [x] Datenbankprüfung über SQLite `mode=ro` + `query_only`
- [x] Journal-Integrität über bestehenden I011-Service bündeln
- [x] Backup-Dateien read-only auf SQLite-Integrität, Manifest und SHA-256 prüfen
- [x] RecoveryPlan-Varianten nur lesend neu berechnen und Blockaden anzeigen
- [x] fehlende optionale Nachweise als GELB statt Fehler darstellen
- [x] Manipulations-/Integritätsverletzungen ROT blockieren
- [x] GUI mit Symbol + Klartext statt Farbsignal allein
- [x] Diagnosezentrale über `Ctrl+Shift+D` integrieren
- [x] letzten Startbericht standardmäßig atomar im Arbeitsbereich speichern
- [x] Service-/GUI-Zieltests und 35er Offscreen-Matrix
- [x] keine Restore-, Sync-, Recovery- oder SQL-Write-Funktion in der Diagnosezentrale

Der Freigabestatus von I012 wird ausschließlich maschinenlesbar in `PROJEKTSTATUS.json`, `QUALIFICATION_REPORT.json` und `REMOTE_TREE_RECEIPT.json` geführt. Dadurch erzeugt die spätere Evidence-/`main`-Promotion keinen selbstwidersprüchlichen TODO-Zustand.

## I013 — nach I012
- [ ] immutable Backup-/RestorePlan mit Kandidatenqualifikation
- [ ] Restore-Vorschau strikt von tatsächlicher Ausführung trennen
- [ ] vorhandenen qualifizierten Backup-/Restore-Kern wiederverwenden; kein paralleler Restore-Pfad

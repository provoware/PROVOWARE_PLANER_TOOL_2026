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

## I002 — Manifest + Evidence Hardening
- [x] Manifest-Builder und SHA-256-Inventar
- [x] Remote-Tree-Validator und zweistufige Remote-Prüfung

## I003 — Klick-&-Start-Orchestrator
- [x] deterministische Startzustände
- [x] PRECHECK → AKTION → POSTCHECK
- [x] Workspace-, SQLite-, Recovery- und Fault-Prüfung

## I004 — Kalender-Domainkern + SQLite-Persistenz
- [x] Domainmodell, Migration 0001, Markierungen, Optimistic Locking, Soft Delete und Backup/Restore

## I005 — Kalender-GUI + ViewModel
- [x] CalendarQueryService und CalendarViewModel
- [x] Tag / Woche / Monat / Jahr
- [x] Design-Tokens, Barrierefreiheit, 112er Offscreen-Matrix und Neustartpersistenz

## I006 — Todo-Domainkern + Kalender↔Todo-Kopplungsvertrag
- [x] Todo-Domainmodell und Migration 0002
- [x] Unteraufgaben, Soft Delete, Optimistic Locking und Soft-Link
- [x] Konflikterkennung, kein kaskadierendes Löschen, Crash-/Rollback-Matrix

## I007 — Todo-GUI + Todo-ViewModel
- [x] TodoQueryService und TodoViewModel
- [x] fünf Todo-Ansichten, Bearbeitung, Verknüpfung und Konflikterklärung
- [x] Tastatur, Accessible Names, High Contrast und sieben Schriftstufen
- [x] 140er Todo-GUI-Matrix, I005-/I006-Regression und Evidence-Zweitpass
- [x] I002 → I003 → I004 → I005 → I006 → I007 vollständig PASS und nach `main` promotet

## I008 — Synchronisations- und Konfliktvorschau
- [x] Synchronisationsvertrag auf Feldebene
- [x] `SynchronizationPreviewService` ohne Schreibschnittstelle
- [x] Titel, Beschreibung und Startzeit als gerichtete Vorschaukandidaten
- [x] Fälligkeit↔Terminende nur semantisch/manuell
- [x] `BOTH_CHANGED`, `DETACHED` und abweichende `CLEAN`-Basis hart blockiert
- [x] Vorschau verändert weder Link noch Nutzdaten
- [x] Schema 2, Zieltests, Vollregression, 140er/112er GUI-Matrizen
- [x] exakter I008-Evidence-SHA-Zweitpass PASS
- [x] I002 → I003 → I004 → I005 → I006 → I007 → I008 vollständig PASS
- [x] qualifizierten I008-Evidence-Commit nach `main` promotet

## I009 — Feld-Baseline / Feld-Hashes + transaktionaler Synchronisationsplan
- [x] Migration 0003 für `sync_field_baselines` und `sync_audit_receipts`
- [x] kanonische typisierte Feldserialisierung und SHA-256
- [x] Feld-Baseline nur bei beweisbar identischen Ausgangswerten bindbar
- [x] bestehende Links ohne beweisbare Baseline fail-closed blockieren
- [x] Drei-Wege-Zustände `UNCHANGED / TODO_ONLY / CALENDAR_ONLY / BOTH_SAME / BOTH_DIFFERENT / BASELINE_MISSING`
- [x] disjunkte Objekt-`BOTH_CHANGED`-Änderungen feldweise verlustfrei planbar
- [x] `BOTH_DIFFERENT` als harter Gesamtplan-Blocker
- [x] `due_at ↔ end_at` weiterhin manuell prüfpflichtig
- [x] deterministische Plan-ID und `precondition_sha256`
- [x] exakte Todo-/Termin-/Link-Versionen im PRECHECK
- [x] exakte Baseline-/Todo-/Kalender-Hashes je Feld im PRECHECK
- [x] atomare Nutzdaten-, Baseline-, Link- und Receipt-Transaktion
- [x] POSTCHECK vor Commit plus SQLite-`quick_check`
- [x] hashgebundenes Audit-Receipt
- [x] Fault-Injection nach Nutzdaten/Baseline/Receipt-Phasen
- [x] echter Prozessabbruch innerhalb offener Sync-Transaktion
- [x] I008-Historienvalidator für Schema 3 vorwärtskompatibel gehärtet
- [x] I009-Validator und Autopilot-Gate angelegt
- [ ] I009-Zieltests und Fault-Matrix remote PASS
- [ ] vollständige Unit-/Regressionstests PASS
- [ ] 140er Todo-GUI- und 112er Kalender-GUI-Regression PASS
- [ ] I002 → I003 → I004 → I005 → I006 → I007 → I008 → I009 vollständig PASS
- [ ] exakter I009-Evidence-SHA-Zweitpass PASS
- [ ] qualifizierten I009-Evidence-Commit nach `main` promoten

## I010 — Nach erfolgreichem I009
- [ ] Synchronisations-Control-GUI auf `SyncPlan` und `SyncAuditReceipt`
- [ ] Feldzustand, Quelle/Ziel, Hashstatus, Grund und erwartete Version verständlich anzeigen
- [ ] `BOTH_DIFFERENT` ausschließlich explizit manuell entscheiden
- [ ] GUI darf weder SQL noch eigene Konfliktlogik enthalten

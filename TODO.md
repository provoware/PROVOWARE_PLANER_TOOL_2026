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
- [x] Remote-Tree-Validator und Fehlerkatalog
- [x] vollständige Repository-Dateiliste
- [x] zweistufige Remote-Qualifikation

## I003 — Klick-&-Start-Orchestrator
- [x] deterministische Startzustände
- [x] PRECHECK → AKTION → POSTCHECK
- [x] Workspace-, SQLite-, Recovery- und Fault-Prüfung

## I004 — Kalender-Domainkern + SQLite-Persistenz
- [x] Domainmodell und Invarianten
- [x] SQLite-Schema und Migration 0001
- [x] fünf Markierungen, Optimistic Locking, Soft Delete und Backup/Restore

## I005 — Kalender-GUI + ViewModel
- [x] CalendarQueryService und CalendarViewModel
- [x] Tag / Woche / Monat / Jahr
- [x] Design-Tokens, Schriftmatrix, Accessible Names und High Contrast
- [x] 112er Offscreen-GUI-Matrix und Neustartpersistenz

## I006 — Todo-Domainkern + Kalender↔Todo-Kopplungsvertrag
- [x] Todo-Domainmodell und Migration 0002
- [x] Unteraufgaben, Soft Delete und Optimistic Locking
- [x] eigenständige Link-ID und Synchronisationsrichtung
- [x] Konfliktzustände CLEAN / TODO_CHANGED / CALENDAR_CHANGED / BOTH_CHANGED / DETACHED
- [x] kein kaskadierendes Löschen zwischen Todo, Termin und Link
- [x] Crash-/Rollback-Matrix und Neustartpersistenz

## I007 — Todo-GUI + Todo-ViewModel
- [x] TodoQueryService und TodoViewModel
- [x] Heute / Diese Woche / Überfällig / Ohne Datum / Erledigt
- [x] Erstellen, Bearbeiten, Status, Priorität, Fortschritt und Unteraufgaben
- [x] sichtbare Kalenderkopplung und Konflikterklärung
- [x] Tastatur, Accessible Names, High Contrast und sieben Schriftstufen
- [x] 140er Todo-GUI-Matrix
- [x] I005-112er GUI-Matrix als Regression
- [x] I006-Crash-/Rollback-Regression
- [x] exakter Evidence-SHA-Zweitpass
- [x] I002 → I003 → I004 → I005 → I006 → I007 vollständig PASS
- [x] qualifizierten I007-Evidence-Commit nach `main` promotet

## I008 — Synchronisations- und Konfliktvorschau
- [x] Synchronisationsvertrag auf Feldebene definieren
- [x] Quelle/Ziel und erlaubte Richtungen je Feld festlegen
- [x] `SynchronizationPreviewService` ohne Schreibschnittstelle
- [x] `SyncPreview` mit Objekt- und Snapshot-Versionen
- [x] Titel, Beschreibung und Startzeit als gerichtete Vorschaukandidaten
- [x] Fälligkeit↔Terminende nur semantisch/manuell prüfen
- [x] nicht zugeordnete Felder ausdrücklich festschreiben
- [x] `BOTH_CHANGED` hart blockieren
- [x] `DETACHED` hart blockieren
- [x] abweichende `CLEAN`-Basiswerte blockieren
- [x] Vorschau darf Linkstatus und Nutzdaten nicht verändern
- [x] keine neue Datenbankmigration; Schema 2 bleibt bestehen
- [x] I008-Zieltests und Validator anlegen
- [ ] Remote-Zieltests und vollständige Regression PASS
- [ ] 140er Todo-GUI- und 112er Kalender-GUI-Regression PASS
- [ ] exakter I008-Evidence-SHA-Zweitpass PASS
- [ ] I002 → I003 → I004 → I005 → I006 → I007 → I008 vollständig PASS
- [ ] qualifizierten I008-Evidence-Commit nach `main` promoten

## I009 — Nach erfolgreichem I008
- [ ] Feld-Baseline oder Feld-Hashes pro synchronisierbarem Feldpaar
- [ ] tatsächliche Feldänderungen seit letztem Sync beweisbar machen
- [ ] transaktionalen Synchronisationsplan mit PRECHECK vorbereiten
- [ ] atomare COMMIT-/POSTCHECK-Kette
- [ ] Rollback-/Crash-/Fault-Matrix für echte Synchronisationswrites
- [ ] Audit-Receipt mit Vorher-/Nachher-Werten
- [ ] `BOTH_CHANGED` nur bei nachweislich disjunkten Änderungen verlustfrei auflösbar machen

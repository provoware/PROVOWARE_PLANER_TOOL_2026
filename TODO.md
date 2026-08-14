# TODO — PROVOWARE PLANER TOOL 2026

## Permanente Regeln
- [x] keine technische Nutzerabnahme als Pflicht
- [x] kein Release bei nicht bestandenen oder nicht ausgeführten Pflichtprüfungen
- [x] kleine, klar begrenzte Patches
- [x] Status, Fortschritt, nächster Schritt und Verbesserungsempfehlung pflegen
- [x] kompletten Repository-Inhalt nach jeder Iteration gegen Soll-Inventar prüfen
- [x] lokale und Remote-Prüfung voneinander trennen
- [ ] Repository-Sichtbarkeit auf privat stellen

## I002 — Manifest + Evidence Hardening
- [x] Manifest-Builder und SHA-256-Inventar
- [x] Remote-Tree-Validator und Fehlerkatalog
- [x] vollständige Repository-Dateiliste
- [x] zweistufige Remote-Qualifikation

## I003 — Klick-&-Start-Orchestrator
- [x] deterministische Startzustände
- [x] PRECHECK → ACTION → POSTCHECK
- [x] Workspace-, SQLite-, Recovery- und Fault-Prüfung

## I004 — Kalender-Domainkern + SQLite-Persistenz
- [x] Domainmodell und Invarianten
- [x] SQLite-Schema, Migrationen, fünf Markierungen
- [x] Optimistic Locking, Soft Delete, Backup/Restore
- [x] historische Gate-Kette I002 → I003 → I004

## I005 — Kalender-GUI + ViewModel
- [x] CalendarQueryService und CalendarViewModel
- [x] Tag / Woche / Monat / Jahr
- [x] fünf sichtbare/editierbare Markierungen
- [x] Design-Tokens, Schriftmatrix, Accessible Names und High Contrast
- [x] 112er Offscreen-GUI-Matrix und Neustartpersistenz
- [x] historische Gate-Kette I002 → I003 → I004 → I005

## I006 — Todo-Domainkern + Kalender↔Todo-Kopplungsvertrag
- [x] Todo-Domainmodell: Status, Priorität, Fortschritt, Start und Fälligkeit
- [x] Migration 0002 mit Todo- und Linktabellen
- [x] Unteraufgaben über `parent_id`
- [x] TodoRepository und TodoService
- [x] Soft Delete und Optimistic Locking
- [x] eigenständige Link-ID und Synchronisationsrichtung
- [x] Konfliktzustände CLEAN / TODO_CHANGED / CALENDAR_CHANGED / BOTH_CHANGED / DETACHED
- [x] kein kaskadierendes Löschen zwischen Todo, Termin und Link
- [x] Entkoppeln erhält beide Endpunkte
- [x] Fault-Matrix für Insert, Link und Soft Delete
- [x] echter Prozessabbruch vor Commit mit Rollback-Nachweis
- [x] automatische Neustartpersistenz
- [x] historische Gate-Kette I002 → I003 → I004 → I005 → I006
- [x] keine Todo-GUI und keine automatische Inhalts-Synchronisation in I006

## I007 — Nächster logischer Schritt
- [ ] TodoQueryService und TodoViewModel
- [ ] Listen: Heute / Diese Woche / Überfällig / Ohne Datum / Erledigt
- [ ] Erstellen, Bearbeiten, Status, Priorität, Fortschritt und Unteraufgaben
- [ ] sichtbare Kalenderkopplung und Konfliktstatus
- [ ] Tastatur, Accessible Names, High Contrast und Schriftmatrix
- [ ] automatische GUI-/Persistenz-/Regressionstests
- [ ] Konfliktauflösung noch nicht automatisch durchführen

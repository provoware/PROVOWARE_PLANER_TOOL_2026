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
- [x] historische I004-Tests isolieren Migration 0001 von späteren Migrationen

## I005 — Kalender-GUI + ViewModel
- [x] CalendarQueryService und CalendarViewModel
- [x] Tag / Woche / Monat / Jahr
- [x] fünf sichtbare/editierbare Markierungen
- [x] Design-Tokens, Schriftmatrix, Accessible Names und High Contrast
- [x] 112er Offscreen-GUI-Matrix und Neustartpersistenz

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
- [x] Fault-Matrix und echter Prozessabbruch vor Commit
- [x] automatische Neustartpersistenz
- [x] historische Gate-Kette I002 → I003 → I004 → I005 → I006
- [x] keine Todo-GUI und keine automatische Inhalts-Synchronisation in I006

## I007 — Todo-GUI + Todo-ViewModel
- [x] TodoQueryService als reine Leseschicht
- [x] TodoViewModel ohne Repository-/SQL-Abhängigkeit
- [x] Darstellungsmodelle mit deutschen Status-, Prioritäts- und Konflikttexten
- [x] Listen: Heute / Diese Woche / Überfällig / Ohne Datum / Erledigt
- [x] Erstellen und Bearbeiten
- [x] Status, Priorität und Fortschritt
- [x] Unteraufgaben
- [x] sichtbare Kalenderkopplung mit eigener Link-ID
- [x] Konfliktstatus und Erklärung sichtbar
- [x] reine Konfliktvorschau ohne Schreiboperation beim Anzeigen
- [x] Verknüpfung lösen, ohne Todo oder Termin zu löschen
- [x] Soft Delete mit ausdrücklichem Schutz gekoppelter Termine
- [x] Tastaturreihenfolge und Kurzbefehle
- [x] Accessible Names und High-Contrast-Klartexte
- [x] Schriftmatrix 90/100/110/125/150/175/200 %
- [x] Todo-GUI-Neustartpersistenz
- [x] 140er Offscreen-GUI-Matrix angelegt
- [x] I005-112er GUI-Matrix als Regression vorgesehen
- [x] automatische Konfliktauflösung und Inhalts-Synchronisation bleiben in I007 deaktiviert
- [ ] Remote-Zieltests und vollständige Regression PASS
- [ ] exakter Evidence-SHA-Zweitpass PASS
- [ ] I002 → I003 → I004 → I005 → I006 → I007 vollständig PASS
- [ ] qualifizierten I007-Evidence-Commit nach `main` promoten

## I008 — Nächster logischer Schritt nach I007
- [ ] Synchronisationsvertrag auf Feldebene definieren
- [ ] Quelle/Ziel und erlaubte Richtungen je Feld festlegen
- [ ] Synchronisationsvorschau vor jeder Änderung
- [ ] atomare PRECHECK → COMMIT → POSTCHECK-Kette
- [ ] verlustfreie Konfliktregeln für BOTH_CHANGED
- [ ] automatische Auflösung nur für ausdrücklich qualifizierte konfliktfreie Fälle

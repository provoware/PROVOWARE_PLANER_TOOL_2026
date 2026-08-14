# I006 — Todo-Domainkern + Kalender↔Todo-Kopplungsvertrag

## Ziel
I006 führt Aufgaben als eigenständigen Domainkern ein. Es entsteht ausdrücklich noch keine Todo-GUI und keine automatische Inhalts-Synchronisation zwischen Aufgabe und Termin.

## Todo-Invarianten
- Status: Offen, In Arbeit, Wartend, Erledigt, Abgebrochen.
- Priorität: Niedrig, Normal, Hoch, Dringend.
- Fortschritt: 0–100 Prozent.
- Eine erledigte Aufgabe besitzt 100 Prozent Fortschritt.
- Start und Fälligkeit sind optionale zeitzonenbewusste Zeitpunkte.
- Unteraufgaben verwenden `parent_id`; Selbstreferenzen sind verboten.
- Fachliches Löschen ist ausschließlich Soft Delete.
- Änderungen verwenden Optimistic Locking über `version`.

## Kopplungsmodell
`todo_calendar_links` ist ein eigenständiges Objekt mit eigener `link_id`, eigener Version und eigenen Zeitstempeln. Es speichert Todo- und Terminversion der letzten bestätigten Synchronisation.

Richtungen: Todo→Kalender, Kalender→Todo, bidirektional oder manuell. I006 speichert diese Absicht nur; Nutzdaten werden noch nicht automatisch übertragen.

Konfliktzustände: `CLEAN`, `TODO_CHANGED`, `CALENDAR_CHANGED`, `BOTH_CHANGED`, `DETACHED`.

## Löschschutz
Todo und Termin löschen sich niemals gegenseitig. Soft Delete eines Endpunkts löscht auch den Link nicht. Bei der Konfliktprüfung wird die Kopplung stattdessen `DETACHED`. Ein explizites Entkoppeln löscht nur den Link weich.

Auf SQLite-Ebene verwenden Link-Endpunkte `ON DELETE RESTRICT`; ein versehentliches physisches Löschen wird dadurch zusätzlich blockiert. Für Unteraufgaben gilt bei physischem Entfernen des Elternobjekts `ON DELETE SET NULL`. `ON DELETE CASCADE` ist in Migration 0002 verboten.

## Fault- und Crash-Matrix
I006 prüft Abbrüche nach Todo-Insert, Link-Insert und Soft-Delete jeweils vor Commit. Zusätzlich beendet ein separater Prozess eine echte offene SQLite-Transaktion hart vor Commit. Nach jedem Szenario muss Rollback beziehungsweise Recovery ohne Geisterdatensatz und mit erfolgreichem `quick_check` nachgewiesen sein.

## Historische Gates
I002 → I003 → I004 → I005 → I006. Der I005-Validator wird für nachfolgende Iterationen als historisches Mindestgate vorwärtskompatibel ausgeführt.

## Nächster logischer Schritt
I007 — Todo-GUI + Todo-ViewModel auf dem qualifizierten I006-Service aufbauen. Erst dort entstehen Listen, Filter, Bearbeitungsdialoge und sichtbare Konfliktinformationen.

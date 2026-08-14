# I008 — Kalender↔Todo-Synchronisations- und Konfliktauflösungsvertrag

## Ziel
I008 führt eine deterministische, vollständig read-only Synchronisationsvorschau ein. Die Vorschau zeigt Quelle, Ziel, Feldwerte, Link-Richtung, Objektversionen und Konfliktzustand. Sie führt keine Datenänderung aus.

## Sicherheitsgrenze
- Keine neue Datenbankmigration; Schema bleibt Version 2.
- Keine `apply()`, `execute()` oder `synchronize()`-Schreibschnittstelle.
- `SyncPreview.write_permitted` ist in I008 immer `False`.
- `BOTH_CHANGED`, `DETACHED` und abweichende `CLEAN`-Ausgangswerte werden hart blockiert.
- Eine Vorschau darf Linkstatus, Versions-Snapshots, Todo oder Termin nicht verändern.

## Feldvertrag
### Kandidaten für eine spätere gerichtete Übertragung
- `title ↔ title`
- `description ↔ description`
- `start_at ↔ start_at`

### Nur semantische Prüfung
- `due_at ↔ end_at`

Fälligkeit einer Aufgabe und Ende eines Termins sind nicht automatisch dasselbe. Deshalb ist dieses Feld in I008 niemals automatischer Kandidat.

### Nicht automatisch zugeordnet
Todo: Status, Priorität, Fortschritt, Elternaufgabe.

Kalender: Status, Zeitzone, Ganztägigkeit, Markierung.

## Konfliktmatrix
- `CLEAN`: Nur identische Feldwerte gelten als sicher. Abweichende Werte ohne Feld-Baseline werden blockiert.
- `TODO_CHANGED`: Todo→Kalender-Vorschlag nur bei `TODO_TO_CALENDAR` oder `BIDIRECTIONAL`.
- `CALENDAR_CHANGED`: Kalender→Todo-Vorschlag nur bei `CALENDAR_TO_TODO` oder `BIDIRECTIONAL`.
- `BOTH_CHANGED`: Immer blockiert.
- `DETACHED`: Immer blockiert; gelöschte Endpunkte werden nicht wiederbelebt.
- `MANUAL`: Keine automatische Richtung.

## Warum BOTH_CHANGED noch nicht feldweise aufgelöst wird
Der I006-Link speichert Objektversionen, aber noch keine belastbare Feld-Baseline oder Feld-Hashes. Bei beidseitig geänderten Objekten kann deshalb nicht bewiesen werden, ob dieselben oder unterschiedliche Felder verändert wurden. Eine automatische Zusammenführung wäre Spekulation.

## Voraussetzung für spätere Schreibsynchronisation
Vor einer späteren Schreibiteration sind mindestens erforderlich:
1. Feld-Baseline oder Feld-Hashes.
2. PRECHECK mit exakten erwarteten Versionen.
3. atomare Transaktion.
4. POSTCHECK gegen das geplante Ergebnis.
5. Rollback-/Crash-/Fault-Matrix.
6. Audit-Receipt mit Quelle, Ziel, Vorher-/Nachher-Werten und Versionskette.

Erst danach darf eine separat qualifizierte Iteration echte Synchronisation ausführen.

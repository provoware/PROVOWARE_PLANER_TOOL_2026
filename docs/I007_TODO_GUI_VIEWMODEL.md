# I007 — Todo-GUI + Todo-ViewModel

## Ziel
I007 ergänzt den qualifizierten I006-Todo-Domainkern um eine PySide6/Qt-Oberfläche. Die GUI bleibt strikt von SQLite und Repository-Details getrennt.

## Verbindliche Schichten

`TodoService → TodoQueryService → TodoViewModel → Darstellungsmodelle → PySide6/Qt`

`ui/` und `viewmodel/` dürfen weder `sqlite3` noch `storage.*` importieren und kein SQL ausführen.

## Fünf Todo-Ansichten
- Heute
- Diese Woche
- Überfällig
- Ohne Datum
- Erledigt

Die Filterlogik liegt in `TodoQueryService`, nicht in Qt.

## Bedienfunktionen
- Aufgabe erstellen und bearbeiten
- Status setzen
- Priorität und Fortschritt bearbeiten
- Unteraufgaben anlegen
- Todo mit Kalendertermin verknüpfen
- Verknüpfung lösen
- Aufgabe per Soft Delete in den Papierkorb verschieben

## Kalender↔Todo-Konflikte
I007 zeigt aktuelle Konflikte über eine reine `preview_conflict`-Abfrage. Das Anzeigen oder Aktualisieren der GUI darf weder den Linkzustand noch Versions-Snapshots verändern.

Sichtbare Zustände: `CLEAN`, `TODO_CHANGED`, `CALENDAR_CHANGED`, `BOTH_CHANGED` und `DETACHED`.

I007 führt **keine automatische Inhalts-Synchronisation und keine automatische Konfliktauflösung** aus. Insbesondere `BOTH_CHANGED` verlangt eine spätere, eigenständig qualifizierte Synchronisationsiteration.

## Barrierefreiheit und Darstellung
- zentrale I005-Design-Tokens wiederverwenden
- Schriftstufen 90/100/110/125/150/175/200 %
- Tastaturreihenfolge und Kurzbefehle
- Accessible Names für sichtbare interaktive Elemente
- High-Contrast-taugliche Klartexte
- Status nie ausschließlich über Farbe

## Integration
Der vorhandene Kalender bleibt Hauptfenster. `Module → Aufgaben öffnen` öffnet das Todo-Fenster mit denselben `PlannerServices` und derselben SQLite-Datenbank. Dadurch entsteht keine zweite Datenquelle.

## Qualifikation
Pflicht sind TodoQueryService-/ViewModel-Zieltests, Todo-GUI-Offscreen-Tests, Neustartpersistenz, eine 140er Todo-GUI-Matrix, die bestehende 112er I005-Kalender-GUI-Matrix als Regression, I006 Crash-/Rollback-Regression, vollständige Unit-/Regressionstests, Standard-Validator, Autopilot I002→I007, Remote-Tree-Prüfung und ein exakter Evidence-SHA-Zweitpass.

## Freigabegrenze
Ein grüner erster Lauf allein genügt nicht. Erst wenn der gespeicherte Evidence-Commit in einem zweiten read-only Lauf anhand seiner exakten SHA erneut vollständig besteht, darf I007 nach `main` promoviert werden.

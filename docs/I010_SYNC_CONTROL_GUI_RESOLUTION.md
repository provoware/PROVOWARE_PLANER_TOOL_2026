# I010 – Synchronisations-Control-GUI + explizite Konfliktentscheidung

## Ziel

I010 macht den in I009 qualifizierten Synchronisationskern sichtbar und bedienbar, ohne dessen Sicherheitsgrenzen zu umgehen.

Die Datenflusskette lautet:

`SyncPlan → SyncControlQuery → SyncControlViewModel → Feldtabelle → explizite BOTH_DIFFERENT-Entscheidung → neuer ResolutionPlan → PRECHECK → atomarer I009-COMMIT → POSTCHECK → Audit-Receipt`

## Unveränderliche Quelle

Der ursprüngliche `SyncPlan` wird niemals verändert. Der neue `ResolutionPlan` bindet:

- `source_plan_id`
- SHA-256 des vollständigen Source-Plan-Vertrags
- Source-`precondition_sha256`
- Todo-/Termin-/Link-Versionen
- Baseline-, Todo- und Kalender-Hashes je Feld
- ursprünglichen Feldzustand und ursprüngliche Aktion
- die explizite Entscheidung
- die daraus abgeleitete Schreibaktion

Die `resolution_sha256` bindet alle diese Angaben. Die `resolution_plan_id` wird deterministisch aus diesem Hash abgeleitet.

## Entscheidungen

Nur `BOTH_DIFFERENT` darf manuell entschieden werden:

- `TODO_WERT`
- `KALENDER_WERT`
- `BLOCKIERT_LASSEN`

`BLOCKIERT_LASSEN` ist immer der Standard. Es gibt keine Heuristik und keine automatische Konfliktauflösung.

## Commit

I010 führt keinen zweiten Datenbank-Schreibpfad ein. Nach erfolgreicher Rekonstruktion des ResolutionPlans wird ein ausführbarer I009-Plan erzeugt, dessen:

- `plan_id` = `resolution_plan_id`
- `precondition_sha256` = `resolution_sha256`
- Feldzustand weiterhin den ursprünglichen Zustand, z. B. `BOTH_DIFFERENT`, enthält
- Aktion die explizit gewählte Richtung enthält

Damit beweist das bestehende Audit-Receipt sowohl den Konflikt als auch die getroffene Entscheidung.

## GUI

Die Oberfläche zeigt pro Feld:

Baseline, Todo, Kalender, Zustand, geplante Aktion, Grund, Versionsstatus, Hashstatus und Entscheidung.

Die Oberfläche schreibt beim Prüfen oder Ändern einer Auswahl nichts. Erst `Atomar ausführen` kann einen qualifizierten Plan committen.

## Sicherheitsgrenzen

- Veralteter Source-Plan: blockiert.
- Manipulierter ResolutionPlan: blockiert.
- Nicht entschiedener Konflikt: blockiert.
- Link-Richtung widerspricht Entscheidung: blockiert.
- Bestehendes `REVIEW_REQUIRED` außerhalb `BOTH_DIFFERENT`: bleibt blockiert.
- Fehler oder Prozessabbruch an den I009-Transaktionspunkten: vollständiger Rollback.

## Repository-Härtung

Repository-Sichtbarkeit, Branch-Protection und Commit-Signierung bleiben Infrastrukturthemen. I010 verändert diese Punkte nicht stillschweigend.

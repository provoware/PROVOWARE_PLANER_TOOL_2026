# I009 — Feld-Baseline, Feld-Hashes und transaktionaler Synchronisationsplan

## Ziel
I009 ersetzt die grobe Objektfrage „Wurde Todo oder Termin geändert?“ durch einen beweisbaren Drei-Wege-Vergleich pro synchronisiertem Feld.

Jedes Feld wird gegen eine gespeicherte gemeinsame Baseline geprüft:

`Baseline → aktueller Todo-Wert + aktueller Kalender-Wert → Feldzustand → Planaktion`.

## Feldzustände
- `UNCHANGED`: beide Seiten entsprechen der Baseline.
- `TODO_ONLY`: nur Todo unterscheidet sich von der Baseline.
- `CALENDAR_ONLY`: nur der Termin unterscheidet sich von der Baseline.
- `BOTH_SAME`: beide Seiten wurden auf denselben neuen kanonischen Wert geändert.
- `BOTH_DIFFERENT`: dasselbe Feld wurde unterschiedlich geändert; harter Blocker.
- `BASELINE_MISSING`: noch keine beweisbare gemeinsame Baseline; harter Blocker.

Damit kann ein Link auf Objektebene `BOTH_CHANGED` sein und trotzdem verlustfrei synchronisierbar bleiben, wenn beispielsweise nur der Todo-Titel und nur die Kalenderbeschreibung verändert wurden.

## Baseline-Bindung
Migration 0003 führt `sync_field_baselines` ein. Eine erste Baseline darf nur gebunden werden, wenn Todo- und Kalenderwert des Feldes kanonisch identisch sind. Bestehende Links erhalten **keine erfundene Baseline**. Abweichende Ausgangswerte werden erklärt und blockiert.

Kanonische Werte werden typisiert serialisiert. Zeitpunkte werden vor SHA-256-Bildung nach UTC normalisiert. Dadurch erzeugen äquivalente Zeitpunkte denselben Feld-Hash.

## Deterministischer SyncPlan
Ein `SyncPlan` enthält:
- Plan-ID aus kanonischem SHA-256-Payload,
- exakte Todo-, Termin- und Link-Version,
- Synchronisationsrichtung,
- Baseline-Hash je Feld,
- aktuellen Todo-Hash je Feld,
- aktuellen Kalender-Hash je Feld,
- Feldzustand und geplante Aktion,
- Precondition-SHA-256,
- Klartextgrund und Schreibfreigabe.

## PRECHECK → COMMIT → POSTCHECK
### PRECHECK
Vor dem Write werden innerhalb der SQLite-Transaktion erneut Versionen, Richtung, aktuelle Feld-Hashes und Baseline-Hashes geprüft. Jede Abweichung macht den Plan veraltet (`STALE`).

### COMMIT
Alle Nutzdatenänderungen, Baseline-Fortschreibungen, Link-Snapshots und das Audit-Receipt laufen in **einer** `BEGIN IMMEDIATE`-Transaktion. Teilcommits sind verboten.

### POSTCHECK
Noch vor dem SQLite-Commit wird geprüft:
- alle verwalteten Feldpaare sind danach identisch,
- alle Baseline-Hashes entsprechen exakt den Endwerten,
- Link-Snapshots entsprechen den finalen Objektversionen,
- das Audit-Receipt existiert mit dem erwarteten Hash.

Nach erfolgreichem Commit folgt zusätzlich `PRAGMA quick_check`.

## Audit-Receipt
`sync_audit_receipts` speichert Plan-ID, Precondition-Hash, Vorher-/Nachher-Versionen, Feldzustände, Aktionen, Baseline-Hashes und einen SHA-256 des kanonischen Receipt-Payloads.

Ein Write ohne vollständiges Receipt ist nicht zulässig: Fehler vor dem Commit rollen Nutzdaten, Baseline, Link und Receipt gemeinsam zurück.

## Semantische Grenze
`due_at ↔ end_at` bleibt auch in I009 manuell prüfpflichtig. Technische Gleichheit beweist nicht, dass Aufgabenfälligkeit und Terminende fachlich dasselbe bedeuten.

## Fault-/Crash-Matrix
I009 injiziert Fehler nach:
1. Nutzdatenwrite,
2. Baseline-Write,
3. vor Receipt,
4. nach Receipt aber vor Commit,
5. echtem Prozessabbruch nach Nutzdatenwrite.

Alle Szenarien müssen nach Neustart den vollständigen Vorzustand zeigen: kein Teilwrite, kein Receipt, konsistente Baseline und `PRAGMA quick_check=ok`.

## Nutzerfeedback
`SynchronizationService.feedback(plan)` liefert für Plan und jedes Feld Klartext: Zustand, Aktion und Grund. Blockaden werden nicht verschluckt und nicht automatisch übergangen.

# I011 — Synchronisationsjournal + Resolution-Historie + sichere Recovery-Ansicht

## Ziel

I011 macht die bereits vorhandenen Audit-Receipts verständlich sichtbar und ergänzt neue Synchronisationsvorgänge um einen hashgebundenen Vorher-/Nachher-Snapshot. Historische Entscheidungen werden niemals still erneut ausgeführt.

## Journal

Die Journalansicht ist read-only. Sie zeigt Zeitpunkt, Planart, Verknüpfung, Integritätsstatus, Recovery-Verfügbarkeit, Versionssprünge, Receipt-SHA-256, Plan-ID und Receipt-ID.

Jeder Receipt-Hash wird beim Lesen erneut aus `payload_json` berechnet. Für I011-Snapshots wird zusätzlich ein eigener SHA-256 über Vorher-JSON, Nachher-JSON und den Receipt-Hash geprüft.

## Migration 0004

`sync_history_snapshots` bindet genau einen Snapshot an genau ein `sync_audit_receipts`-Objekt. `ON DELETE RESTRICT` verhindert eine kaskadierende Entfernung der Nachweiskette.

Neue Snapshots werden innerhalb derselben SQLite-Transaktion wie Nutzdaten, Baselines, Linkfortschreibung und Receipt geschrieben. Der neue Fault-Punkt `SYNC_AFTER_HISTORY_SNAPSHOT` beweist Rollback sowohl bei Exception als auch bei echtem Prozessabbruch.

## Umgang mit alten Receipts

I009/I010-Receipts bleiben unverändert gültig. Da sie keine damaligen Feldwerte enthalten, markiert I011 sie als `LEGACY_NO_SNAPSHOT`. Sie bleiben auditierbar, werden aber nicht künstlich mit geschätzten oder aktuellen Werten aufgefüllt.

## RecoveryPlan

Eine Recovery beginnt immer mit einem neuen unveränderlichen `RecoveryPlan`.

Gebunden werden:

- Quell-Receipt-ID und Receipt-SHA-256,
- Quell-Snapshot-SHA-256,
- ursprüngliche Plan-ID,
- aktueller SyncPlan inklusive vollständigem SHA-256,
- aktuelle Precondition,
- Todo-, Kalender- und Link-Version,
- aktuelle Feld-Hashes,
- historischer Ziel-Hash je Feld,
- gewählte Recovery-Art.

Unterstützte Absichten:

- `NACHHER_ERNEUT_ANWENDEN`
- `VORHER_WIEDERHERSTELLEN`

## Fail-closed Regeln

I011 schreibt historische Werte nicht frei aus dem Journal zurück. Ein Zielwert darf nur über den bestehenden I009-Transaktionskern übertragen werden, wenn er auf mindestens einer aktuellen Seite hashidentisch vorhanden ist und die Link-Richtung diese Übertragung erlaubt.

War der historische Zielzustand selbst divergent, fehlt ein Snapshot, wurde Receipt/Snapshot manipuliert, ist der aktuelle SyncPlan veraltet oder ist der Zielwert auf keiner aktuellen Seite mehr vorhanden, bleibt der RecoveryPlan blockiert.

`DUE_END` bleibt semantisch prüfpflichtig und wird durch Recovery nicht still freigegeben.

## GUI

`Synchronisationsjournal öffnen` zeigt die unveränderliche Historie sowie einen Vorher-/Nachher-Feldvergleich. Eine Recovery hat zwei getrennte Schritte:

1. historischen Zielstand ausdrücklich prüfen,
2. nur einen `READY`-RecoveryPlan atomar ausführen.

Nach erfolgreicher Recovery entsteht ein neues Audit-Receipt und wiederum ein neuer I011-Snapshot. Der alte Nachweis wird niemals verändert.

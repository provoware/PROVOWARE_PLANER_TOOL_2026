# PROVOWARE PLANER TOOL 2026

Privates, portables und vollständig offline ausgerichtetes Ein-Nutzer-Planungswerkzeug für Linux. Der Planner wird als wartbarer modularer Monolith entwickelt und autonom qualifiziert.

## 1. Projektstatus
- **Version:** `0.11.0-dev.1`
- **Iteration:** `I011`
- **Checkpoint:** `C011-SYNC-JOURNAL-RECOVERY`
- **Status:** `QUALIFIZIERT / GRÜN`
- **Zielplattform:** Linux, insbesondere Ubuntu-/Kubuntu-Derivate
- **Betrieb:** lokal und offline-first
- **Technische Nutzerabnahme:** nicht Bestandteil der Pflicht-Freigabekette

Die maschinenlesbare Wahrheit liegt in `VERSION.json`, `PROJEKTSTATUS.json` und `PROJECT_CONTRACT.json`.

## 2. Was ist das Tool?
PROVOWARE PLANER verbindet Kalender, Aufgabenplanung, Synchronisationskontrolle, Journal, Diagnose und spätere Zusatzmodule. Nutzerdaten bleiben lokal im ausgewählten Arbeitsbereich.

## 3. Kernmodule
### Kalender
Tag, Woche, Monat und Jahr; Termine und fünf editierbare Markierungen.

### Todo
Aufgaben, Status, Priorität, Fälligkeit, Unteraufgaben, Fortschritt und sichere Kalender-Verknüpfungen.

### Synchronisation
I009 führt Feld-Baselines, Drei-Wege-Vergleich, atomare SyncPlans und Audit-Receipts ein. I010 ergänzt die explizite, hashgebundene Konfliktentscheidung über neue ResolutionPlans. I011 ergänzt ein ausschließlich lesendes Synchronisationsjournal sowie neue, hashgebundene RecoveryPlans.

### Synchronisationsjournal
Neue I011-Transaktionen speichern gemeinsam mit dem Audit-Receipt einen unveränderlichen Vorher-/Nachher-Snapshot. Ältere I009/I010-Receipts bleiben gültige Nachweise, besitzen aber keine erfundenen historischen Werte und sind deshalb nicht automatisch wiederherstellbar.

### Dashboard und Diagnose
Die zentrale Dashboard-/Diagnosezentrale folgt in I012. Bis dahin bleiben Start-, Datenbank-, Synchronisations- und Journaldiagnosen in ihren qualifizierten Fachmodulen.

## 4. Oberfläche und globale Gestaltung
Die Oberfläche verwendet zentrale Designregeln, skalierbare Schrift, Tastaturnavigation und textliche Statusaussagen. Farbe allein trägt keine Bedeutung.

## 5. Ampelsystem
- ● **GRÜN – BEREIT**
- ▲ **GELB – EINGESCHRÄNKT**
- ● **ROT – BLOCKIERT**

## 6. Klick-&-Start
Der Start-Orchestrator prüft Betriebssystem, Runtime, Programmdateien, Manifeste, Konfiguration, Workspace, Datenbank, Migrationen, Recovery, Module und GUI. Relevante Aktionen folgen `PRECHECK → AKTION → POSTCHECK`.

## 7. Daten und Sicherheit
SQLite arbeitet mit Foreign Keys, WAL, `synchronous=FULL`, Transaktionen, hashgebundenen Migrationen und Vor-Migrations-Sicherungen. I011 führt Migration `0004_sync_journal_snapshots.sql` ein und hebt das Datenbankschema auf Version 4.

Ein neuer Journal-Snapshot wird innerhalb derselben `BEGIN IMMEDIATE`-Transaktion wie Nutzdaten, Baselines, Linkfortschreibung und Audit-Receipt geschrieben. Ein Crash darf deshalb weder ein Receipt ohne Snapshot noch einen Snapshot ohne zugehörigen Commit hinterlassen.

Ein RecoveryPlan darf historische Werte niemals frei aus dem Journal zurückschreiben. Ein historischer Zielwert muss im aktuellen Datenstand auf mindestens einer Seite beweisbar vorhanden sein und über die bestehende Link-Richtung durch denselben I009-Transaktionskern übertragen werden können. Andernfalls bleibt der Plan blockiert.

## 8. Globale Standards
Verbindliche Standards liegen unter `standards/` und sind über `standards/STANDARD_INDEX.json` registriert. Der Vorrang lautet `PROVOWARE_GLOBAL_STANDARD → PROJECT_CONTRACT → Modulvertrag → konkrete Konfiguration`.

## 9. Repository-Vollständigkeit
`REPOSITORY_MANIFEST.json` ist das Soll-Inventar des vollständigen Entwicklungsbaums. Jede Iteration prüft fehlende und unerwartete Dateien, Projekt-/Versionskonsistenz, Manifeste, SHA-256-Nachweise und relevante Dateimodi.

## 10. Autonomer Entwicklungs- und Prüfautopilot
`tools/autopilot/autopilot.py qualifizieren` führt globale Standards und alle historischen Pflichtgates bis zur aktuellen Iteration aus. `FAIL` und `NOT_RUN` blockieren Freigaben. Die Remoteprüfung endet mit einem exakten Evidence-SHA-Zweitpass.

## 11. Historische Entwicklung
- **I002:** Manifest-/Evidence-Kette und Remote-Tree-Receipt.
- **I003:** Klick-&-Start-Orchestrator und sichere Recovery-Basis.
- **I004:** Kalender-Domainkern und SQLite.
- **I005:** Kalender-GUI und 112er Offscreen-Matrix.
- **I006:** Todo-Domain, Soft-Link und Crash-/Rollback-Matrix.
- **I007:** Todo-GUI und 140er Offscreen-Matrix.
- **I008:** read-only Synchronisationsvorschau.
- **I009:** Feld-Baselines, Drei-Wege-Vergleich, atomarer SyncPlan und Audit-Receipt.
- **I010:** Synchronisations-Control-GUI und immutable ResolutionPlan.
- **I011:** read-only Journal, hashgebundene Vorher-/Nachher-Snapshots und stale-sichere RecoveryPlans.

## 12. Kalender↔Todo-Kopplungsvertrag
Todo und Termin bleiben eigenständige Objekte. Die Kopplung ist ein versionierter Soft-Link. Physische Endpunktlöschung ist geschützt; Entkoppeln löscht keine Nutzdaten.

## 13. Read-only Synchronisationsvorschau
`SynchronizationPreviewService` bleibt als reine Diagnoseebene ohne Schreibschnittstelle erhalten. Sie wird durch I009–I011 nicht ersetzt.

## 14. Feld-Baseline und Drei-Wege-Vergleich
Für `TITLE`, `DESCRIPTION`, `START_AT` und `DUE_END` werden typisierte kanonische Werte und SHA-256-Feldzustände verwendet. `BOTH_DIFFERENT`, fehlende Baselines und getrennte Endpunkte bleiben fail-closed. `due_at ↔ end_at` bleibt semantisch prüfpflichtig.

## 15. Transaktionaler Sync-, Resolution- und Recovery-Pfad
Der verbindliche Schreibpfad bleibt:
`PRECHECK → atomarer COMMIT → POSTCHECK → Audit-Receipt → quick_check`.

I010 verändert einen erkannten SyncPlan nicht, sondern erzeugt einen neuen ResolutionPlan. I011 verändert weder alte Receipts noch alte Entscheidungen, sondern erzeugt bei einer zulässigen Recovery einen neuen immutable RecoveryPlan. Jeder neue Plan bindet Quellnachweis, aktuellen Plan, aktuelle Objektversionen und aktuelle Feld-Hashes.

## 16. Aktueller Checkpoint
**C011 — SYNC-JOURNAL-RECOVERY.** Implementiert werden das read-only Synchronisationsjournal, Migration 0004, atomare Snapshot-Nachweise, Integritätsprüfung alter und neuer Receipts, Vorher-/Nachher-Diff, immutable RecoveryPlans sowie eigene Fault-/Crash- und GUI-Matrizen. I011 ist vollständig qualifiziert; der Evidence-SHA-Zweitpass bleibt die verbindliche Promotionsvoraussetzung für `main`.

Alte I009/I010-Receipts ohne Snapshot werden ausdrücklich als `LEGACY_NO_SNAPSHOT` dargestellt: auditierbar, aber nicht automatisch recoverbar. Manipulierte Receipt-/Snapshot-Daten werden als `TAMPERED` hart blockiert.

## 17. Nächster logischer Schritt
Nach erfolgreicher I011-Qualifikation: **I012 — Dashboard + Diagnose-/Recovery-Zentrale.** Dort sollen Journal-Integrität, Datenbankzustand, Sicherungsstatus, Startdiagnose und blockierte RecoveryPläne read-only zusammengeführt werden.

## 18. Weiterführende Verbesserung
Die Diagnosezentrale soll niemals einen zweiten Reparaturpfad eröffnen. Sie darf nur qualifizierte Fachservices aufrufen und sollte jeden risikobehafteten Vorgang über einen neuen, unveränderlichen Plan mit PRECHECK und nachvollziehbarem Receipt freigeben.

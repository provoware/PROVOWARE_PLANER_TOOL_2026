# PROVOWARE PLANER TOOL 2026

Privates, portables und vollständig offline ausgerichtetes Ein-Nutzer-Planungswerkzeug für Linux. Entwicklungs-Repository, Nutzerpaket, Evidence und persönliche Sicherungen bleiben technisch getrennte Bereiche.

<!-- PROVOWARE:SECTION:PROJECT_STATUS -->
## 1. Projektstatus
- **Version:** `0.16.0-dev.1`
- **Iteration:** `I016`
- **Checkpoint:** `C016-RESTORE-EXECUTION-SAFETY`
- **Status:** `IN_ARBEIT / GELB` bis zur vollständigen Remotequalifikation
- **Zielplattform:** Linux, insbesondere Ubuntu-/Kubuntu-Derivate
- **Betrieb:** lokal und offline-first

Die maschinenlesbare Wahrheit liegt in `VERSION.json`, `PROJEKTSTATUS.json`, `PROJECT_CONTRACT.json` und `ITERATION_PLAN.json`.

<!-- PROVOWARE:SECTION:PRODUCT -->
## 2. Was ist das Tool?
PROVOWARE PLANER verbindet Kalender, Aufgabenplanung, Synchronisationskontrolle, Journal, Diagnose und sichere lokale Wiederherstellung. Nutzerdaten liegen im gewählten Arbeitsbereich und gehören nicht in Programm- oder Entwicklungsordner.

## 3. Kernmodule
- **Kalender:** Tag, Woche, Monat, Jahr und editierbare Markierungen.
- **Todo:** Aufgaben, Status, Priorität, Fälligkeit, Unteraufgaben und Fortschritt.
- **Synchronisation:** Feld-Baselines, Drei-Wege-Vergleich, Sync-/Resolution-/Recovery-Pläne und Audit-Receipts.
- **Diagnose:** read-only Start-, SQLite-, Journal-, Backup- und Recovery-Nachweise.
- **Backup/Restore I015:** read-only Kandidatenqualifikation, immutable RestorePlan, exakte Precondition und rollbackfähiger Postcheck.
- **Restore Execution Safety I016:** persistenter Intent, exklusive Lease, sicherer Vorzustands-Snapshot und deterministische Crash-Recovery.

## 4. Transportprofile
Der normale Transport ist nicht „alles als ZIP“.
- **NUTZER** *(Standard)*: lauffähiger Produktkern + kurze Nutzeranleitung.
- **PROJEKTKERN**: nur technischer Produktkern.
- **ENTWICKLER**: Produktkern + Tests, Standards, Entwicklerwerkzeuge, Verträge und Entwicklungsdokumentation; ohne Evidence.
- **EVIDENCE**: Nachweise/Receipts/Manifeste + minimaler Versionskontext; ohne Produktquellbaum.

**Nutzdaten und Sicherungen sind kein Code-Transportprofil.** SQLite-Dateien, Backups, Restore-Kandidaten, Pre-Restore-Abbilder, Restore-Intent/Lease, Workspace-Berichte, Logs und temporäre Dateien werden in allen Codepaketen ausgeschlossen.

## 5. Paketintegrität
Jedes erzeugte Paket erhält `PAKETMANIFEST.json` und `PAKET_INVENTAR.json`. Lauffähige Profile erhalten zusätzlich ein paketbezogenes `SHA256_DATEI_INVENTAR.json`.

## 6. Klick-&-Start
Vor dem bisherigen Start-Orchestrator prüft I016, ob ein vorheriger Restore nach einem Prozessabbruch offen geblieben ist. Eindeutige Zustände werden sicher abgeschlossen; uneindeutige Zustände blockieren den Start. Danach prüft der bestehende Start-Orchestrator System, Runtime, Programmintegrität, Workspace, Datenbank, Migrationen, Recovery und GUI.

## 7. Daten und Sicherheit
SQLite arbeitet mit Foreign Keys, WAL, `synchronous=FULL`, Transaktionen und hashgebundenen Migrationen. I016 verändert weder Tabellenstruktur noch Nutzdatenmodell; Schema bleibt Version 4.

<!-- PROVOWARE:SECTION:GLOBAL_STANDARDS -->
## 8. Globale Standards
Verbindliche Standards liegen unter `standards/`. I016 ergänzt `PROVOWARE-RESTORE-EXECUTION 1.0.0`. Der Vorrang bleibt `PROVOWARE_GLOBAL_STANDARD → PROJECT_CONTRACT → Modulvertrag → Konfiguration`.

<!-- PROVOWARE:SECTION:REPOSITORY -->
## 9. Repository-Vollständigkeit
Das Repository bleibt die vollständige auditierbare Entwicklungsbasis. Sein Soll entsteht aus qualifizierter Baseline + deklariertem `add/modify/delete`-Delta. Transportpakete besitzen eigene profilbezogene Inventare.

<!-- PROVOWARE:SECTION:AUTOPILOT -->
## 10. Autonomer Entwicklungs- und Prüfautopilot
Die Reihenfolge bleibt:

`Ermittlung → Planung → P0 Static → P1 Zielprüfung → P2 Runtime → P3 Regression → P4 Evidence → P5 Promotion → Optimierung`

I016 ergänzt als Pflichtgates Lease-/Intent-Prüfung, echten Prozessabbruch nach dem atomaren Datenbanktausch, Start-Recovery, Snapshot-Rollback und Transportregression.

## 11. Historische Entwicklung
- **I002–I012:** Evidence, Start, Kalender, Todo, Synchronisation, Journal/Recovery und Diagnose.
- **I013:** Entwicklungsautopilot V2.
- **I014:** Trennung von Produktkern, Nutzerpaket, Entwicklerbasis, Evidence und Sicherungen.
- **I015:** hashgebundener Backup-/RestorePlan und planpflichtiger Restorepfad.
- **I016:** persistenter Restore-Intent, exklusive Lease und Crash-Recovery.

## 12. Restore-Intent und Lease
Vor einem destruktiven Commit setzt I016 eine exklusive Restore-Lease. Neue Planner-Schreibtransaktionen werden blockiert. Ein hashgebundener Intent hält die Zustände `PREPARED → COMMITTING → VERIFIED → CLOSED` dauerhaft fest.

## 13. Sicherer Vorzustand
Vor `COMMITTING` wird über die SQLite-Backup-API ein konsistenter Vorzustand erzeugt, per SHA-256 gebunden, mit `quick_check` geprüft und fachlich gegen den aktiven Datenbestand verglichen.

## 14. Harter Prozessabbruch
Bleibt der Prozess in `COMMITTING` stehen, prüft der nächste Start den tatsächlichen Datenbankzustand. Ein eindeutig erfolgreicher Restore wird finalisiert, ein eindeutig unveränderter Zustand ohne Datenänderung geschlossen. Nur ein verifizierter Sicherheits-Snapshot darf einen uneindeutigen Zwischenzustand zurücksetzen; Vermutungen sind verboten.

## 15. Ein physischer Restorekern
Der tatsächliche Dateiaustausch bleibt ausschließlich in `storage.backup.restore_backup()`. I016 verändert `storage/backup.py` nicht und erzeugt keinen zweiten physischen Restorepfad.

<!-- PROVOWARE:SECTION:CHECKPOINT -->
## 16. Aktueller Checkpoint
**C016 — RESTORE-EXECUTION-SAFETY.** Persistenter Intent, exklusive Lease, Planner-Schreibguard, konsistenter Pre-Restore-Snapshot und Start-Recovery werden qualifiziert.

<!-- PROVOWARE:SECTION:NEXT_STEP -->
## 17. Nächster logischer Schritt
Nach qualifiziertem I016: **I017 — Restore-Control-GUI**. Sie darf ausschließlich `RestoreExecutionService` verwenden und muss Vorschau, Risikoanzeige, Bestätigung und Ausführung klar trennen.

<!-- PROVOWARE:SECTION:IMPROVEMENT -->
## 18. Weiterführende Verbesserung
Vor einer Stable-Linie bleiben Repository-Sichtbarkeit, Branch-Schutz für `main` und signierte Release-/Evidence-Commits offen. Die Restore-Oberfläche wird erst auf den qualifizierten I016-Pfad gesetzt.

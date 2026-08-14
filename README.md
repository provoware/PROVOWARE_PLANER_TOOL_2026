# PROVOWARE PLANER TOOL 2026

Privates, portables und vollständig offline ausgerichtetes Ein-Nutzer-Planungswerkzeug für Linux. Entwicklungs-Repository, Nutzerpaket, Evidence und persönliche Sicherungen bleiben technisch getrennte Bereiche.

<!-- PROVOWARE:SECTION:PROJECT_STATUS -->
## 1. Projektstatus
- **Version:** `0.15.0-dev.1`
- **Iteration:** `I015`
- **Checkpoint:** `C015-BACKUP-RESTOREPLAN`
- **Status:** `QUALIFIZIERT / GRÜN`
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

## 4. Transportprofile
Der normale Transport ist nicht „alles als ZIP“.
- **NUTZER** *(Standard)*: lauffähiger Produktkern + kurze Nutzeranleitung.
- **PROJEKTKERN**: nur technischer Produktkern.
- **ENTWICKLER**: Produktkern + Tests, Standards, Entwicklerwerkzeuge, Verträge und Entwicklungsdokumentation; ohne Evidence.
- **EVIDENCE**: Nachweise/Receipts/Manifeste + minimaler Versionskontext; ohne Produktquellbaum.

**Nutzdaten und Sicherungen sind kein Code-Transportprofil.** SQLite-Dateien, Backups, Restore-Kandidaten, Pre-Restore-Abbilder, Workspace-Berichte, Logs und temporäre Dateien werden in allen Codepaketen ausgeschlossen.

## 5. Paketintegrität
Jedes erzeugte Paket erhält `PAKETMANIFEST.json` und `PAKET_INVENTAR.json`. Lauffähige Profile erhalten zusätzlich ein paketbezogenes `SHA256_DATEI_INVENTAR.json`.

## 6. Klick-&-Start
Der Start-Orchestrator prüft System, Runtime, Programmintegrität, Workspace, Datenbank, Migrationen, Recovery und GUI. Persönliche Daten bleiben im externen Arbeitsbereich.

## 7. Daten und Sicherheit
SQLite arbeitet mit Foreign Keys, WAL, `synchronous=FULL`, Transaktionen und hashgebundenen Migrationen. I015 verändert weder Tabellenstruktur noch Nutzdatenmodell; Schema bleibt Version 4.

<!-- PROVOWARE:SECTION:GLOBAL_STANDARDS -->
## 8. Globale Standards
Verbindliche Standards liegen unter `standards/`. I015 ergänzt `PROVOWARE-BACKUP-RESTORE 1.0.0`. Der Vorrang bleibt `PROVOWARE_GLOBAL_STANDARD → PROJECT_CONTRACT → Modulvertrag → Konfiguration`.

<!-- PROVOWARE:SECTION:REPOSITORY -->
## 9. Repository-Vollständigkeit
Das Repository bleibt die vollständige auditierbare Entwicklungsbasis. Sein Soll entsteht aus qualifizierter Baseline + deklariertem `add/modify/delete`-Delta. Transportpakete besitzen eigene profilbezogene Inventare.

<!-- PROVOWARE:SECTION:AUTOPILOT -->
## 10. Autonomer Entwicklungs- und Prüfautopilot
Die Reihenfolge bleibt:

`Ermittlung → Planung → P0 Static → P1 Zielprüfung → P2 Runtime → P3 Regression → P4 Evidence → P5 Promotion → Optimierung`

I015 ergänzt als Pflichtgates Kandidatenqualifikation, Plan-Tamper/Stale-Prüfung, echten Restore-Rollbacktest, Prozessabbruch vor physischem Schreibzugriff und Transportregression.

## 11. Historische Entwicklung
- **I002–I012:** Evidence, Start, Kalender, Todo, Synchronisation, Journal/Recovery und Diagnose.
- **I013:** Entwicklungsautopilot V2.
- **I014:** Trennung von Produktkern, Nutzerpaket, Entwicklerbasis, Evidence und Sicherungen.
- **I015:** hashgebundener Backup-/RestorePlan und planpflichtiger Restorepfad.

## 12. Kandidatenqualifikation
Ein Restore-Kandidat wird ausschließlich lesend geprüft. Pflicht sind: reguläre Datei, erlaubter Backup-Bereich, Manifest, SHA-256, Größe, SQLite `quick_check` und exakt kompatibles Schema 4. Ein Kandidat außerhalb des Workspace-/Backup-Bereichs wird blockiert.

## 13. Immutable RestorePlan
Der RestorePlan bindet Backup-Pfad/-Hash/-Größe, Manifest-Pfad/-Hash, Backup-Schema, Zielpfad, Zielzustand, Vorhandensein, Zustandsgröße und Erstellzeit in einen kanonischen SHA-256-Planhash. Nachträgliche Planmanipulation blockiert.

## 14. WAL-sensitiver Stale-Schutz
Die aktive Datenbank wird nicht nur über die Hauptdatei gebunden. Der Zielzustands-Hash umfasst Hauptdatenbank und WAL. Änderungen nach Planerstellung werden dadurch auch dann erkannt, wenn SQLite sie noch nicht in die Hauptdatei eingecheckpointet hat.

## 15. Ein physischer Restorekern
Der tatsächliche Dateiaustausch bleibt ausschließlich in `storage.backup.restore_backup()`. `RestoreService` darf weder `os.replace` noch eigene Kopier-/Austauschlogik besitzen. Ablauf: `PRECHECK → COMMIT → POSTCHECK`. Scheitert der Postcheck, wird der vorherige Datenbankstand über den bestehenden Rollbackpfad wiederhergestellt.

<!-- PROVOWARE:SECTION:CHECKPOINT -->
## 16. Aktueller Checkpoint
**C015 — BACKUP-RESTOREPLAN.** Implementiert werden read-only Kandidatenqualifikation, immutable RestorePlan, Main+WAL-Precondition, finaler Precheck im physischen Kern, planpflichtiger Commit und rollbackfähiger Postcheck.

<!-- PROVOWARE:SECTION:NEXT_STEP -->
## 17. Nächster logischer Schritt
Nach qualifiziertem I015: **I016 — Restore-Control-GUI**. Sie darf ausschließlich `RestoreService` verwenden und muss Vorschau, Risikoanzeige und tatsächliche Ausführung klar voneinander trennen.

<!-- PROVOWARE:SECTION:IMPROVEMENT -->
## 18. Weiterführende Verbesserung
Vor einer Stable-Linie bleiben Repository-Sichtbarkeit, Branch-Schutz für `main` und signierte Release-/Evidence-Commits offen. Für Restore bleibt zusätzlich ein späteres persistentes Crash-Intent/Recovery-Protokoll sinnvoll, falls auch ein harter Prozessabbruch *nach* dem atomaren Dateiaustausch vollständig als eigener Recovery-Zustand nachweisbar werden soll.

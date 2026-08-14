# PROVOWARE PLANER TOOL 2026

Privates, portables und vollständig offline ausgerichtetes Ein-Nutzer-Planungswerkzeug für Linux. Der Planner wird als wartbarer modularer Monolith entwickelt und autonom qualifiziert.

## 1. Projektstatus
- **Version:** `0.12.0-dev.1`
- **Iteration:** `I012`
- **Checkpoint:** `C012-DIAGNOSE-DASHBOARD`
- **Status:** `IN_ARBEIT / GELB` bis zur vollständigen I012-Remotequalifikation
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
I009 führt Feld-Baselines, Drei-Wege-Vergleich, atomare SyncPlans und Audit-Receipts ein. I010 ergänzt die explizite, hashgebundene Konfliktentscheidung über ResolutionPlans. I011 ergänzt ein read-only Synchronisationsjournal und stale-sichere RecoveryPlans.

### Diagnose- und Recovery-Zentrale
I012 bündelt fünf vorhandene Nachweisbereiche in einer gemeinsamen read-only Oberfläche: Startzustand, SQLite-Integrität, Journal-Integrität, Backup-Nachweise und Recovery-Blockaden. Die Zentrale besitzt keinen eigenen Reparatur-, Restore-, Sync- oder Recovery-Commit-Pfad.

## 4. Oberfläche und globale Gestaltung
Die Oberfläche verwendet zentrale Designregeln, skalierbare Schrift, Tastaturnavigation und textliche Statusaussagen. Farbe allein trägt keine Bedeutung.

## 5. Ampelsystem
- ● **GRÜN – BEREIT**
- ▲ **GELB – EINGESCHRÄNKT**
- ● **ROT – BLOCKIERT**

Gelb bedeutet in I012 auch: ein optionaler Nachweis fehlt oder ein RecoveryPlan wird absichtlich sicher blockiert. Rot ist für echte Integritäts-, Manipulations- oder Lesefehler reserviert.

## 6. Klick-&-Start
Der Start-Orchestrator prüft Betriebssystem, Runtime, Programmdateien, Manifeste, Konfiguration, Workspace, Datenbank, Migrationen, Recovery, Module und GUI. Relevante Aktionen folgen `PRECHECK → AKTION → POSTCHECK`.

I012 speichert den ohnehin erzeugten Startbericht standardmäßig atomar als `LETZTER_STARTBERICHT.json` im Arbeitsbereich. Die Diagnosezentrale liest diesen Nachweis nur.

## 7. Daten und Sicherheit
SQLite arbeitet mit Foreign Keys, WAL, `synchronous=FULL`, Transaktionen, hashgebundenen Migrationen und Vor-Migrations-Sicherungen. Das Datenbankschema bleibt in I012 unverändert auf Version 4; I012 führt bewusst keine neue Migration ein.

Die Datenbankdiagnose öffnet die aktive SQLite-Datei mit `mode=ro`, setzt `PRAGMA query_only=ON` und führt `quick_check` aus. Backup-Kandidaten werden ebenso ausschließlich lesend auf SQLite-Integrität, Manifest und SHA-256 geprüft.

Ein RecoveryPlan darf historische Werte niemals frei aus dem Journal zurückschreiben. I012 zeigt lediglich neu berechnete I011-Recovery-Vorschauen und deren Blockierungsgründe an; ausgeführt wird nichts.

## 8. Globale Standards
Verbindliche Standards liegen unter `standards/` und sind über `standards/STANDARD_INDEX.json` registriert. Der Vorrang lautet `PROVOWARE_GLOBAL_STANDARD → PROJECT_CONTRACT → Modulvertrag → konkrete Konfiguration`.

## 9. Repository-Vollständigkeit
`REPOSITORY_MANIFEST.json` ist das Soll-Inventar des vollständigen Entwicklungsbaums. Jede Iteration prüft fehlende und unerwartete Dateien, Projekt-/Versionskonsistenz, Manifeste, SHA-256-Nachweise und relevante Dateimodi.

## 10. Autonomer Entwicklungs- und Prüfautopilot
`tools/autopilot/autopilot.py qualifizieren` führt globale Standards und alle historischen Pflichtgates bis zur aktuellen Iteration aus. `FAIL` und `NOT_RUN` blockieren Freigaben. I012 ergänzt das `I012-DIAGNOSE-DASHBOARD-GATE`.

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
- **I012:** read-only Diagnose-/Recovery-Zentrale mit Start-, Datenbank-, Journal-, Backup- und Recovery-Nachweisen.

## 12. Kalender↔Todo-Kopplungsvertrag
Todo und Termin bleiben eigenständige Objekte. Die Kopplung ist ein versionierter Soft-Link. Physische Endpunktlöschung ist geschützt; Entkoppeln löscht keine Nutzdaten.

## 13. Read-only Diagnoseprinzip
Die Diagnosezentrale ist Beobachter, nicht Reparaturinstanz. Sie darf keine Migration ausführen, kein Backup wiederherstellen, keinen Sync committen, keinen RecoveryPlan committen und keine Nutzdaten verändern. Für risikobehaftete Aktionen bleiben ausschließlich die bereits qualifizierten Fachservices zuständig.

## 14. Feld-Baseline und Drei-Wege-Vergleich
Für `TITLE`, `DESCRIPTION`, `START_AT` und `DUE_END` werden typisierte kanonische Werte und SHA-256-Feldzustände verwendet. `BOTH_DIFFERENT`, fehlende Baselines und getrennte Endpunkte bleiben fail-closed. `due_at ↔ end_at` bleibt semantisch prüfpflichtig.

## 15. Transaktionaler Sync-, Resolution- und Recovery-Pfad
Der verbindliche Schreibpfad bleibt:
`PRECHECK → atomarer COMMIT → POSTCHECK → Audit-Receipt → quick_check`.

I012 fügt diesem Pfad keinen neuen Schreiber hinzu. Die Recovery-Diagnose verwendet ausschließlich `build_recovery()` als Vorschau und zeigt `READY` beziehungsweise sichere Blockaden an.

## 16. Aktueller Checkpoint
**C012 — DIAGNOSE-DASHBOARD.** Implementiert sind `DiagnosticsService`, Diagnose-ViewModel, Qt-Diagnosezentrale, `Ctrl+Shift+D`-Integration, standardmäßig gespeicherter letzter Startbericht, Service-/GUI-Zieltests und eine 35er Offscreen-Matrix.

Vor Promotion nach `main` müssen I002→I012, I012-Zieltests, die 35er Diagnose-GUI-Matrix, die bestehenden Todo-/Kalender-/Sync-/Crashregressionen, die komplette Unit-Suite, Standards, Repository-Inventar, Remote-Tree und ein exakter read-only Evidence-SHA-Zweitpass erfolgreich sein.

## 17. Nächster logischer Schritt
Nach vollständig qualifiziertem I012: **I013 — immutable Backup-/RestorePlan mit Kandidatenqualifikation.** Die bestehende Backup-/Restore-Implementierung soll dabei wiederverwendet werden; Vorschau und tatsächliche Wiederherstellung bleiben strikt getrennt.

## 18. Weiterführende Verbesserung
Vor einer Stable-Linie sollten zusätzlich Repository-Sichtbarkeit, Schutz von `main` mit verbindlichen Statuschecks und signierte Release-/Evidence-Commits geschlossen werden, ohne die funktionale Entwicklung mit einer parallelen Freigabelogik zu vermischen.

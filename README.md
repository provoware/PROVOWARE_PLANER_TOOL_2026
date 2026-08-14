# PROVOWARE PLANER TOOL 2026

Privates, portables und vollständig offline ausgerichtetes Ein-Nutzer-Planungswerkzeug für Linux. Der Planner wird als wartbarer modularer Monolith entwickelt und autonom qualifiziert.

<!-- PROVOWARE:SECTION:PROJECT_STATUS -->
## 1. Projektstatus
- **Version:** `0.13.0-dev.1`
- **Iteration:** `I013`
- **Checkpoint:** `C013-ENTWICKLUNGSAUTOPILOT-V2`
- **Status:** `IN_ARBEIT / GELB` bis zur vollständigen I013-Remotequalifikation
- **Zielplattform:** Linux, insbesondere Ubuntu-/Kubuntu-Derivate
- **Betrieb:** lokal und offline-first
- **Technische Nutzerabnahme:** nicht Bestandteil der Pflicht-Freigabekette

Die maschinenlesbare Wahrheit liegt in `VERSION.json`, `PROJEKTSTATUS.json`, `PROJECT_CONTRACT.json` und ab I013 zusätzlich in `ITERATION_PLAN.json`.

<!-- PROVOWARE:SECTION:PRODUCT -->
## 2. Was ist das Tool?
PROVOWARE PLANER verbindet Kalender, Aufgabenplanung, Synchronisationskontrolle, Journal, Diagnose und spätere Zusatzmodule. Nutzerdaten bleiben lokal im ausgewählten Arbeitsbereich.

## 3. Kernmodule
### Kalender
Tag, Woche, Monat und Jahr; Termine und fünf editierbare Markierungen.

### Todo
Aufgaben, Status, Priorität, Fälligkeit, Unteraufgaben, Fortschritt und sichere Kalender-Verknüpfungen.

### Synchronisation
I009 führt Feld-Baselines, Drei-Wege-Vergleich, atomare SyncPlans und Audit-Receipts ein. I010 ergänzt explizite Konfliktentscheidungen, I011 das read-only Journal und stale-sichere RecoveryPlans.

### Diagnose- und Recovery-Zentrale
I012 bündelt Startzustand, SQLite-Integrität, Journal-Integrität, Backup-Nachweise und Recovery-Blockaden read-only.

### Entwicklungsautopilot V2
I013 verbessert die Entwicklungskette selbst: Baseline-Identität, maschinenlesbarer Iterationsplan, explizite Dateidifferenz, statischer Fail-Fast-Preflight, planbasiertes Repository-Soll, Gate-Deduplizierung, Timing-Evidence und weiterhin exakter SHA-Zweitpass.

## 4. Oberfläche und globale Gestaltung
Die Oberfläche verwendet zentrale Designregeln, skalierbare Schrift, Tastaturnavigation und textliche Statusaussagen. Farbe allein trägt keine Bedeutung.

## 5. Ampelsystem
- ● **GRÜN – BEREIT**
- ▲ **GELB – EINGESCHRÄNKT / PRÜFUNG AUSSTEHEND**
- ● **ROT – BLOCKIERT**

## 6. Klick-&-Start
Der Start-Orchestrator prüft Betriebssystem, Runtime, Programmdateien, Manifeste, Konfiguration, Workspace, Datenbank, Migrationen, Recovery, Module und GUI. Relevante Aktionen folgen `PRECHECK → AKTION → POSTCHECK`.

## 7. Daten und Sicherheit
SQLite arbeitet mit Foreign Keys, WAL, `synchronous=FULL`, Transaktionen, hashgebundenen Migrationen und Vor-Migrations-Sicherungen. I013 verändert weder Datenbankschema noch Nutzdatenlogik.

<!-- PROVOWARE:SECTION:GLOBAL_STANDARDS -->
## 8. Globale Standards
Verbindliche Standards liegen unter `standards/` und sind über `standards/STANDARD_INDEX.json` registriert. I013 ergänzt `PROVOWARE-DEVELOPMENT 2.0.0`. Der Vorrang lautet `PROVOWARE_GLOBAL_STANDARD → PROJECT_CONTRACT → Modulvertrag → konkrete Konfiguration`.

<!-- PROVOWARE:SECTION:REPOSITORY -->
## 9. Repository-Vollständigkeit
Ab I013 wird das Repository-Soll nicht mehr aus dem aktuellen Arbeitsbaum selbst abgeleitet. Es entsteht aus der letzten qualifizierten Baseline plus der in `ITERATION_PLAN.json` deklarierten `add`/`modify`/`delete`-Differenz. Jeder ungeplante Pfad blockiert die Qualifikation.

<!-- PROVOWARE:SECTION:AUTOPILOT -->
## 10. Autonomer Entwicklungs- und Prüfautopilot
Die neue Reihenfolge lautet:

`Ermittlung → Planung → P0 Static → P1 Zielprüfung → P2 Runtime → P3 Regression → P4 Evidence → P5 Promotion → Optimierung`

P0 läuft ohne apt, pip, Qt oder Anwendungsruntime. Erst nach erfolgreicher statischer Prüfung dürfen Runtime-Abhängigkeiten installiert werden. Vollständige Testsuite und historische Gate-Kette laufen pro Pass jeweils genau einmal. `tools/autopilot/autopilot.py` misst zusätzlich die Gate-Laufzeiten.

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
- **I011:** read-only Journal, hashgebundene Snapshots und RecoveryPlans.
- **I012:** read-only Diagnose-/Recovery-Zentrale.
- **I013:** Entwicklungsautopilot V2 mit Static-first, planbasiertem Inventar und Gate-Deduplizierung.

## 12. Kalender↔Todo-Kopplungsvertrag
Todo und Termin bleiben eigenständige Objekte. Die Kopplung ist ein versionierter Soft-Link. Physische Endpunktlöschung ist geschützt; Entkoppeln löscht keine Nutzdaten.

## 13. Entwicklungspräzision
`PROCESS_AUDIT_I012.json` dokumentiert die Prozessbaseline. Zwei vermeidbare I012-Remote-Fehlversuche wurden korrekt blockiert, aber zu spät erkannt: ein statischer GUI-Vertragsfehler und ein Dokumentationsstrukturfehler. I013 verschiebt beide Fehlerklassen in P0.

## 14. Dokumentationsvertrag
Maschinenprüfungen verwenden ab I013 stabile semantische README-Marker. Dadurch bleibt die Struktur verbindlich, während Überschriften sprachlich verbessert werden können, ohne einen rein textuellen Fehlalarm auszulösen.

## 15. Evidence- und Promotionspfad
Der Exact-SHA-Zweitpass bleibt verbindlich und read-only. Promotion nach `main` ist nur bei `ahead > 0`, `behind = 0`, passender Merge-Base und ohne `force` zulässig. Danach folgt weiterhin eine unabhängige Main-Nachqualifikation.

<!-- PROVOWARE:SECTION:CHECKPOINT -->
## 16. Aktueller Checkpoint
**C013 — ENTWICKLUNGSAUTOPILOT-V2.** Implementiert werden Entwicklungsstandard 2.0, Pipelinevertrag, Iterationsplan, I012-Prozessaudit, planbasiertes Kandidateninventar, statischer P0-Preflight, deduplizierter/timingfähiger Autopilot, robuste Dokumentationsmarker und effizientere CI-Reihenfolge.

<!-- PROVOWARE:SECTION:NEXT_STEP -->
## 17. Nächster logischer Schritt
Nach vollständig qualifiziertem I013: **I014 — immutable Backup-/RestorePlan mit Kandidatenqualifikation.** Diese sicherheitskritische Funktion wird erstmals vollständig unter dem neuen Entwicklungsvertrag umgesetzt.

<!-- PROVOWARE:SECTION:IMPROVEMENT -->
## 18. Weiterführende Verbesserung
Vor einer Stable-Linie bleiben Repository-Sichtbarkeit, Schutz von `main` mit verbindlichen Statuschecks und signierte Release-/Evidence-Commits als Infrastrukturhärtung offen. Sie sollen getrennt von fachlicher Feature-Logik geschlossen werden.

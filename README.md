# PROVOWARE PLANER TOOL 2026

Privates, portables und vollständig offline ausgerichtetes Ein-Nutzer-Planungswerkzeug für Linux. Das Entwicklungs-Repository ist ab I014 ausdrücklich **nicht** mit dem normalen Nutzerpaket gleichzusetzen.

<!-- PROVOWARE:SECTION:PROJECT_STATUS -->
## 1. Projektstatus
- **Version:** `0.14.0-dev.1`
- **Iteration:** `I014`
- **Checkpoint:** `C014-TRANSPORTPROFILE-TRENNUNG`
- **Status:** `QUALIFIZIERT / GRÜN`
- **Zielplattform:** Linux, insbesondere Ubuntu-/Kubuntu-Derivate
- **Betrieb:** lokal und offline-first

Die maschinenlesbare Wahrheit liegt in `VERSION.json`, `PROJEKTSTATUS.json`, `PROJECT_CONTRACT.json` und `ITERATION_PLAN.json`.

<!-- PROVOWARE:SECTION:PRODUCT -->
## 2. Was ist das Tool?
PROVOWARE PLANER verbindet Kalender, Aufgabenplanung, Synchronisationskontrolle, Journal und Diagnose. Nutzerdaten liegen im frei gewählten Arbeitsbereich und gehören nicht in den Programm- oder Entwicklungsordner.

## 3. Kernmodule
- **Kalender:** Tag, Woche, Monat, Jahr und editierbare Markierungen.
- **Todo:** Aufgaben, Status, Priorität, Fälligkeit, Unteraufgaben und Fortschritt.
- **Synchronisation:** Feld-Baselines, Drei-Wege-Vergleich, Sync-/Resolution-/Recovery-Pläne und Audit-Receipts.
- **Diagnose:** read-only Start-, SQLite-, Journal-, Backup- und Recovery-Nachweise.

## 4. Transportprofile ab I014
Der normale Transport ist nicht mehr „alles als ZIP“.

- **NUTZER** *(Standard)*: lauffähiger Produktkern + kurze `NUTZERANLEITUNG.md`.
- **PROJEKTKERN**: nur technischer Produktkern.
- **ENTWICKLER**: Produktkern + Tests, Standards, Entwicklerwerkzeuge, Verträge und Entwicklungsdokumentation; ohne Evidence.
- **EVIDENCE**: Nachweise/Receipts/Manifeste + minimaler Versionskontext; ohne Produktquellbaum.

**Nutzdaten und Sicherungen sind kein Code-Transportprofil.** SQLite-Dateien, Backups, Restore-Kandidaten, Workspace-Berichte, Logs und temporäre Dateien werden in allen Codepaketen hart ausgeschlossen.

## 5. Paketintegrität
Jedes erzeugte Paket erhält `PAKETMANIFEST.json` und `PAKET_INVENTAR.json`. Lauffähige Profile erhalten zusätzlich ein paketbezogenes `SHA256_DATEI_INVENTAR.json`, damit der vorhandene Start-Orchestrator die reduzierte Paketmenge statt des vollständigen Entwicklungs-Repositorys prüft.

## 6. Klick-&-Start
Der Start-Orchestrator prüft System, Runtime, Programmintegrität, Workspace, Datenbank, Migrationen, Recovery und GUI. Das NUTZER-Paket wird gegen einen **externen** Workspace gestartet; persönliche Daten bleiben dadurch vom Programmordner getrennt.

## 7. Daten und Sicherheit
SQLite arbeitet mit Foreign Keys, WAL, `synchronous=FULL`, Transaktionen, hashgebundenen Migrationen und sicheren Sicherungspfaden. I014 verändert weder Datenbankschema noch Nutzdatenmodell.

<!-- PROVOWARE:SECTION:GLOBAL_STANDARDS -->
## 8. Globale Standards
Verbindliche Standards liegen unter `standards/`. I014 ergänzt `PROVOWARE-TRANSPORT 1.0.0` und erweitert Manifest-/Releaseregeln um getrennte Paketprofile. Der Vorrang bleibt `PROVOWARE_GLOBAL_STANDARD → PROJECT_CONTRACT → Modulvertrag → Konfiguration`.

<!-- PROVOWARE:SECTION:REPOSITORY -->
## 9. Repository-Vollständigkeit
Das Repository bleibt die vollständige auditierbare Entwicklungsbasis. Sein Soll entsteht aus qualifizierter Baseline + deklariertem `add/modify/delete`-Delta. Transportpakete besitzen dagegen **eigene** profilbezogene Inventare. Repository-Inventar und Transport-Inventar sind bewusst unterschiedliche Nachweise.

<!-- PROVOWARE:SECTION:AUTOPILOT -->
## 10. Autonomer Entwicklungs- und Prüfautopilot
Die Reihenfolge bleibt:

`Ermittlung → Planung → P0 Static → P1 Zielprüfung → P2 Runtime → P3 Regression → P4 Evidence → P5 Promotion → Optimierung`

I014 prüft bereits in P0 Profilvertrag, eindeutige Klassifikation, verbotene Transportpfade und das planbasierte Repository-Soll. Erst danach folgen Paketbau, Runtime-Smoke, Regression und Evidence.

## 11. Historische Entwicklung
- **I002–I012:** Evidence, Start, Kalender, Todo, Synchronisation, Journal/Recovery und Diagnose.
- **I013:** Entwicklungsautopilot V2 mit Static-first, planbasiertem Inventar und Gate-Deduplizierung.
- **I014:** Trennung von Produktkern, Nutzerpaket, Entwicklerbasis, Evidence und Nutzdaten/Sicherungen.

## 12. Nutzer- versus Entwicklungsordner
Ein normaler Nutzer muss weder `.github/`, `tests/`, `docs/I...`, `standards/`, `tools/autopilot/`, historische Projektverträge noch Evidence-Receipts transportieren. Diese Inhalte bleiben im Entwicklungs-Repository beziehungsweise in ausdrücklich erzeugten Spezialpaketen.

## 13. Backupgrenze
Sicherungen liegen im Arbeitsbereich bzw. dessen `backups/`-/`Sicherungen/`-Bereich. `.gitignore` und der Transportvertrag sperren typische Datenbank-, Backup-, Restore-, Log-, Cache- und temporäre Dateien zusätzlich. Ein späterer RestorePlan darf diese Grenze nicht wieder aufweichen.

## 14. Deterministischer Paketbau
Der Paketbuilder wählt nur registrierte Repository-Dateien anhand der zentralen Transportklassifikation. ZIP-Reihenfolge, Zeitstempel und Dateimodi sind normalisiert. Gleicher Commit + gleiches Profil muss byte-identische ZIPs erzeugen.

## 15. Evidence- und Promotionspfad
Evidence bleibt ein separates Profil und wird nicht in Nutzer- oder Entwicklerpakete gemischt. Exact-SHA-Zweitpass, Fast-Forward ohne Force und unabhängige Main-Nachqualifikation bleiben unverändert Pflicht.

<!-- PROVOWARE:SECTION:CHECKPOINT -->
## 16. Aktueller Checkpoint
**C014 — TRANSPORTPROFILE-TRENNUNG.** Implementiert werden zentrale Transportklassifikation, NUTZER als sicherer Standard, getrennte Entwickler-/Evidence-Artefakte, harte Nutzdaten-/Backup-Ausschlüsse, deterministischer Paketbuilder, eigenes Paket-Inventar und Fresh-Unpack-Runtime-Abnahme.

<!-- PROVOWARE:SECTION:NEXT_STEP -->
## 17. Nächster logischer Schritt
Nach qualifiziertem I014: **I015 — immutable Backup-/RestorePlan mit Kandidatenqualifikation.** Sicherungen bleiben dabei strikt im Workspace-/Backup-Bereich und außerhalb sämtlicher Code-Transportprofile.

<!-- PROVOWARE:SECTION:IMPROVEMENT -->
## 18. Weiterführende Verbesserung
Vor einer Stable-Linie bleiben Repository-Sichtbarkeit, Branch-Schutz für `main` und signierte Release-/Evidence-Commits als Infrastrukturhärtung offen. Zusätzlich sollen spätere Endnutzer-Releases ausschließlich aus dem qualifizierten NUTZER-Profil entstehen.

# PROVOWARE PLANER TOOL 2026

Privates, portables und vollständig offline ausgerichtetes Ein-Nutzer-Planungswerkzeug für Linux. Das Projekt wird als maximal wartbarer modularer Monolith entwickelt und soll ohne technische Nutzerabnahme autonom qualifiziert werden.

## 1. Projektstatus

- **Version:** `0.1.0-dev.1`
- **Phase:** FOUNDATION
- **Iteration:** I001
- **Checkpoint:** C001-GLOBAL-STANDARDS
- **Ampel:** 🟢 GRÜN – Foundation konsistent angelegt
- **Zielplattform:** Linux, insbesondere Ubuntu-/Kubuntu-Derivate
- **Betrieb:** lokal, offline-first, ohne Cloud-Zwang
- **Technische Nutzerabnahme:** nicht Bestandteil der Freigabekette
- **Releaseziel:** reproduzierbares Linux-Paket plus qualifiziertes ZIP

Die Ampel ist nur eine Zusatzinformation. Ein Status wird immer zusätzlich als Text ausgegeben.

## 2. Was ist das Tool?

PROVOWARE PLANER verbindet Kalender, Aufgabenplanung, Dashboard, Diagnose und spätere Zusatzmodule in einer einheitlichen Oberfläche. Nutzerdaten bleiben lokal. Beim ersten Start wird ein Arbeitsordner gewählt, real auf Lesen und Schreiben geprüft und über eine eindeutige Workspace-ID dauerhaft zugeordnet.

## 3. Kernmodule

### Kalender
Jahres-, Monats-, Wochen- und Tagesansicht, Termine, ganztägige Einträge sowie fünf frei benennbare Markierungen. Markierungen verwenden Farbe plus Text oder Symbol, damit Farbe nie alleinige Information ist.

### Todo
Aufgaben mit Status, Priorität, Fälligkeit, Unteraufgaben, Fortschritt, Filter, Suche und definierter Kalenderkopplung.

### Dashboard
Heute, nächste Termine, fällige und überfällige Aufgaben, Sicherungszustand, Modulstatus, Systemstatus und Schnellaktionen.

### Diagnose und Logging
Jedes relevante Problem soll eindeutig beantworten: Was? Wann? Wo? Wie? Wodurch? Welche Auswirkung? Was kann automatisch getan werden? Was kann der Nutzer tun? Technische Ereignisse erhalten stabile IDs und maschinenlesbare Daten.

## 4. Oberfläche und globale Gestaltung

Alle Module verwenden zentrale Designregeln. Einzelne Module dürfen Abstände, Typografie, Fokusdarstellung oder Statusfarben nicht frei neu erfinden.

Das globale Abstandssystem basiert auf einem 4-Pixel-Raster: 4, 8, 12, 16, 24, 32 und 48 Pixel. Schrift wird über semantische Rollen geführt und global skalierbar gehalten. Freigegebene Stufen sind 90 %, 100 %, 110 %, 125 %, 150 %, 175 % und 200 %.

Geplanter Grundaufbau:
1. Menüleiste
2. kompakte Schnellstart- und Favoritenleiste
3. modulare Tabs
4. aktiver Arbeitsbereich
5. Statusbereich mit Sicherung, Diagnose und Version

## 5. Ampelsystem

- 🟢 **GRÜN – BEREIT:** alle für den Zustand erforderlichen Prüfungen bestanden
- 🟡 **GELB – EINGESCHRÄNKT:** nutzbar, aber mindestens ein nichtkritischer Hinweis besteht
- 🔴 **ROT – BLOCKIERT:** sichere Weiterarbeit oder Freigabe nicht zulässig

Ein kritischer roter Teilstatus macht den Gesamtstatus rot. Ohne Rot, aber mit mindestens einem gelben Teilstatus, wird der Gesamtstatus gelb. Farbe wird nie ohne Symbol und Text verwendet.

## 6. Klick-&-Start-Ziel

Der spätere Start-Orchestrator prüft transparent Betriebssystem, Architektur, Runtime, Programmdateien, Manifeste, Konfiguration, Workspace-ID, reale Lese-/Schreibfähigkeit, Datenbank, Schema, Sicherung, Recovery, Module, Logging, Ereignissystem und GUI. Jede relevante Aktion folgt `PRECHECK → AKTION → POSTCHECK`.

Es werden nur notwendige lokale Komponenten gestartet. Kein eigener Webserver, Broker oder Hintergrunddienst wird ohne zwingenden Grund eingeführt.

## 7. Daten und Sicherheit

Programm, Nutzerdaten, Laufzeitdaten, Konfiguration, Sicherungen und Logs werden strikt getrennt. Für lokale Daten ist SQLite vorgesehen. Schreibvorgänge sollen transaktional erfolgen. Schemaänderungen benötigen Sicherung, Migration und Nachvalidierung. Administratorrechte sind im Normalbetrieb nicht vorgesehen.

## 8. Globale Standards

Die verbindlichen Standards liegen unter `standards/` und werden über `standards/STANDARD_INDEX.json` registriert. Der zentrale Vorrang lautet:

`PROVOWARE_GLOBAL_STANDARD → PROJECT_CONTRACT → Modulvertrag → konkrete Konfiguration`

Aktuell registriert sind Benennung, UI, Barrierefreiheit, Daten, Logging, Tests, Start, Manifeste, Release, Qualität und Dokumentation.

## 9. Repository-Vollständigkeit

`REPOSITORY_MANIFEST.json` ist das Soll-Inventar des gesamten Projektbaums. Jede Iteration muss prüfen:
- fehlt eine erwartete Datei?
- existiert eine unerwartete Datei?
- stimmen Projekt, Version, Iteration und Standards überein?
- sind README, TODO und Statusdateien synchron?

Die Prüfung erfolgt lokal durch den unabhängigen Validator und remote erneut durch GitHub Actions.

## 10. Autonomer Entwicklungs- und Prüfautopilot

Der Einstieg liegt unter `tools/autopilot/`.

- `standard_validator.py` prüft Standards, Verträge, Status, Dokumentation und Repository-Inventar unabhängig vom Erzeuger.
- `autopilot.py pruefen` führt die Foundation-Prüfung aus.
- `autopilot.py qualifizieren` ist der kanonische Qualifikations-Einstieg für die aktuelle Entwicklungsstufe.

Der Validator verwendet in der Foundation ausschließlich die Python-Standardbibliothek und erzeugt klare deutsche Fehlertexte sowie maschinenlesbare Ergebnisse.

## 11. Automatische Qualitätssicherung

Die endgültige Prüfkette wächst stufenweise zu Syntax, statischer Analyse, Typprüfung, Architekturgrenzen, Unit-, Contract- und Property-Tests, Datenbank, Migration, Integration, GUI, Tastatur, Barrierefreiheit, Recovery, Persistenz, Performance, Portabilität, Packaging und reproduzierbarem Release.

Eine Pflichtprüfung kennt nur `PASS`, `FAIL` oder `NOT_RUN`. `FAIL` und `NOT_RUN` blockieren Release. Absolute Fehlerfreiheit wird nicht behauptet; freigegeben wird nur auf Basis nachweisbarer Gates.

## 12. Manifest- und Nachweiskette

Geplant ist die Kette:

`SOURCE_MANIFEST.json → BUILD_MANIFEST.json → RELEASE_MANIFEST.json → EVIDENCE_MANIFEST.json`

`REPOSITORY_MANIFEST.json` sichert bereits ab I001 die Vollständigkeit des Entwicklungsbaums. In I002 werden kryptografische Datei-Hashes, Evidence-Schemata und Remote-Tree-Receipts ergänzt.

## 13. Entwicklung

Kanonischer Ablauf:

`Anforderung → Risikoanalyse → Testdesign → Baseline → Minimalpatch → Zieltests → Regression → Wartbarkeitsprüfung → Evidence → Commit → Remote-Prüfung → Checkpoint`

Große Features, Refactoring und Dependency-Updates werden möglichst getrennt. Jeder relevante behobene Fehler erhält später einen dauerhaften Regressionstest.

## 14. Aktuelle Repository-Struktur

```text
.github/workflows/          Remote-Foundation-Prüfung
standards/                  globale maschinenlesbare Standards
tools/autopilot/            autonomer Prüf- und Entwicklungs-Einstieg
tests/                      automatische Validator-Tests
PROJECT_CONTRACT.json       zentraler Projektvertrag
VERSION.json                kanonische Version
PROJEKTSTATUS.json          maschinenlesbarer Entwicklungsstand
REPOSITORY_MANIFEST.json    vollständiges Soll-Inventar
CHANGELOG.md                nachvollziehbare Änderungen
README.md                   menschliche Projektzentrale
TODO.md                     Roadmap und Checkpoints
```

## 15. Dokumentation

README ist der Einstieg für Nutzer und Entwickler. Maschinenlesbare Wahrheit liegt in den JSON-Verträgen. README, TODO, Version, Projektstatus, Standardindex und Repository-Manifest werden automatisch auf Konsistenz geprüft, damit Dokumentation nicht unbemerkt vom Projektstand abweicht.

## 16. Aktueller Checkpoint

**C001 – GLOBALE STANDARDS / FOUNDATION**

I000 und I001 sind als maschinenlesbares Fundament angelegt. Der unabhängige Standard-Validator und die Remote-Foundation-Qualifikation wurden bewusst vor dem ersten Fachmodul eingeführt.

## 17. Nächster logischer Schritt

**I002:** Manifest- und Evidence-Vertrag vervollständigen, kryptografische Datei-Hashes und einen Remote-Tree-Receipt einführen und danach das Start-Orchestrator-Grundgerüst beginnen.

## 18. Weiterführende Verbesserung

Den Repository-Vollständigkeitsvertrag um eine zweite unabhängige Remote-Tree-Prüfung erweitern, die Commit, Tree, Pfade, Dateimodi und Hashes gegen das lokale Soll-Inventar verifiziert. Dadurch prüft nicht derselbe Mechanismus ausschließlich seine eigene Ausgabe.

## I002 — Manifest + Evidence Hardening
- Version: `0.2.0-dev.1`
- vollständiges SHA-256-Dateiinventar
- Source-, Build-, Release- und Evidence-Manifeste
- Remote-Tree-Prüfung mit Pfad, Blob-SHA, Modus und Größe
- zentraler Fehlerkatalog mit klaren Nutzerhinweisen
- vollständige Repositoryprüfung in jeder Iteration

### Nächster logischer Schritt
I003: Klick-&-Start-Orchestrator als testbare Zustandsmaschine mit Vorprüfung, Aktion, Nachprüfung, Recovery und detailliertem Nutzerfeedback.

## I003 — Klick-&-Start-Orchestrator
- Version: `0.3.0-dev.1`
- deterministische Zustände: INIT, CHECKING, READY, DEGRADED, RECOVERY_REQUIRED, BLOCKED
- jeder vollständige Schritt: PRECHECK → ACTION → POSTCHECK
- reale Workspace-Schreibprobe und SQLite-Integritätsprüfung
- sichere Konfigurationsquarantäne statt stiller Überschreibung
- detailliertes Nutzerfeedback mit Fehler-ID und automatischer Maßnahme
- Fault-Injection ausschließlich in temporären Test-Workspaces

### Nächster logischer Schritt
I004: Kalender-Domainkern und SQLite-Persistenzschicht zunächst GUI-unabhängig entwickeln und qualifizieren.

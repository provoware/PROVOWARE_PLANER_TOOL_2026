# PROVOWARE PLANER TOOL 2026

Privates, portables und vollständig offline ausgerichtetes Ein-Nutzer-Planungswerkzeug für Linux.

## 1. Projektstatus

- **Phase:** Neuaufbau / Foundation
- **Zielplattform:** Linux, insbesondere Ubuntu-/Kubuntu-Derivate
- **Betrieb:** lokal, offline-first, ohne Cloud-Zwang
- **Architekturziel:** maximal wartbarer modularer Monolith
- **Bedienprinzip:** Klick & Start mit automatischer Vor- und Nachvalidierung
- **Technische Nutzerabnahme:** soll nicht erforderlich sein
- **Releaseziel:** reproduzierbares Linux-Paket plus qualifiziertes ZIP

## 2. Ziel

PROVOWARE PLANER soll Kalender, Aufgabenplanung, Dashboard, Diagnose und spätere Zusatzmodule in einer einheitlichen, modernen und leicht verständlichen Oberfläche verbinden. Die Nutzerdaten bleiben lokal. Beim ersten Start wird ein Arbeitsordner ausgewählt, real auf Lese- und Schreibfähigkeit geprüft und über eine eindeutige Workspace-ID dauerhaft zugeordnet.

## 3. Kernmodule

### Kalender
- Jahres-, Monats-, Wochen- und Tagesansicht
- Termine und ganztägige Einträge
- fünf frei benennbare Farbmarkierungen
- Markierungen zusätzlich mit Text oder Symbol, damit Farbe nie alleinige Information ist
- Vorbereitung für Suche, Wiederholungen und offene Austauschformate

### Todo
- Aufgaben, Status, Priorität und Fälligkeit
- Unteraufgaben und Fortschritt
- Filter, Suche und Favoriten
- definierte Verknüpfung mit Kalenderdaten
- keine versteckten Datenlöschungen bei gelösten Verknüpfungen

### Dashboard
- heutige Informationen
- nächste Termine
- fällige und überfällige Aufgaben
- Sicherungsstatus
- Modul- und Systemstatus
- Schnellaktionen

### Diagnose und Logging
Probleme sollen eindeutig beschreiben:
- Was ist passiert?
- Wann?
- Wo?
- Wie?
- Wodurch vermutlich?
- Welche Auswirkung besteht?
- Was kann automatisch getan werden?
- Was kann der Nutzer tun?

Technische Ereignisse erhalten stabile IDs und maschinenlesbare Daten. Die Oberfläche zeigt dazu einfache deutsche Erklärungen.

## 4. Oberfläche

Geplanter Grundaufbau:
1. Menüleiste
2. kompakte Schnellstart- und Favoritenleiste mit kleinen Kacheln
3. modulare Tabs
4. aktiver Arbeitsbereich
5. Statusbereich mit Sicherung, Diagnose und Version

Die Bereiche sollen sich automatisch an Fenstergröße und Schriftskalierung anpassen. Hauptlayouts verwenden keine starre absolute Positionierung.

## 5. Globale UI-Standards

Gestaltungswerte werden zentral geführt. Einzelne Module dürfen Abstände, Schriftgrößen oder Statusfarben nicht frei neu erfinden.

Geplant sind globale Design-Tokens für:
- Abstände auf Basis eines 4-Pixel-Rasters
- Typografie-Rollen
- flexible Schriftskalierung
- Farben und Kontraste
- Fokusdarstellung
- Karten, Buttons und Statusanzeigen
- Barrierefreiheitsregeln

Vorgesehene Schriftskalierung: 90 %, 100 %, 110 %, 125 %, 150 %, 175 % und 200 %.

## 6. Ampelsystem

Die Ampel ist nur eine unterstützende Statusdarstellung. Farbe wird immer durch Text und Symbol ergänzt.

- **GRÜN – BEREIT:** definierte Prüfungen bestanden
- **GELB – EINGESCHRÄNKT:** Programm nutzbar, aber ein Hinweis oder nichtkritisches Problem besteht
- **ROT – BLOCKIERT:** sichere Weiterarbeit aktuell nicht zulässig

Der Gesamtstatus wird zentral aus den Zuständen von Arbeitsordner, Datenbank, Modulen, Sicherung und Diagnose abgeleitet.

## 7. Klick-&-Start-Prinzip

Der Start-Orchestrator soll automatisch und transparent prüfen:
1. Betriebssystem und Architektur
2. Runtime und Programmdateien
3. Manifeste
4. Konfiguration
5. Arbeitsordner und Workspace-ID
6. reale Lese-/Schreibfähigkeit
7. Datenbank und Schema
8. Sicherungs- und Wiederherstellungszustand
9. aktivierte Module
10. Logging und internes Ereignissystem
11. GUI
12. Nachstartprüfung

Es werden nur tatsächlich notwendige lokale Komponenten gestartet. Unnötige Server, Hintergrunddienste oder Cloud-Abhängigkeiten sind nicht vorgesehen.

## 8. Datenprinzip

Strikte Trennung von:
- Programm
- Nutzerdaten
- Laufzeitdaten
- Konfiguration
- Sicherungen
- Logs

Für die lokale Datenhaltung ist SQLite vorgesehen. Schreibvorgänge sollen transaktional erfolgen. Schemaänderungen erhalten Vorprüfung, Sicherung und Nachvalidierung.

## 9. Globale Standards

Das Projekt soll maschinenlesbare Standards führen für:
- Projekt- und Architekturvertrag
- Benennungen
- UI und Barrierefreiheit
- Datenformate
- Startlogik
- Logging und Fehlercodes
- Tests und Qualitäts-Gates
- Manifeste und Nachweise
- Versionierung und Releases
- Dokumentationsstruktur

Eine niedrigere Ebene darf einen globalen Standard nur durch eine dokumentierte Ausnahme überschreiben.

## 10. Manifest- und Nachweiskette

Geplant ist eine nachvollziehbare Kette:

`SOURCE_MANIFEST.json` → `BUILD_MANIFEST.json` → `RELEASE_MANIFEST.json` → `EVIDENCE_MANIFEST.json`

Ein `MANIFEST_INDEX.json` dient als zentraler Einstieg. Kritische Dateien und Berichte werden über SHA-256, Version, Commit und Lineage nachvollziehbar verbunden.

## 11. Entwicklungsprinzip

Entwicklung erfolgt in kleinen, klar begrenzten Schritten:

Anforderung → Risikoanalyse → Testdesign → Baseline → Minimalpatch → Zieltests → Regression → Wartbarkeitsprüfung → Nachweis → Commit → Remote-Prüfung → Checkpoint

Wichtige Regeln:
- keine technische Nutzerabnahme als Pflicht
- keine Freigabe bei nicht bestandener Pflichtprüfung
- keine unkontrollierten Abhängigkeitsänderungen
- keine Vermischung großer Funktionsentwicklung mit unnötigem Refactoring
- relevante Fehlerbehebungen erhalten dauerhafte Regressionstests
- Standards, Manifeste und Statusdaten werden automatisch auf Widersprüche geprüft

## 12. Automatische Qualitätssicherung

Geplant sind automatische Prüfungen für:
- Syntax und statische Analyse
- Typprüfung
- Architekturgrenzen
- Unit-, Contract- und Property-Tests
- Datenbank und Migrationen
- Module und Integrationen
- GUI und Tastaturbedienung
- Barrierefreiheit
- Wiederherstellung und Persistenz
- Performance und Ressourcen
- Portabilität
- Packaging
- reproduzierbare Builds
- Prüfung des tatsächlich erzeugten Releasepakets

Absolute Fehlerfreiheit wird nicht behauptet. Freigaben basieren auf nachweisbaren Prüf-Gates und einer transparenten technischen Konfidenzbewertung.

## 13. Technische Zielrichtung

Aktuell vorgesehen:
- Python 3.12+
- PySide6 / Qt 6
- SQLite
- pytest
- Ruff
- Pyright oder MyPy
- Bandit
- Dependency-Prüfung
- GitHub Actions

Die endgültige Auswahl wird im Foundation-Vertrag fixiert und danach versionsgebunden geführt.

## 14. Dokumentation

Vorgesehene Kernunterlagen:
- `README.md`
- `TODO.md`
- `CHANGELOG.md`
- `ARCHITEKTUR.md`
- `DATENMODELL.md`
- `MODULSTANDARD.md`
- `TESTKONZEPT.md`
- `RELEASEVERTRAG.md`
- `LAIENANLEITUNG.md`
- `PROJEKTSTATUS.json`
- `VERSION.json`

README, Statusdateien und Manifeste sollen später automatisch auf Konsistenz geprüft werden.

## 15. Entwicklungsphasen

1. I000 Produkt- und Foundation-Vertrag
2. I001 globale Standards
3. I002 Manifest- und Nachweisstandard
4. I003 Repositorystruktur
5. I004 Entwicklungsautopilot
6. I005 Testfundament
7. I006 Start-Orchestrator
8. I007 Workspace und Rechte
9. I008 Datenbank, Migration und Wiederherstellung
10. I009 Modulsystem
11. I010 Designsystem
12. I011 GUI-Shell
13. danach Kalender, Todo, Kopplung, Dashboard und Härtung

## 16. Aktueller Checkpoint

**C000 – REPOSITORY RESET / NEUAUFBAU**

Der bisherige Arbeitsbaum wurde für den neuen Projektansatz ersetzt. `README.md` und `TODO.md` bilden die neue kanonische Ausgangsbasis. Die weitere Entwicklung beginnt beim Foundation-Vertrag und nicht bei vorzeitigem Fachcode.

## 17. Nächster logischer Schritt

**I000/I001:** `PROJECT_CONTRACT.json` und die globalen Standards vollständig definieren, bevor die erste Fachfunktion implementiert wird.

## 18. Weiterführende Verbesserung

Direkt danach soll ein unabhängiger Standard- und Manifest-Validator entstehen. Er prüft die zentralen Verträge getrennt vom späteren Erzeuger und verhindert, dass sich ein Generator ausschließlich selbst bestätigt.

# PROVOWARE PLANER — Nutzeranleitung

Dieses Paket enthält nur die Dateien, die zum Ausführen des Planers benötigt werden. Entwicklerwerkzeuge, Tests, historische Entwicklungsdokumentation, CI-Dateien und Evidence-Nachweise sind absichtlich nicht Bestandteil des normalen Nutzerpakets.

## Start

Voraussetzungen:
- Linux, bevorzugt Ubuntu-/Kubuntu-Derivat
- Python 3.12 oder neuer
- die in `requirements-gui.lock` festgelegte PySide6-/Qt-Laufzeit

Beispiel:

```bash
python tools/start_gui.py --workspace "$HOME/PROVOWARE-PLANER-DATEN"
```

Der angegebene Arbeitsbereich enthält Ihre persönlichen Daten. Er ist **nicht** Teil des Programmordners und sollte getrennt gesichert werden.

## Was gehört wohin?

- **Programmordner:** Programmdateien aus diesem Paket.
- **Arbeitsbereich:** persönliche Kalender-, Todo- und Konfigurationsdaten.
- **Sicherungen:** liegen im Arbeitsbereich beziehungsweise dessen Sicherungsordner und werden nicht in Programm-/Quellcodepakete aufgenommen.
- **Entwicklerunterlagen:** werden nur über das ausdrücklich gewählte Entwicklerprofil verteilt.
- **Evidence/Nachweise:** werden nur als separates Evidence-Paket verteilt.

## Integritätsprüfung

`PAKET_INVENTAR.json` bindet die Dateien dieses Pakets mit SHA-256. Der Startpfad verwendet dieses Paketinventar automatisch, wenn das Programm aus einem Nutzerpaket gestartet wird.

## Wichtig

Kopieren Sie zum Weitergeben des Programms nicht den kompletten Entwicklungs-Repositoryordner. Verwenden Sie das erzeugte **NUTZER**-Transportpaket. Nutzdaten und Sicherungen gehören niemals in ein normales Programm- oder Entwicklerpaket.

# I005 — Kalender-GUI + ViewModel-Schicht

## Ziel
Die erste sichtbare Kalenderoberfläche baut ausschließlich auf der in I004 qualifizierten Service-API auf.

## Architektur
`CalendarService → CalendarQueryService → CalendarViewModel → PySide6/Qt`.

Die GUI enthält kein SQL, keine Migrationen, kein Backup/Restore und keine direkte SQLite-Abhängigkeit.

## Ansichten
- Tag: Terminliste des gewählten Tages.
- Woche: sieben echte Tagesbereiche Montag bis Sonntag.
- Monat: echtes 7-Spalten-Kalenderraster mit bis zu sechs Wochen.
- Jahr: zwölf Monatsfelder mit Termin- und Markierungszusammenfassung.

Alle Ansichten verwenden dieselben Query- und Darstellungsmodelle.

## Bedienung
Heute, Zurück, Vor, Datumsauswahl und Ansichtsumschaltung sind direkt erreichbar. `Ctrl+N`, `Ctrl+E`, `Ctrl+T`, `Ctrl+Links`, `Ctrl+Rechts` sowie `Alt+1..4` stehen als Tastaturpfade bereit.

## Markierungen
Alle fünf Markierungen sind gleichzeitig sichtbar. Name, Kürzel, Hexfarbe und Symbol sind editierbar. Farbe ist nur ergänzend; Symbol, Kürzel und Klartext bleiben sichtbar. Der komplette Markierungssatz wird transaktional gespeichert.

## Design
Abstände und Schriftskalierung werden aus `standards/UI_STANDARD.json` gelesen. Unterstützte Skalierungen: 90, 100, 110, 125, 150, 175 und 200 Prozent.

## Barrierefreiheit
Interaktive Kernelemente besitzen Accessible Names. Status wird als Symbol + Klartext dargestellt. Die Oberfläche verwendet die Systempalette und setzt Markierungsfarben nur ergänzend ein, damit High-Contrast-Themes funktionsfähig bleiben.

## GUI-Laufzeit
`contracts/GUI_RUNTIME_CONTRACT.json` bindet PySide6 6.9.1 sowie die notwendigen nativen Linux-Bibliotheken. Der I003-Start-Orchestrator läuft vor jedem Qt-Import. Fehlt die GUI-Laufzeit, wird mit `START-GUI-RUNTIME-001` verständlich blockiert statt roh abzustürzen. Netzwerkbasierte stille Nachinstallation ist untersagt.

## Automatische Qualifikation
Offscreen-Qt wird für 1280×720, 1366×768, 1600×900 und 1920×1080 sowie 90/100/110/125/150/175/200 Prozent geprüft. Zusätzlich werden ViewModel, Marker-Persistenz, Neustartpersistenz, vier Ansichten, Tastaturpfade und historische Gates I002→I003→I004→I005 validiert.

## Startintegration
`tools/start_gui.py` führt vor Qt den qualifizierten I003-Start-Orchestrator und danach den nativen GUI-Runtime-Check aus. Nur `READY` oder kontrolliert `DEGRADED` plus vollständige GUI-Runtime dürfen zur Oberfläche weitergehen.

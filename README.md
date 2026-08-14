# PROVOWARE PLANER TOOL 2026

Privates, portables und vollständig offline ausgerichtetes Ein-Nutzer-Planungswerkzeug für Linux. Das Projekt wird als maximal wartbarer modularer Monolith entwickelt und soll ohne technische Nutzerabnahme autonom qualifiziert werden.

## 1. Projektstatus

- **Kanonische Version:** siehe `VERSION.json`
- **Kanonischer Entwicklungsstand:** siehe `PROJEKTSTATUS.json`
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
Aufgaben mit Status, Priorität, Fälligkeit, Unteraufgaben, Fortschritt und expliziter Kalenderkopplung. Todo und Termin bleiben eigenständige Datenobjekte; Kopplungen besitzen eine eigene Identität und löschen ihre Endpunkte niemals kaskadierend.

### Dashboard
Heute, nächste Termine, fällige und überfällige Aufgaben, Sicherungszustand, Modulstatus, Systemstatus und Schnellaktionen.

### Diagnose und Logging
Jedes relevante Problem soll eindeutig beantworten: Was? Wann? Wo? Wie? Wodurch? Welche Auswirkung? Was kann automatisch getan werden? Was kann der Nutzer tun? Technische Ereignisse erhalten stabile IDs und maschinenlesbare Daten.

## 4. Oberfläche und globale Gestaltung

Alle Module verwenden zentrale Designregeln. Einzelne Module dürfen Abstände, Typografie, Fokusdarstellung oder Statusfarben nicht frei neu erfinden.

Das globale Abstandssystem basiert auf einem 4-Pixel-Raster: 4, 8, 12, 16, 24, 32 und 48 Pixel. Schrift wird über semantische Rollen geführt und global skalierbar gehalten. Freigegebene Stufen sind 90 %, 100 %, 110 %, 125 %, 150 %, 175 % und 200 %.

## 5. Ampelsystem

- 🟢 **GRÜN – BEREIT:** alle für den Zustand erforderlichen Prüfungen bestanden
- 🟡 **GELB – EINGESCHRÄNKT:** nutzbar, aber mindestens ein nichtkritischer Hinweis besteht
- 🔴 **ROT – BLOCKIERT:** sichere Weiterarbeit oder Freigabe nicht zulässig

Farbe wird nie ohne Symbol und Text verwendet.

## 6. Klick-&-Start

Der Start-Orchestrator prüft Betriebssystem, Runtime, Programmdateien, Manifeste, Konfiguration, Workspace, Datenbank, Schema, Recovery, Module und GUI. Jede relevante Aktion folgt `PRECHECK → AKTION → POSTCHECK`.

## 7. Daten und Sicherheit

Programm, Nutzerdaten, Laufzeitdaten, Konfiguration, Sicherungen und Logs werden strikt getrennt. SQLite arbeitet mit Foreign Keys, WAL, Transaktionen, hashgebundenen Migrationen und Vor-Migrations-Sicherungen. Fachliches Löschen erfolgt als Soft Delete.

## 8. Repository- und Evidence-Vertrag

`REPOSITORY_MANIFEST.json` ist das Soll-Inventar. Source-, Build-, Release- und Evidence-Manifeste sowie ein SHA-256-Inventar und Remote-Tree-Receipt bilden die Nachweiskette. Jede Iteration wird lokal logisch und remote unabhängig geprüft.

## 9. Entwicklungsautopilot

`tools/autopilot/autopilot.py qualifizieren` führt globale Standards und alle historischen Pflichtgates bis zur aktuellen Iteration aus. `FAIL` und `NOT_RUN` blockieren Freigaben.

## I002 — Manifest + Evidence Hardening
- Version `0.2.0-dev.1`
- SHA-256-Inventar, Manifestkette, Remote-Tree-Receipt und zweite Remote-Prüfung.

## I003 — Klick-&-Start-Orchestrator
- Version `0.3.0-dev.1`
- deterministische Startzustände, Workspace-Prüfung, Recovery und Fault-Injection.

## I004 — Kalender-Domainkern + SQLite-Persistenz
- Version `0.4.0-dev.1`
- Kalender-Domainmodell, fünf Marker, Migrationen, Optimistic Locking, Soft Delete, Backup/Restore.

## I005 — Kalender-GUI + ViewModel
- Version `0.5.0-dev.1`
- Tag/Woche/Monat/Jahr, `CalendarService → CalendarQueryService → CalendarViewModel → Qt`.
- sieben Schriftstufen, vier Fenstergrößen, 112 Offscreen-Konfigurationen, Accessible Names und High Contrast.

## I006 — Todo-Domainkern + Kalender↔Todo-Kopplungsvertrag
- Version: `0.6.0-dev.1`
- Status, Priorität, Fortschritt, Start, Fälligkeit und Unteraufgaben als GUI-unabhängiges Domainmodell.
- Migration `0002_todo_domain_links.sql` mit Foreign Keys, Constraints und Optimistic Locking.
- Todo und Termin bleiben eigenständige Entitäten; fachliches Löschen ist Soft Delete.
- Kopplungen besitzen eigene `link_id`, Version, Richtung und Versions-Snapshots.
- Konfliktstatus: sauber, Todo geändert, Termin geändert, beide geändert oder getrennt.
- `ON DELETE CASCADE` ist für Todo↔Termin verboten; Link-Endpunkte verwenden `RESTRICT`.
- Entkoppeln löscht weder Todo noch Termin.
- automatische Inhalts-Synchronisation ist in I006 ausdrücklich deaktiviert.
- kontrollierte Transaktionsabbrüche plus echter Prozessabbruch vor Commit werden automatisch geprüft.
- historische Gate-Kette: I002 → I003 → I004 → I005 → I006.

### Nächster logischer Schritt
I007: Todo-GUI + Todo-ViewModel ausschließlich auf den qualifizierten I006-Services aufbauen. Konflikte zunächst sichtbar machen; automatische Konfliktauflösung erst nach eigenem Vertrag freigeben.

# TODO — PROVOWARE PLANER TOOL 2026

## C000 — Neuaufbau
- [x] alten Arbeitsbaum ablösen
- [x] neue README anlegen
- [x] neue TODO-Roadmap anlegen
- [ ] Repository-Sichtbarkeit auf privat stellen

## I000 — Foundation
- [x] `PROJECT_CONTRACT.json`
- [x] Produkt- und Architekturvertrag
- [x] Definition of Ready / Done
- [x] autonomer Freigabe- und Repository-Prüfvertrag

## I001 — Globale Standards
- [x] Standardindex
- [x] Namensstandard
- [x] UI- und Barrierefreiheitsstandard
- [x] Daten-, Logging-, Test-, Start-, Manifest- und Releasestandard
- [x] Qualitäts- und Dokumentationsstandard
- [x] einheitliche Abstände und Design-Tokens
- [x] flexible Schriftgrößen
- [x] Ampelstatus mit Farbe, Symbol und Text
- [x] `VERSION.json` und `PROJEKTSTATUS.json`

## Vorgezogene Foundation-Härtung
- [x] vollständiges `REPOSITORY_MANIFEST.json`
- [x] unabhängigen `standard_validator` anlegen
- [x] Validator-Unit-Tests anlegen
- [x] Autopilot-Grundstruktur anlegen
- [x] GitHub-Actions-Foundation-Qualifikation anlegen
- [x] README/TODO/Status-Konsistenz automatisch prüfen
- [x] vollständige Repository-Dateiliste in jeder Iteration prüfen

## I002 — Manifest und Evidence
- [ ] Source-/Build-/Release-/Evidence-Manifest-Schemata
- [ ] SHA-256-Inventar für Release-relevante Dateien
- [ ] Remote-Tree-Receipt mit Commit, Tree, Pfaden, Modi und Hashes
- [ ] unabhängigen Manifest-Validator ergänzen
- [ ] maschinenlesbare Qualification Reports

## I003 — Start und Daten
- [ ] Klick-&-Start-Orchestrator
- [ ] Arbeitsordner mit persistenter Workspace-ID
- [ ] reale Rechteprüfung mit Schreib-/Lese-/Umbenenn-/Löschtest
- [ ] Vor-/Nachvalidierung
- [ ] SQLite, Migration, Backup und Wiederherstellung

## I004 — Modulsystem und GUI
- [ ] Modulvertrag und Ereignissystem
- [ ] Design-Tokens in Qt-Komponenten umsetzen
- [ ] Menüleiste
- [ ] Schnellstart-/Favoritenleiste
- [ ] Tabs
- [ ] Statusbereich mit Ampelunterstützung
- [ ] responsive und skalierbare Oberfläche

## I005 — Fachmodule
- [ ] Kalender: Jahr / Monat / Woche / Tag
- [ ] fünf editierbare Markierungen
- [ ] Todo mit Priorität, Status, Fälligkeit und Unteraufgaben
- [ ] Kalender-Todo-Kopplung
- [ ] Dashboard
- [ ] Diagnose und Logging

## I006 — Qualifizierung und Release
- [ ] automatische Modul-, Integrations- und GUI-Prüfungen
- [ ] Barrierefreiheit
- [ ] Recovery und Persistenz
- [ ] Performance und Portabilität
- [ ] reproduzierbares Linux-Paket und ZIP
- [ ] GitHub-Qualifizierung
- [ ] RC1
- [ ] Stable 1.0

## Permanente Regeln
- [x] keine technische Nutzerabnahme als Pflicht
- [x] kein Release bei nicht bestandenen oder nicht ausgeführten Pflichtprüfungen
- [x] kleine, klar begrenzte Patches
- [x] Status, Fortschritt, nächster Schritt und Verbesserungsempfehlung pflegen
- [x] kompletten Repository-Inhalt nach jeder Iteration gegen Soll-Inventar prüfen
- [x] lokale und Remote-Prüfung voneinander trennen

## Nächster logischer Schritt
I002: Manifest-/Evidence-Kette, kryptografisches Repository-Inventar und Remote-Tree-Receipt ergänzen; danach I003 Start-Orchestrator beginnen.

## I002 — Manifest + Evidence Hardening
- [x] Manifest-Builder
- [x] SHA-256-Inventar
- [x] Remote-Tree-Validator
- [x] Fehlerstandard und Fehlerkatalog
- [x] vollständige Repository-Dateiliste
- [x] Remote-Qualifikation und Receipt-Kette

## I003 — Nächster logischer Schritt
- [ ] Klick-&-Start-Orchestrator als Zustandsmaschine
- [ ] Fault-Injection und Recovery
- [ ] detailliertes laienverständliches Live-Feedback

## I003 — Klick-&-Start-Orchestrator
- [x] deterministische Startzustände
- [x] PRECHECK → ACTION → POSTCHECK
- [x] System-, Runtime- und Manifestprüfung
- [x] persistenter Workspace mit realer Dateioperation
- [x] Konfigurations-Recovery mit Quarantäne
- [x] SQLite quick_check und Transaktionsprobe
- [x] Module, Logging, Ereignisbus und GUI-Übergabe
- [x] Nachstartprüfung und Ready-Marker
- [x] Pflicht-Fault-Matrix
- [x] automatischer zweiter Remote-Verifikationslauf

## I004 — Nächster logischer Schritt
- [ ] Kalender-Domainmodell
- [ ] SQLite-Schema und Migrationen
- [ ] Service-API ohne GUI-Abhängigkeit
- [ ] erst danach erste Kalenderoberfläche

## I004 — Kalender-Domainkern + SQLite-Persistenz
- [x] Domainmodell und Invarianten
- [x] SQLite-Schema und fünf Markierungstypen
- [x] UTC-Persistenz mit erhaltener IANA-Zeitzone
- [x] hashgebundene Migrationen
- [x] automatisches Vor-Migrations-Backup
- [x] Repository und Service-API
- [x] Optimistic Locking und Soft Delete
- [x] atomisches Backup und Restore
- [x] Crash-/Rollback- und Fault-Injection-Tests
- [x] historische Gate-Kette I002 → I003 → I004

## I005 — Nächster logischer Schritt
- [ ] Kalender-GUI ausschließlich über CalendarService
- [ ] Tag-, Woche-, Monat- und Jahransicht
- [ ] fünf Markierungen sichtbar und editierbar
- [ ] Design-Tokens, flexible Schrift und Ampelstatus verwenden
- [ ] automatisierte GUI- und Barrierefreiheitsmatrix

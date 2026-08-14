# I012 — Dashboard + Diagnose-/Recovery-Zentrale

## Ziel
I012 bündelt vorhandene Zustands- und Integritätsnachweise in einer laienlesbaren, ausschließlich lesenden Oberfläche. Das Dashboard führt keine Reparatur aus und erzeugt keinen zweiten Daten- oder Recovery-Pfad.

## Bereiche
1. **Startzustand** — liest den zuletzt gespeicherten Startbericht.
2. **Datenbank** — öffnet SQLite mit `mode=ro` und `PRAGMA query_only=ON`, führt `quick_check` aus und liest die Schema-Version.
3. **Synchronisationsjournal** — verwendet den qualifizierten I011-Journalservice und zeigt verifizierte, Legacy- und manipulierte Nachweise.
4. **Sicherungen** — prüft vorhandene SQLite-Sicherungen ausschließlich lesend auf `quick_check`, Manifest und SHA-256.
5. **Recovery-Pläne** — erzeugt nur neue read-only Recovery-Vorschauen über I011 und zählt aktuell ausführbare beziehungsweise sicher blockierte Varianten.

## Ampellogik
- `● BEREIT`: Nachweis vorhanden und Prüfung erfolgreich.
- `▲ EINGESCHRÄNKT`: kein optionaler Nachweis vorhanden oder eine sichere Schutzblockade ist aktiv.
- `● BLOCKIERT`: Integritäts-, Manipulations- oder Lesefehler.

Farbe ist nie das einzige Signal; Symbol und Text sind verpflichtend.

## Sicherheitsgrenze
Die Diagnosezentrale besitzt keine Funktionen für SQL-Write, Migration, Restore, Sync-Commit, Recovery-Commit oder freie Datenreparatur. Bestehende Fachmodule bleiben die einzigen autoritativen Aktionspfade.

## Startbericht
`tools/start_gui.py` speichert den vorhandenen StartOrchestrator-Bericht zusätzlich standardmäßig als `LETZTER_STARTBERICHT.json` im Arbeitsbereich. Dieser Schreibvorgang gehört zum bestehenden Start-/Loggingpfad; das Dashboard selbst liest die Datei nur.

## Qualifikation
I012 muss die historische Kette I002→I012, vollständige Regressionstests, eine 35er Qt-Offscreen-Matrix, Datenbank-Nichtmutation, Backup-Manipulationserkennung, Startberichtsauswertung, Remote-Tree-Prüfung und einen exakten read-only Evidence-Zweitpass bestehen.

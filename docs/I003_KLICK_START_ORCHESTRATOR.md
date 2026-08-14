# I003 — Klick-&-Start-Orchestrator

## Ziel

I003 führt eine deterministische Startlaufzeit ein. Noch keine Kalender-GUI. Der Start wird erst freigegeben, wenn System, Laufzeit, Programmintegrität, Arbeitsordner, Konfiguration, SQLite, Recovery, Module, Logging, Ereignisbus, GUI-Übergabe und Nachstartprüfung kontrolliert wurden.

## Zustände

`INIT → CHECKING → READY`

Aus `CHECKING` sind zusätzlich möglich:

- `DEGRADED`: Start möglich, nichtkritische Funktion eingeschränkt.
- `RECOVERY_REQUIRED`: Start angehalten, sichere Wiederherstellung erforderlich.
- `BLOCKED`: Start aus Integritäts- oder Sicherheitsgründen verboten.

Sicher reparierbare Fehler dürfen vorübergehend `RECOVERY_REQUIRED → CHECKING` durchlaufen und erst nach erfolgreichem Postcheck in `READY` enden.

## Verbindliche Schrittfolge

Jeder vollständig ausgeführte Startschritt folgt:

1. `PRECHECK` — Voraussetzung prüfen, noch keine riskante Aktion.
2. `ACTION` — nur notwendige und zulässige Aktion ausführen.
3. `POSTCHECK` — Ergebnis unabhängig nachprüfen.

## Reale Prüfungen

- Linux und Python 3.12+
- benötigte Python-Standardmodule
- SHA-256-Dateiinventar
- mindestens 64 MiB freier Speicher vor Schreibprobe
- reale Lese-/Schreib-/Umbenenn-/Löschprobe im Workspace
- JSON-Konfiguration und sichere Standardwiederherstellung
- SQLite `quick_check` und transaktionale Probe
- Recovery-Auswertung
- interne Pflichtmodule
- Logdatei schreiben und rücklesen
- Ereignis-Rundlauf
- vollständiger GUI-Übergabekontext
- abschließender Ready-Marker

## Fehlerbehandlung

Jeder Befund enthält mindestens Phase, Status, Fehlercode, verständlichen Nutzertext, technische Details und automatische Maßnahme. Kritische Integritätsfehler werden nicht still repariert.

Beschädigte Konfigurationen dürfen nur reversibel behandelt werden: Originaldatei in Quarantäne umbenennen, sichere Standardwerte schreiben, erneut validieren. Eine beschädigte SQLite-Nutzerdatenbank wird nicht überschrieben. Eine Datenbanksperre wird nicht gewaltsam entfernt. Rechte werden nicht automatisch erhöht.

## Fault-Injection

Pflichtszenarien:

- fehlende Rechte
- verschwundener Workspace
- beschädigte Konfiguration
- manipuliertes Manifest
- gesperrte SQLite-Datenbank
- beschädigte SQLite-Datenbank
- simulierter Speichermangel

Zusätzlich wird ein optional fehlendes Modul für den Zustand `DEGRADED` geprüft.

Fault-Injection ist nur mit expliziter Freigabe und ausschließlich in temporären Test-Workspaces erlaubt. Reale Nutzerdaten dürfen niemals Ziel einer Fault-Injection sein.

## Bedienung

Normaler Teststart:

```bash
python tools/start_orchestrator.py --workspace /tmp/provoware-i003-test
```

Maschinenlesbarer Bericht:

```bash
python tools/start_orchestrator.py --workspace /tmp/provoware-i003-test --json-report /tmp/i003-runtime.json
```

Fault-Injection ist ausschließlich für Tests vorgesehen:

```bash
python tools/start_orchestrator.py \
  --workspace /tmp/provoware-i003-fault \
  --fault config_corrupt \
  --allow-fault-injection
```

## Abnahmekriterium

I003 ist erst abgeschlossen, wenn Healthy Path, alle Pflicht-Faults, Unit-/Regressionstests, Standardvalidator, I002-Evidence-Vertrag, Manifestkette, Remote-Tree-Prüfung und ein zweiter unabhängiger Remote-Verifikationslauf auf dem gespeicherten Evidence-Commit PASS melden.

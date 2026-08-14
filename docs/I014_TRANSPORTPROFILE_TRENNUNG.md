# I014 — Transportprofile und Artefakttrennung

## Ziel

Das Entwicklungs-Repository bleibt vollständig auditierbar, wird aber nicht länger mit einem normalen Weitergabe- oder Nutzerpaket gleichgesetzt. Programm, Entwicklerbasis, Evidence und Nutzdaten/Sicherungen erhalten getrennte Verantwortungs- und Transportgrenzen.

## Vier Transportklassen

- `PRODUKTKERN`: ausführbarer Planner, Domain-/Service-/Storage-/UI-Code, Migrationen, Fehlerkataloge, Runtime-Vertrag, Startdateien und gepinnte GUI-Abhängigkeiten.
- `NUTZERDOKU`: kurze Dokumentation, die tatsächlich beim Endnutzer benötigt wird.
- `ENTWICKLUNG`: Tests, Standards, Entwicklerverträge, historische Iterationsdokumentation, Autopilot, Matrizen, CI und Projektsteuerung.
- `EVIDENCE`: Qualifikationsberichte, Remote-Receipts, Repository-/SHA-/Build-/Evidence-Manifeste und Prozessaudits.

Jeder im Repository registrierte Pfad muss genau einer Klasse zugeordnet sein. Mehrdeutige oder nicht klassifizierte Pfade blockieren I014.

## Profile

### NUTZER — Standard

Enthält ausschließlich `PRODUKTKERN + NUTZERDOKU`. Dieses Profil ist der Standard für Weitergabe, lokale Kopie oder spätere Release-Pakete.

Nicht enthalten sind insbesondere `.github/`, `tests/`, `docs/I...`, `standards/`, Entwicklerverträge, `tools/autopilot/`, `ITERATION_PLAN.json`, `PROJECT_CONTRACT.json`, `QUALIFICATION_REPORT.json` und `REMOTE_TREE_RECEIPT.json`.

### PROJEKTKERN

Nur technischer Produktkern, ohne Nutzer- oder Entwicklerdokumentation. Gedacht für interne technische Verarbeitung, nicht als Standardweitergabe.

### ENTWICKLER

Produktkern plus Nutzerdoku und Entwicklungsschicht. Evidence bleibt absichtlich separat, damit Entwicklerpakete nicht mit Qualifikationsnachweisen aufgebläht oder semantisch vermischt werden.

### EVIDENCE

Nur Evidence plus `VERSION.json` und `PROJEKTSTATUS.json` als minimaler Kontext. Kein Produktquellbaum und keine Tests.

## Nutzdaten und Sicherungen

Nutzdaten und Sicherungen sind **kein Code-Transportprofil**. SQLite-Dateien, WAL-/SHM-Dateien, `backups/`, `Sicherungen/`, Restore-Kandidaten, Startberichte, Logs, temporäre Dateien und lokale Workspaces sind in allen Codeprofilen verboten.

Der Paketbuilder wählt seine Quelldateien ausschließlich aus dem registrierten Repository-Soll. Ungetrackte lokale Dateien werden nicht als Paketquelle betrachtet. `.gitignore` bildet eine zusätzliche Schutzschicht.

## Integrität

Jedes Transportpaket erhält:

- `PAKETMANIFEST.json`: Profil, Version, Iteration, Quellcommit/-tree und Sicherheitsdeklaration.
- `PAKET_INVENTAR.json`: SHA-256 und Größe aller Paketdateien außer seiner eigenen Selbstreferenz.

Lauffähige Profile erhalten zusätzlich ein paketbezogenes `SHA256_DATEI_INVENTAR.json`. Dadurch kann der bereits qualifizierte Start-Orchestrator die Integrität des reduzierten Pakets prüfen, ohne das vollständige Entwicklungsinventar zu verlangen.

## Determinismus

ZIP-Einträge werden sortiert, mit festen Zeitstempeln und normalisierten Dateimodi erzeugt. Gleicher Commit plus gleiches Profil muss byte-identische ZIPs liefern.

## Qualifikation

I014 prüft:

1. P0 Static und planbasiertes Repository-Soll.
2. vollständige eindeutige Klassifikation.
3. Profilgrenzen und harte Nutzdaten-/Backup-Ausschlüsse.
4. deterministischen Doppelbau.
5. unabhängige ZIP-/Hashprüfung.
6. frisch entpacktes NUTZER-Paket mit realem Offscreen-Start gegen externen Workspace.
7. vollständige Regression, historische Gates und Exact-SHA-Zweitpass.

## Folgeiteration

Nach I014 folgt I015 — immutable Backup-/RestorePlan. Die dortigen Sicherungsartefakte bleiben in einem eigenen Workspace-/Backup-Vertrag und dürfen niemals in Produkt-, Entwickler- oder Evidence-Codepakete zurückwandern.

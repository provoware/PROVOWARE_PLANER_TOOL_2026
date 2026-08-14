# I015 — Immutable Backup-/RestorePlan

## Ziel
I015 schließt die Lücke zwischen der seit I004 vorhandenen physischen Backup-/Restore-Funktion und einer sicher planbaren Wiederherstellung. Die physische Restore-Implementierung wird **nicht dupliziert**.

## Architektur

`Backup-Kandidat → read-only Qualifikation → RestorePlan → PRECHECK → storage.backup.restore_backup() → POSTCHECK`

### Kandidatenqualifikation
Ein Kandidat ist nur freigegeben, wenn:

1. er als reguläre Datei innerhalb des konfigurierten Backup-Bereichs liegt,
2. das zugehörige Manifest vorhanden und gültig ist,
3. Manifest-SHA, Datenbank-SHA und Größe konsistent sind,
4. SQLite `quick_check` `ok` meldet,
5. die bereits seit I004 kanonische Tabelle `schema_migrations` als höchste angewandte Migration exakt Schema 4 ausweist.

Die Kandidatenprüfung verwendet SQLite `mode=ro`, `immutable=1` und `query_only=ON` und verändert die Sicherung nicht. I015 führt bewusst **kein** paralleles `PRAGMA user_version`-Signal ein; dieselbe Schemaquelle wird verwendet wie in `Database.schema_version()`.

## RestorePlan
`RestorePlan` ist `dataclass(frozen=True, slots=True)` und bindet alle sicherheitsrelevanten Eingaben in einen kanonischen SHA-256-Planhash. Ein verändertes Feld bei unverändertem Plan-Hash wird abgewiesen.

## Zielzustandsbindung und WAL
Nur den Hash von `planer.sqlite3` zu speichern wäre unzureichend: Im WAL-Modus können neue Commits ausschließlich in `planer.sqlite3-wal` liegen. I015 bildet deshalb einen Zustands-Hash über:

- Hauptdatenbank,
- WAL-Datei einschließlich Vorhandensein und Größe.

Die SHM-Datei wird bewusst nicht gebunden, da sie Lock-/Shared-Memory-Zustand enthält und reine Leseraktivität keinen fachlichen Stale-Zustand erzeugen soll.

## Ein physischer Restorekern
`services/restore_service.py` qualifiziert, plant und prüft. Es führt **keinen** eigenen Dateiaustausch aus. Der einzige physische Kern bleibt:

`storage.backup.restore_backup()`

Der historische Kern wurde ausschließlich um zwei Hooks erweitert:

- `precheck`: letzter fail-closed Zustandstest unmittelbar vor Schreiboperationen,
- `postcheck`: Integritäts-/Hashprüfung nach Austausch, aber bevor das Pre-Restore-Abbild gelöscht wird.

Scheitert der Postcheck als Exception, stellt derselbe bestehende Kern das Pre-Restore-Abbild wieder her.

## Fehler- und Crashmodell
Automatisiert geprüft werden:

- Fehler vor physischem Schreibzugriff → Ziel unverändert,
- Prozessabbruch `os._exit(91)` im finalen Precheck → Ziel unverändert,
- Exception nach atomarem Austausch vor erfolgreichem Postcheck → alter Zielzustand wird wiederhergestellt,
- Planmanipulation → blockiert,
- Manifeständerung nach Planerstellung → blockiert,
- Zieländerung nach Planerstellung → blockiert.

Ein harter Prozessabbruch **nach** dem atomaren Austausch kann nicht durch Python-Exception-Rollback abgefangen werden. Da der Austausch erst mit bereits vollständig validiertem Restore-Kandidaten erfolgt, bleibt dabei eine gültige Datenbank bestehen; ein persistentes Restore-Intent/Recovery-Protokoll kann in einer späteren Iteration zusätzlich den unvollständigen Abschlusszustand explizit nachweisbar machen.

## Transportgrenze
`backup_core/`, `RestoreService` und `storage/backup.py` sind Produkt-Runtime. Echte Sicherungsdateien, aktive Datenbanken, `.pre-restore`, `.restore-candidate`, WAL/DB-Dateien und Workspace-Daten bleiben dennoch aus allen Code-Transportprofilen ausgeschlossen.

## Datenbankschema
I015 führt **keine Migration** ein. Schema bleibt Version 4; maßgeblich ist weiterhin die bestehende `schema_migrations`-Historie.

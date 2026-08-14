# I004 — Kalender-Domainkern + SQLite-Persistenz

## Ziel

I004 baut den vollständigen GUI-unabhängigen Daten- und Geschäftslogikkern des Kalenders. Die spätere Oberfläche darf ausschließlich die Service-API verwenden und weder SQL noch Migrationen oder Recovery selbst ausführen.

## Architektur

`CalendarService → CalendarRepository → Database → SQLite`

Parallel dazu arbeiten `MigrationRunner` und `Backup/Restore` als Infrastrukturkomponenten.

## Dateninvarianten

- Termine benötigen einen Titel.
- Titel sind auf 200 Zeichen begrenzt.
- Start und Ende müssen zeitzonenbehaftet sein.
- Ende darf nicht vor Start liegen.
- IANA-Zeitzone wird separat gespeichert.
- Zeitpunkte werden kanonisch in UTC persistiert.
- Es existieren fünf editierbare Markierungstypen.
- Markierungen werden nicht allein durch Farbe semantisch beschrieben.
- Datensätze verwenden Optimistic Locking über `version`.
- Löschen erfolgt zunächst als Soft Delete über `deleted_at`.

## SQLite-Schutz

- `foreign_keys=ON`
- WAL-Journal
- `synchronous=FULL`
- Busy-Timeout
- ausschließlich transaktionale Schreiboperationen
- Rollback bei Ausnahmen
- `PRAGMA quick_check` nach Migration und bei Integritätsprüfung

## Migrationen

Migrationen sind nummerierte SQL-Dateien. Jede angewandte Migration wird mit SHA-256 in `schema_migrations` registriert. Eine nachträgliche Änderung einer bereits angewandten Migration blockiert die weitere Verarbeitung. Vor jeder neuen Migration wird automatisch eine SQLite-Sicherung erzeugt.

## Backup und Restore

Backups werden über die SQLite Backup API erstellt, anschließend mit `quick_check` geprüft und mit SHA-256 dokumentiert. Restore arbeitet ausschließlich über einen temporären Kandidaten. Vor der atomaren Promotion wird die aktive WAL-Datei gecheckpointet; veraltete `-wal`/`-shm`-Dateien werden kontrolliert entfernt. Eine beschädigte oder hashfalsche Sicherung darf die aktive Datenbank nicht ersetzen.

## Fehlerbehandlung

Kalenderfehler werden in `errors/KALENDER_FEHLERKATALOG.json` geführt. Der globale Fehlerstandard erlaubt modulare Kataloge, verlangt aber projektweit eindeutige Codes und vollständige Registrierung aller im produktiven Code verwendeten stabilen Fehler-IDs.

## Automatische Qualifikation

I004 prüft mindestens:

1. Domaininvarianten,
2. Schema und fünf Marker,
3. UTC-Persistenz einschließlich Zeitumstellung,
4. CRUD und Bereichsabfrage,
5. Optimistic Locking,
6. Soft Delete,
7. Transaktionsrollback bei simuliertem Abbruch,
8. hashgebundene Migrationen,
9. Vor-Migrations-Backup,
10. Backup/Restore-Roundtrip,
11. falschen Backup-Hash,
12. beschädigtes Backup,
13. SQLite-Lock,
14. Datenbankintegrität,
15. vollständige I002-/I003-Regression,
16. Repository-/Manifest-/Remote-Tree-Evidence.

## Abgrenzung

I004 enthält bewusst keine Kalender-GUI. Erst der nach I004 qualifizierte Datenkern darf in I005 visualisiert werden.

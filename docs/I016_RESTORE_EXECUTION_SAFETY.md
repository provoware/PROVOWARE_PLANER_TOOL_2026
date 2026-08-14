# I016 — Restore Execution Safety

I016 ergänzt vor der späteren Restore-Oberfläche eine sichere Ausführungsschicht.

Die Reihenfolge lautet: RestorePlan prüfen, exklusive Lease setzen, Planner-Schreibvorgänge blockieren, laufende Schreiber ausschließen, konsistenten Vorzustand sichern, Intent `PREPARED` speichern, `COMMITTING` speichern, bestehenden I015-Restorekern aufrufen, Ergebnis prüfen, `VERIFIED` und anschließend `CLOSED` speichern.

Nach einem unerwarteten Prozessende wird dieser Zustand vor der normalen Datenbank-Startprüfung ausgewertet. Ein eindeutiger neuer Zustand wird verifiziert und abgeschlossen. Ein eindeutiger unveränderter Vorzustand wird ohne Änderung geschlossen. Ein anderer Zustand darf nur anhand des vorher erzeugten und geprüften Sicherheits-Snapshots wiederhergestellt werden. Uneindeutige oder manipulierte Zustände blockieren den Start.

Der physische Restorekern bleibt `storage.backup.restore_backup`. I016 erzeugt keinen zweiten physischen Restorepfad und verändert `storage/backup.py` nicht.

SQLite bleibt bei Schema 4. Laufzeitdateien unter `.provoware_restore` sind keine transportierbaren Programmdateien.

Die Restore-GUI folgt erst nach erfolgreicher Qualifikation dieser Sicherheitsschicht und darf ausschließlich `RestoreExecutionService` benutzen.

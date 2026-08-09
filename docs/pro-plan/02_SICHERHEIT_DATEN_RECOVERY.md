# Teil 2 — Persistenz, Security, Recovery und Accessibility

## 1. Persistenzvertrag
SQLite wird für strukturierten Kernzustand eingesetzt: Termine, Aufgaben, Modulregistry, Settings-Metadaten, Änderungsjournal, Migrationsstand und interne Toolnotiz. Einfache ausdrücklich dateibasierte Sammellisten bleiben TXT. Jedes persistente Format besitzt Schema-/Formatversion, Migrationspfad und Kompatibilitätsgrenze.

## 2. SQLite-Journalmodus
Kein blindes `WAL` als universeller Standard. SQLite dokumentiert, dass WAL gemeinsame Host-/Shared-Memory-Bedingungen benötigt und nicht über Netzwerkdateisysteme funktioniert. Der tatsächliche Default wird erst nach Tests auf lokalen Linux-Dateisystemen und portablen Zielmedien festgelegt.

Prüfmatrix: ext4, xfs/btrfs soweit verfügbar, exFAT-/USB-Fall, NTFS/FUSE-Fall soweit relevant, read-only, fast voller Datenträger, unerwartete Trennung. Netzwerkpfade sind kein unterstützter Standard-Kernspeicher.

## 3. Integritätsprüfungen
- `PRAGMA quick_check` für schnellen Healthcheck.
- `PRAGMA integrity_check` für tiefe Diagnose, Restore und Releasequalifikation.
- `PRAGMA foreign_key_check` zusätzlich bei Fremdschlüsseln.
- Integritätsprüfung meldet strukturiert `PASS/WARN/BLOCKED`.

## 4. Migrationen
Jede Migration besitzt `MIG-ID`, Quell-/Zielschema, Vorbedingungen, Backupanforderung, Up-Schritt, Verify-Schritt, Rollback oder Restoreweg, Kennzeichnung irreversibler Aspekte und Testfixture.

Ablauf: Integrität → Versionscheck → validiertes Backup → Migration → Zielversionscheck → Integrität → Healthcheck → Event/Evidence. Eine unbekannte neuere Schema-Version wird nicht still überschrieben.

## 5. Backup ist ein verifiziertes Produkt
Ein Backup gilt nicht als erfolgreich, weil eine Datei existiert. Pflicht: Quelle/Version identifiziert, konsistenter Snapshot, Manifest, Hash, Ziel lesbar, DB/Dateistruktur validiert und Restorefähigkeit nachgewiesen.

Für eine laufende SQLite-Datenbank wird ein konsistentes Verfahren wie die SQLite Online Backup API oder eine gleichwertige sichere Methode bevorzugt; blindes Kopieren geöffneter DB-Dateien ist kein Standardweg.

Backupklassen: Pre-Migration, Pre-Update, periodisch, manuell, Pre-Restore-Rückfall, kompletter Projektexport und Stable-Baseline.

## 6. Restore
Restoreablauf: Backupidentität → Hash → Manifest → Kompatibilität → Zielzustand prüfen → Rückfallsicherung des aktuellen Zustands → Restore → Integrität → Migration falls vorgesehen → Healthcheck → Evidence. Bei Fehler bleibt die Rückfallsicherung erhalten.

## 7. Recovery Shell
Bei verdächtigem Zustand kein normales Dashboard erzwingen. Zwei Hauptwege:
- A empfohlen: letzte validierte Sicherung wiederherstellen.
- B: Nur-Lesen öffnen und Debugbundle exportieren.

Keine automatische destruktive Reparatur ohne vorherige Rückfallmöglichkeit.

## 8. Never-Crash präzisiert
„Never Crash“ ist ein UX-/Fehlerarchitekturziel, keine physikalische 100-%-Garantie. Erwartbare Fehler werden abgefangen, Zustand bleibt soweit möglich konsistent, Datenrisiko wird benannt, zwei Reparaturwege werden angeboten. Unerwartete Panics/Exceptions bleiben Defekte und werden nicht als Normalzustand kaschiert.

## 9. Fehlerobjekt
Felder: Code, Severity, Domain, Operation, technische Ursache, Nutztext, Datenrisiko, empfohlene Aktion A, Alternative B, Correlation-ID und optional Event-ID. Rohe Stacktraces erscheinen nicht als Hauptmeldung.

## 10. Rust-Fehlerdisziplin
`unwrap`/`expect` werden in nutzer-, daten- und dateisystemkritischen Pfaden restriktiv behandelt. Panic ist kein regulärer Rückgabekanal. Tauri-Commandfehler werden in typisierte Domänenfehler übersetzt. Frontend-Rejections und globale Fehler werden ebenfalls strukturiert erfasst.

## 11. Logging/Observability
Ein Eventmodell erzeugt JSONL und menschenlesbare TXT-/GUI-Sicht. Mindestfelder: Timestamp, Event-ID, Sequence, Session-ID, Correlation-ID, Severity, Domain, Event-Type, Operation, Result, Duration, Safe Context, Error Code, App-/Schema-Version.

Keine Secrets oder unnötigen privaten Inhalte. Steuerzeichen normalisieren, Pfade maskierbar, Rotation und Größenlimit. `ENOSPC` und read-only Logziel werden getestet; Logger-Ausfall darf Kernoperationen nicht unkontrolliert reißen.

## 12. Debugbundle
Enthält: App-/Buildversion, OS, Projektrootstatus, Speicher-/Dateisystemstatus, DB-/Migrationsstatus, Pluginstatus, relevante Fehlerkette, Reparaturversuche, Prüfsummen und Datenschutzfilterstatus. Ausgaben mindestens TXT + JSON.

## 13. Security-by-Design
Stabile Referenz: NIST SSDF 1.1. SSDF 1.2 bleibt bis zur Finalisierung Beobachtungsquelle. OWASP SAMM ergänzt Reifeperspektiven Governance, Design, Implementation, Verification, Operations. ASVS 5.0 dient punktuell für technische Sicherheitsanforderungen.

## 14. Threat Modeling
Wiederkehrend, nicht einmalig. Vier Kernfragen:
1. Was bauen wir?
2. Was kann schiefgehen?
3. Was tun wir dagegen?
4. Haben wir ausreichend geprüft?

Threat Model wird bei neuen Vertrauensgrenzen, Plugins, Updates, IPC-/Filesystem-Funktionen, Datenformaten und externen Inhalten aktualisiert.

## 15. Primäre Bedrohungsflächen
Manipulierte Projektdateien, Path Traversal, Symlink-/TOCTOU-Fälle, Pluginmanifest/Plugininhalt, manipulierte Updates, unsichere IPC-Commands, XSS über lokale Inhalte, Log Injection, beschädigte DB, manipuliertes Backup, kompromittierte Dependency/Build-Chain und ungewollte Writes außerhalb des Projektroot.

P0-Securitybefund blockiert Stable unabhängig vom Umsetzungsgrad.

## 16. Accessibility-Vertrag
Ziel WCAG 2.2 AA soweit auf Desktop-WebView sinnvoll. Verbindlich: Tastatur-only-Kernworkflow, sichtbarer Fokus, fokussiertes Element nicht vollständig verdeckt, keine Drag-only-Funktion, ausreichend große Targets oder gleichwertige Controls, semantisches HTML, ARIA nur ergänzend, High Contrast, skalierbare Schrift, Status nicht nur Farbe und Reduced Motion.

Dialoge: Fokusfalle nur solange Modal aktiv, sinnvoller Startfokus, Fokusrückgabe nach Schließen. Live Regions gezielt, nicht spamartig.

## 17. A11y-Teststufen
Statische Checks → Tastatur-Smoke → Fokusreihenfolge → Zoom/Schrift → High Contrast → Reduced Motion → Screenreader-Stichprobe → reale Tauri-WebView-Abnahme.

## 18. Modulvertrag
Jedes Modul dokumentiert `module_id`, Version, Zweck, Inputs, Outputs, persistierte Daten, Permissions, Commands, Events, Error Codes, Tests, Accessibility Contract und Migration Contract. Ein Modulfehler darf die Dashboard-Shell nicht komplett reißen.

## 19. Fachmodule
Verbindliche 1.x-Bereiche bleiben: Einzeiler-Sammler, Monatskalender, Terminübersicht, To-Do, Entwicklerinformationen, interne Toolnotiz und Einstellungen. Sie werden erst in ihren vorgesehenen Phasen realisiert.

## 20. Pluginmodell
1.x bevorzugt deklarative/registrierte Plugins mit kleiner Host-API. Kein freier Shellzugriff, kein beliebiger Dateisystemzugriff, kein Remote-Code-Laden, keine pauschale Bridge. Aufnahme: Datei → Schema → Hash → Signaturstatus → Kompatibilität → Rechte → isolierter Smoke-Test → Registry → Aktivierung. Safe Mode deaktiviert Drittplugins.

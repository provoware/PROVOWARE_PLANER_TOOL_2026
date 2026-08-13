# I002 — Manifest + Evidence Hardening

## Ziel
Jede Iteration muss lokal und remote beweisbar machen, welcher Git-Stand geprüft wurde.

## Nachweiskette
SOURCE_MANIFEST → BUILD_MANIFEST → RELEASE_MANIFEST → EVIDENCE_MANIFEST → MANIFEST_INDEX.

Zusätzlich werden `SHA256_DATEI_INVENTAR.json`, `REMOTE_TREE_RECEIPT.json` und `QUALIFICATION_REPORT.json` geführt.

## Pflichtdaten
Für den qualifizierten Git-Stand werden Commit-SHA, Tree-SHA, Pfad, Blob-SHA, Dateimodus, Dateigröße und Prüfstatus erfasst. Inhaltsdaten werden zusätzlich über SHA-256 gebunden.

## Attestierungsmodell
Selbstreferenzen werden vermieden: Ein nachgelagerter Evidence-Stand attestiert den zuvor qualifizierten Subject-Stand. Volatile Attestierungsdateien sind aus ihrem eigenen Hash-Scope ausgeschlossen.

## Fehlerbehandlung
Fehler erhalten stabile IDs, Schweregrad, Auswirkung und klare Handlung. Kritische Inkonsistenzen blockieren die Promotion. Automatische Behandlung darf keine Nutzerdaten löschen und keine riskanten Aktionen blind wiederholen.

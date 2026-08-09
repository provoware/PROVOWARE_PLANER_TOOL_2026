# TRACEABILITY-REGISTRY — SPEZIFIKATION 0.1

## Zweck
Die Registry verbindet Anforderungen, Tests und Evidence maschinenlesbar. Sie ist kein Ersatz für die eigentliche Implementierung, sondern der Nachweisvertrag dafür.

## Identitätskette
`REQ → TEST → EVD → TODO → später REL/ART`

## Statusregeln
- `geplant`: nur spezifiziert.
- `bereit`: Spezifikation vollständig genug zur Ausführung.
- `bestanden`: real ausgeführter Test war erfolgreich.
- `erzeugt`: Evidence-Datei existiert.
- `verifiziert`: Evidence wurde gegen erwartete Identität/Hash/Ergebnis geprüft.

## Unzulässig
- geplante Tests als bestanden markieren,
- Hashes erfinden,
- Evidence ohne Testbezug,
- erledigten TODO ohne Required Evidence,
- Test ohne Anforderung.

## Aktueller Einsatz
`manifests/traceability/TODO_1_2.registry.json` ist der erste kanonische Datensatz.

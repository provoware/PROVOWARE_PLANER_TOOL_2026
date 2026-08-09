# PLAN-CONSISTENCY-GATE — SPEZIFIKATION 0.1

## Status
**Nur spezifiziert. Nicht implementiert.**

## Terminierung
Implementierung als **TODO 1.9**, erst nach:
- 1.7 Testgrundgerüst,
- 1.8 maschinenlesbarer Build-/Statusvertrag.

## Zweck
Automatisch prüfen, ob Plan-, Status-, Test-, Evidence- und Releaseobjekte widerspruchsfrei miteinander verbunden sind.

## Mindestprüfungen v0
1. JSON-Dateien sind syntaktisch gültig.
2. Registry entspricht Schema.
3. REQ-, TEST- und EVD-IDs sind eindeutig.
4. TEST referenziert nur existente REQ.
5. EVD referenziert nur existente TEST und REQ.
6. TODO `erledigt` benötigt alle Required Evidence `verifiziert`.
7. `PROJEKTSTATUS.json`, `manifest.json`, `DEVELOPMENT_STATUS.json` widersprechen sich nicht bei Projektname, Planversion und aktuellem TODO.
8. Release/ZIP ohne SHA-256 wird blockiert.
9. Verifizierte Evidence ohne Commit-/Artefaktbindung wird ab Releasequalifikation blockiert.
10. Fehlermeldung nennt exakte Datei, ID und Reparaturweg.

## Exitcodes v0
- 0 = konsistent.
- 2 = Schema-/Referenzfehler.
- 3 = Statuswiderspruch.
- 4 = Release-/Evidence-Blocker.
- 5 = interne Gate-Störung.

## Nichtziel v0
Keine Produktlogik ändern und keine Dateien automatisch reparieren.

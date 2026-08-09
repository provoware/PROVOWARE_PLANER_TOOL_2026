# DEVELOPER_HANDBOOK

## Arbeitsmodus
PROVOWARE Planer 2026 wird in kleinen, nachweisbaren Iterationen entwickelt. Pro Iteration existiert exakt ein primärer TODO-Punkt. Entdeckte Zusatzarbeit wird registriert und nur dann sofort umgesetzt, wenn sie zwingend zur Erfüllung des aktiven TODO gehört.

## Pflichtablauf je Iteration
1. Ausgangsstand und aktiven TODO prüfen.
2. Requirement-/ADR-/Risiko-Bezug lesen.
3. Akzeptanzkriterien festlegen.
4. kleinstmöglichen Patch bestimmen.
5. nur den Scope implementieren.
6. statische Checks.
7. Funktions-/Smoke-Test.
8. definierter Fehlerfall.
9. Fehler beheben und erneut testen.
10. Regressionstest bei Bugfix.
11. Dateigrößen-/Dependency-Prüfung.
12. Dokumentation, Status, TODO, Changelog und Manifest aktualisieren.
13. Evidence erzeugen.
14. Entwicklungsartefakt + SHA-256 erzeugen und verifizieren.

## Architekturgrenzen
`UI → validierter Tauri Command → Service → Core/OS`. Core kennt UI nicht. Die UI erhält keinen freien Dateisystemzugriff. Persistente Datenformate, Sicherheitsgrenzen und öffentliche Verträge werden über ADRs gesteuert.

## Qualität
Kein TODO ist nur durch vorhandenen Code erledigt. Done bedeutet Implementierung + statische Prüfung + Positivtest + Fehlerfall + Retest + Regression + Dokumentation + Evidence.

## Release
Stable erst nach vollständigem Gate. Ein qualifiziertes RC-Artefakt wird nach Möglichkeit unverändert zu Stable promoviert statt nach der Qualifikation neu gebaut zu werden.

## Aktuell
Nächster Produkt-TODO: **1.2 Tauri-Minimalapp offline starten**. Keine späteren Fachmodule vorziehen.

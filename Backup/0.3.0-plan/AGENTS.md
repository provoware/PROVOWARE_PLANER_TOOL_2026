# AGENTS.md

## Projektziel
PROVOWARE Planer 2026 iterativ als offline-first Linux-Desktop-App entwickeln.

## Harte Regeln
1. Exakt ein primärer TODO pro Entwicklungsiteration.
2. Nächster Produkt-TODO: 1.2 Tauri-Minimalapp offline starten.
3. Keine späteren Features vorziehen.
4. UI → validierter Tauri Command → Service → Core/OS.
5. Kein freier Dateisystemzugriff aus der UI.
6. Keine Runtime-CDNs/ungeprüften Downloads.
7. Least Privilege.
8. Erwartbare Fehler müssen in verständliche Fehlerdomänen übersetzt werden.
9. Quelldatei <1000 Zeilen; Reviewwarnung ab 600.
10. Bugfix benötigt Regressionstest.
11. Doku/Status/Changelog/Manifest sind Teil von Done.
12. Releaseartefakt benötigt Inventar und SHA-256.
13. Änderungen an Datenformat/Securitygrenze/API benötigen ADR.
14. Keine 100%-Qualitätsbehauptung ohne reale Evidence.

## Definition of Done
Implementierung + statische Checks + Funktionstest + Fehlerfall + Retest + Regression + Doku + Status + Artefakt/Evidence.

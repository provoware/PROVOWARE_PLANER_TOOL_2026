# I013 — Entwicklungsautopilot V2

## Ziel
I013 verbessert nicht die Fachfunktion des Planers, sondern die Qualität der Entwicklungsarbeit selbst. Ausgangspunkt war die I012-Qualifikation: Die Sicherheitsgates funktionierten, zwei vermeidbare Remote-Schleifen entstanden jedoch durch eine ungünstige Prüfkosten-Reihenfolge.

## Kernänderung
Die verbindliche Reihenfolge lautet:

`Ermittlung → Plan → P0 Static → P1 Zielprüfung → P2 Runtime → P3 Regression → P4 Evidence → P5 Promotion → Optimierung`

Ein später, teurer Gate darf keinen Fehler entdecken, der bereits ohne Runtime-Abhängigkeiten eindeutig feststellbar gewesen wäre.

## Ermittlung
Vor jeder Iteration werden Baseline-Commit, Baseline-Tree, Risikoklasse, Änderungsumfang und Akzeptanzkriterien erfasst. `ITERATION_PLAN.json` ist dafür die maschinenlesbare Quelle.

## Planung
Der Dateiänderungsumfang besteht aus drei disjunkten Mengen: `add`, `modify`, `delete`. Das Soll-Inventar wird ausschließlich aus dem letzten qualifizierten Repository-Soll plus dieser Differenz gebildet.

Eine aktuelle Arbeitskopie darf ihr eigenes Soll nicht mehr rückwirkend definieren.

## Umsetzung
Die Iteration wird auf einem isolierten Zweig vollständig zusammengesetzt. Der qualifizierende Workflow soll erst am Ende der Kandidatenmontage aktiviert werden. Branch-Concurrency verwirft veraltete Läufe.

## P0 — Statische Vorprüfung
Ohne apt, pip, Qt oder Anwendungsruntime werden geprüft:
- JSON-Syntax,
- Python-Syntax,
- Version/Iteration/Checkpoint,
- Standardindex,
- stabile README-Abschnittsmarker,
- Entwicklungs-Pipelinevertrag,
- Baseline + deklarierte Repository-Differenz,
- Workflow-Härtung.

## P1/P2 — Zielvalidierung
Neue Prozesswerkzeuge werden zuerst mit eng begrenzten Zieltests geprüft. Runtime-Abhängigkeiten dürfen erst nach P0 installiert werden.

## P3 — Regression
Die vollständige Unit-/Regressionstestsuite läuft genau einmal pro Pass. Die historische Gate-Kette läuft ebenfalls genau einmal. Risikorelevante Matrizen bleiben erhalten und werden nicht aus Effizienzgründen entfernt.

## P4 — Evidence
Die erste erfolgreiche Qualifikation erzeugt das Evidence-Overlay. Anschließend wird exakt dessen SHA in einem read-only Zweitpass erneut geprüft. Der Zweitpass darf keinen Commit erzeugen.

## P5 — Promotion
Promotion nach `main` ist nur bei `ahead > 0`, `behind = 0` und identischer Merge-Base zulässig. `force` bleibt verboten. Nach der Promotion folgt eine unabhängige Main-Nachprüfung.

## Dokumentationspräzision
Statt exakter Überschriftentexte werden stabile semantische Marker verwendet. Dadurch bleibt die geforderte Dokumentstruktur verbindlich, ohne sprachlich sinnvolle Umformulierungen als technische Fehler zu behandeln.

## Effizienzmetriken
Gemessen werden mindestens:
- vermeidbare fehlgeschlagene Remote-Läufe,
- doppelte Gate-Ausführungen,
- Zeitpunkt statischer Fehler relativ zum Runtime-Setup,
- Laufzeit der Qualifikation,
- Anzahl vollständiger Regressionen pro Pass,
- ungeplante Repository-Pfade.

## I012-Baseline
I012 benötigte vor dem finalen Erfolg zwei vermeidbare Fehlversuche: einen statischen GUI-Vertragsfehler und einen Dokumentationsstrukturfehler. Beide Fehlerklassen werden in I013 nach P0 verschoben.

## Nächster Produktentwicklungsschritt
Nach I013 folgt I014: immutable Backup-/RestorePlan mit Kandidatenqualifikation. Damit wird die sicherheitskritische Restore-Entwicklung erstmals vollständig unter dem neuen Entwicklungsvertrag umgesetzt.

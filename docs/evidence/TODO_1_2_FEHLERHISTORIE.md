# TODO 1.2 — Fehlerhistorie und Fixnachweis

## Run 1 — 31293494519
**Befund:** Tauri `generate_context!()` konnte `src-tauri/icons/icon.png` nicht finden.  
**Ursache:** Minimalprojekt enthielt kein von Tauri erwartetes Desktop-Runtime-Icon.  
**Fixversuch:** leere Bundle-Iconliste.

## Run 2 — 31293600645
**Befund:** derselbe Fehler blieb bestehen.  
**Erkenntnis:** `bundle.icon = []` entfernt die Kontextanforderung nicht.  
**Fix:** reale lokale PNG-Ressource `src-tauri/icons/icon.png` hinzugefügt.

## Run 3 — 31293732658
**Produktprüfungen:** Rust-Checks, Build sowie zwei reale Offline-Fensterstarts bestanden.  
**Restfehler:** letzter Workflow-Schritt scheiterte ausschließlich an fehlerhafter Shell-Quote-Syntax im zusätzlichen Grep-Gate.

## Run 4 — 31293938431
**Produktprüfungen:** Build sowie beide Offline-Fensterstarts erneut bestanden.  
**Restfehler:** der nach dem Build erneut gestartete Validator durchsuchte versehentlich `src-tauri/target/` und versuchte generierte Binärdaten als UTF-8-Quelltext zu lesen.

## Run 5 — 31294082046
**Fix:** Dateigrößenprüfung auf eigene Quellbereiche begrenzt und Missing-Icon-Regression ergänzt.  
**Ergebnis:** vollständige TODO-1.2-Qualifikation bestanden.

## Regression
Der statische Validator prüft nun zusätzlich Existenz und PNG-Signatur von `src-tauri/icons/icon.png`, damit der erste reale Fehler nicht erneut unbemerkt auftreten kann.

# TODO 1.2 — Qualifikationsnachweis

**Software:** 0.4.0-dev.1  
**Plan:** 0.3.1-plan  
**Getesteter Commit:** `5a8f03223f5c22168cf4a4171d45df391280ae14`  
**GitHub-Run:** `31294082046` / Job `93196179804`  
**Ergebnis:** **BESTANDEN**

## Reale Umgebung
- Ubuntu 22.04.5 LTS
- rustc 1.97.1
- cargo 1.97.1
- WebKitGTK 4.1: 2.50.4
- Tauri direkt gepinnt: 2.11.2
- tauri-build direkt gepinnt: 2.6.2

## Bestandene Prüfungen
1. statische Scope-/CSP-/Assetprüfung
2. cargo fmt --check
3. cargo check
4. cargo clippy -- -D warnings
5. cargo build
6. realer Fensterstart unter Xvfb
7. Netzwerk-Namespace ohne Außenverbindung
8. unmittelbarer zweiter Start
9. Remote-Runtime-Asset-Gate
10. lokales ZIP-Inventar/CRC/SHA-256-Gate

## Scopegrenze
Keine Fachmodule, SQLite-Produktpersistenz, Plugins, Updates, Backupengine oder vollständiges Dashboard wurden vorgezogen. AppImage folgt gemäß Roadmap später.

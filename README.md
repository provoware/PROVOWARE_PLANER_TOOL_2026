# PROVOWARE_PLANER_TOOL_2026

Portable, offline-first Linux-Desktop-Anwendung mit HTML/CSS/TypeScript-Oberfläche und Tauri-2/Rust-Systemkern.

## Aktueller Stand
- **Software:** `0.4.0-dev.1`
- **Planungsbaseline:** `0.3.1-plan`
- **TODO 1.2:** qualifiziert abgeschlossen
- **Nächster erlaubter Produkt-TODO:** 1.3 Frontend-Minimalstart — noch nicht begonnen
- **Plan-Consistency-Gate:** weiterhin nur spezifiziert; Umsetzung erst TODO 1.9 nach 1.7/1.8

## Sichtbares Ergebnis 1.2
Eine minimale lokale Tauri-2-Anwendung öffnet unter Ubuntu 22.04/WebKitGTK 4.1 ein reales Fenster. Der Start und unmittelbare Restart wurden zusätzlich in einem isolierten Netzwerk-Namespace ohne Außenverbindung geprüft.

## Technische Basis
- Rust/Tauri-Minimalruntime
- `tauri = =2.11.2`
- `tauri-build = =2.6.2`
- lokale `ui/index.html` und `ui/styles.css`
- kein JavaScript im Walking Skeleton
- CSP mit `connect-src 'none'`
- minimale Capability `core:default` für das Hauptfenster

## Prüfung
```bash
python3 tests/smoke/todo_1_2_static.py
cargo fmt --manifest-path src-tauri/Cargo.toml -- --check
cargo check --manifest-path src-tauri/Cargo.toml
cargo clippy --manifest-path src-tauri/Cargo.toml -- -D warnings
cargo build --manifest-path src-tauri/Cargo.toml
```

Der reale Linux-Nachweis liegt unter `docs/evidence/TODO_1_2_QUALIFIKATION.*`.

## Noch bewusst nicht enthalten
SQLite-Produktpersistenz, Fachmodule, Pluginmanager, Update-/Backupengine, vollständiges Dashboard und AppImage-Paketierung.

## Repository
https://github.com/provoware/PROVOWARE_PLANER_TOOL_2026

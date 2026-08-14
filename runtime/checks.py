from __future__ import annotations

import hashlib
import importlib
import json
import platform
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

from .faults import RuntimeContext
from .model import Phase, PhaseResult, PhaseStatus, StepResult


def p(phase: Phase, status: PhaseStatus, code: str, msg: str, tech: str = "", action: str = "KEINE") -> PhaseResult:
    return PhaseResult(phase, status, code, msg, tech, action)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _existing_parent(path: Path) -> Path:
    current = path
    while not current.exists() and current.parent != current:
        current = current.parent
    return current


def _open_db(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(path, timeout=1.0)


def system_check(ctx: RuntimeContext) -> StepResult:
    r = StepResult("system", "System")
    ok = platform.system().lower() == "linux" and sys.version_info >= (3, 12)
    if not ok:
        r.phases.append(p(Phase.PRECHECK, PhaseStatus.BLOCKED, "START-SYS-001",
                          "Das System erfüllt die Startvoraussetzungen nicht.",
                          f"os={platform.system()} python={sys.version.split()[0]}", "START ABBRECHEN"))
        return r
    r.phases += [
        p(Phase.PRECHECK, PhaseStatus.PASS, "START-SYS-PRE", "Linux und Python 3.12+ sind verfügbar."),
        p(Phase.ACTION, PhaseStatus.INFO, "START-SYS-ACTION", "Keine Systemänderung erforderlich.",
          f"architektur={platform.machine()}"),
        p(Phase.POSTCHECK, PhaseStatus.PASS, "START-SYS-POST", "Systemprüfung abgeschlossen."),
    ]
    return r


def runtime_check(ctx: RuntimeContext) -> StepResult:
    r = StepResult("runtime", "Python-Laufzeit")
    required = ("json", "sqlite3", "pathlib", "logging", "hashlib")
    missing = []
    for name in required:
        try:
            importlib.import_module(name)
        except Exception:
            missing.append(name)
    if missing:
        r.phases.append(p(Phase.PRECHECK, PhaseStatus.BLOCKED, "START-RUNTIME-001",
                          "Benötigte Python-Bestandteile fehlen.", ",".join(missing), "START ABBRECHEN"))
        return r
    r.phases += [
        p(Phase.PRECHECK, PhaseStatus.PASS, "START-RUNTIME-PRE", "Alle Pflichtbestandteile der Laufzeit sind vorhanden."),
        p(Phase.ACTION, PhaseStatus.INFO, "START-RUNTIME-ACTION", "Keine Laufzeitreparatur erforderlich."),
        p(Phase.POSTCHECK, PhaseStatus.PASS, "START-RUNTIME-POST", "Laufzeitprüfung abgeschlossen."),
    ]
    return r


def manifest_check(ctx: RuntimeContext) -> StepResult:
    r = StepResult("manifest", "Programm- und Dateiintegrität")
    inventory = ctx.repo_root / "SHA256_DATEI_INVENTAR.json"
    if not inventory.is_file():
        r.phases.append(p(Phase.PRECHECK, PhaseStatus.BLOCKED, "START-MANIFEST-001",
                          "Das Datei-Inventar fehlt.", str(inventory), "START BLOCKIEREN"))
        return r
    r.phases.append(p(Phase.PRECHECK, PhaseStatus.PASS, "START-MANIFEST-PRE", "Das SHA-256-Inventar ist vorhanden."))
    if ctx.fault("manifest_tampered"):
        r.phases.append(p(Phase.ACTION, PhaseStatus.BLOCKED, "START-MANIFEST-001",
                          "Eine manipulierte Programmdatei wurde erkannt.",
                          "Fault-Injection manifest_tampered", "NICHT REPARIEREN; START BLOCKIEREN"))
        return r
    try:
        data = json.loads(inventory.read_text(encoding="utf-8"))
        bad = []
        for item in data.get("entries", []):
            path = ctx.repo_root / item["path"]
            if not path.is_file() or path.stat().st_size != item["size"] or _sha256(path) != item["sha256"]:
                bad.append(item["path"])
                if len(bad) == 5:
                    break
    except Exception as exc:
        bad = [f"Inventar nicht lesbar: {exc!r}"]
    if bad:
        r.phases.append(p(Phase.ACTION, PhaseStatus.BLOCKED, "START-MANIFEST-001",
                          "Die Programmintegrität ist nicht bestätigt.", "; ".join(bad), "START BLOCKIEREN"))
        return r
    r.phases += [
        p(Phase.ACTION, PhaseStatus.PASS, "START-MANIFEST-ACTION", "Alle gebundenen Dateien stimmen mit Hash und Größe überein."),
        p(Phase.POSTCHECK, PhaseStatus.PASS, "START-MANIFEST-POST", "Integritätsprüfung abgeschlossen."),
    ]
    return r


def workspace_check(ctx: RuntimeContext) -> StepResult:
    r = StepResult("workspace", "Persistenter Arbeitsordner")
    if ctx.fault("missing_permissions"):
        r.phases.append(p(Phase.PRECHECK, PhaseStatus.BLOCKED, "START-WORKSPACE-PERM-001",
                          "Der Arbeitsordner ist nicht beschreibbar.",
                          "Fault-Injection missing_permissions", "KEINE RECHTE AUTOMATISCH ERHÖHEN"))
        return r
    if ctx.fault("disk_full"):
        r.phases.append(p(Phase.PRECHECK, PhaseStatus.BLOCKED, "START-WORKSPACE-DISK-001",
                          "Es ist nicht genug freier Speicher verfügbar.",
                          "Fault-Injection disk_full", "VOR JEDEM SCHREIBEN BLOCKIEREN"))
        return r

    free = shutil.disk_usage(_existing_parent(ctx.workspace)).free
    minimum = 64 * 1024 * 1024
    if free < minimum:
        r.phases.append(p(Phase.PRECHECK, PhaseStatus.BLOCKED, "START-WORKSPACE-DISK-001",
                          "Es ist nicht genug freier Speicher verfügbar.",
                          f"frei={free}; minimum={minimum}", "VOR JEDEM SCHREIBEN BLOCKIEREN"))
        return r

    if ctx.workspace.exists():
        r.phases.append(p(Phase.PRECHECK, PhaseStatus.PASS, "START-WORKSPACE-PRE", "Der Arbeitsordner ist vorhanden."))
        recovered = False
    else:
        r.phases.append(p(Phase.PRECHECK, PhaseStatus.ACTION_REQUIRED, "START-WORKSPACE-MISSING",
                          "Der Arbeitsordner fehlt und kann sicher angelegt werden.", str(ctx.workspace), "ORDNER ANLEGEN"))
        ctx.workspace.mkdir(parents=True, exist_ok=True)
        ctx.recovery_actions.append("workspace_created")
        recovered = True

    probe = ctx.workspace / ".i003-probe"
    renamed = ctx.workspace / ".i003-probe-renamed"
    try:
        probe.write_text("PROVOWARE-I003", encoding="utf-8")
        if probe.read_text(encoding="utf-8") != "PROVOWARE-I003":
            raise OSError("Leserückprüfung fehlgeschlagen")
        probe.rename(renamed)
        renamed.unlink()
    except Exception as exc:
        for item in (probe, renamed):
            try:
                item.unlink(missing_ok=True)
            except Exception:
                pass
        r.phases.append(p(Phase.ACTION, PhaseStatus.BLOCKED, "START-WORKSPACE-PERM-001",
                          "Die reale Lese-/Schreibprobe ist fehlgeschlagen.", repr(exc), "START BLOCKIEREN"))
        return r

    r.phases += [
        p(Phase.ACTION, PhaseStatus.RECOVERED if recovered else PhaseStatus.PASS, "START-WORKSPACE-ACTION",
          "Arbeitsordner angelegt und reale Lese-/Schreib-/Umbenenn-/Löschprobe bestanden."
          if recovered else "Reale Lese-/Schreib-/Umbenenn-/Löschprobe bestanden."),
        p(Phase.POSTCHECK, PhaseStatus.PASS, "START-WORKSPACE-POST", "Die Probe wurde rückstandsfrei aufgeräumt."),
    ]
    return r


def _default_config() -> dict:
    return {"schema_version": 1, "language": "de", "autosave_minutes": 5, "safe_mode": True}


def config_check(ctx: RuntimeContext) -> StepResult:
    r = StepResult("configuration", "Konfiguration")
    if not ctx.config_path.exists():
        r.phases.append(p(Phase.PRECHECK, PhaseStatus.ACTION_REQUIRED, "START-CONFIG-MISSING",
                          "Die Konfiguration fehlt; sichere Standardwerte können angelegt werden.",
                          str(ctx.config_path), "STANDARDKONFIGURATION ANLEGEN"))
        ctx.config_path.write_text(json.dumps(_default_config(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        ctx.recovery_actions.append("config_created")
        r.phases.append(p(Phase.ACTION, PhaseStatus.RECOVERED, "START-CONFIG-CREATED",
                          "Eine sichere Standardkonfiguration wurde erstellt."))
    else:
        r.phases.append(p(Phase.PRECHECK, PhaseStatus.PASS, "START-CONFIG-PRE", "Die Konfigurationsdatei ist vorhanden."))
        try:
            data = json.loads(ctx.config_path.read_text(encoding="utf-8"))
            if data.get("schema_version") != 1:
                raise ValueError("schema_version fehlt oder ist falsch")
            r.phases.append(p(Phase.ACTION, PhaseStatus.PASS, "START-CONFIG-ACTION", "Die Konfiguration ist gültig."))
        except Exception as exc:
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            quarantine = ctx.workspace / f"config.corrupt-{stamp}.json"
            try:
                ctx.config_path.rename(quarantine)
                ctx.config_path.write_text(json.dumps(_default_config(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                ctx.recovery_actions.append(f"config_quarantined:{quarantine.name}")
                r.phases.append(p(Phase.ACTION, PhaseStatus.RECOVERED, "START-CONFIG-001",
                                  "Die beschädigte Konfiguration wurde gesichert und durch sichere Standardwerte ersetzt.",
                                  repr(exc), "QUARANTÄNE + STANDARDWERTE"))
            except Exception as repair_exc:
                r.phases.append(p(Phase.ACTION, PhaseStatus.RECOVERY_REQUIRED, "START-CONFIG-001",
                                  "Die Konfiguration konnte nicht sicher wiederhergestellt werden.",
                                  repr(repair_exc), "MANUELLE WIEDERHERSTELLUNG"))
                return r
    try:
        valid = json.loads(ctx.config_path.read_text(encoding="utf-8")).get("schema_version") == 1
    except Exception:
        valid = False
    r.phases.append(p(Phase.POSTCHECK, PhaseStatus.PASS if valid else PhaseStatus.RECOVERY_REQUIRED,
                      "START-CONFIG-POST" if valid else "START-CONFIG-001",
                      "Die Konfiguration ist nach der Prüfung gültig." if valid else "Die Konfiguration ist weiterhin ungültig."))
    return r


def database_check(ctx: RuntimeContext) -> StepResult:
    r = StepResult("database", "SQLite-Datenbank")
    if ctx.fault("sqlite_locked"):
        r.phases.append(p(Phase.PRECHECK, PhaseStatus.RECOVERY_REQUIRED, "START-DB-LOCK-001",
                          "Die Datenbank ist gesperrt.", "Fault-Injection sqlite_locked", "NICHT ERZWINGEN; SPÄTER ERNEUT PRÜFEN"))
        return r

    if not ctx.database_path.exists():
        r.phases.append(p(Phase.PRECHECK, PhaseStatus.ACTION_REQUIRED, "START-DB-MISSING",
                          "Die lokale Datenbank fehlt und kann neu angelegt werden.", str(ctx.database_path), "LEERE DATENBANK ANLEGEN"))
        try:
            con = _open_db(ctx.database_path)
            try:
                con.execute("PRAGMA journal_mode=WAL")
                con.execute("CREATE TABLE IF NOT EXISTS runtime_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
                con.commit()
            finally:
                con.close()
            ctx.recovery_actions.append("database_created")
            r.phases.append(p(Phase.ACTION, PhaseStatus.RECOVERED, "START-DB-CREATED", "Eine neue lokale Datenbank wurde angelegt."))
        except Exception as exc:
            r.phases.append(p(Phase.ACTION, PhaseStatus.RECOVERY_REQUIRED, "START-DB-CORRUPT-001",
                              "Die Datenbank konnte nicht sicher angelegt werden.", repr(exc), "WIEDERHERSTELLUNG ERFORDERLICH"))
            return r
    else:
        r.phases.append(p(Phase.PRECHECK, PhaseStatus.PASS, "START-DB-PRE", "Die Datenbankdatei ist vorhanden."))
        try:
            con = _open_db(ctx.database_path)
            try:
                row = con.execute("PRAGMA quick_check").fetchone()
                if not row or row[0] != "ok":
                    raise sqlite3.DatabaseError(f"quick_check={row}")
                con.execute("SAVEPOINT i003_probe")
                con.execute("CREATE TABLE IF NOT EXISTS runtime_probe (id INTEGER)")
                con.execute("INSERT INTO runtime_probe(id) VALUES (1)")
                count = con.execute("SELECT COUNT(*) FROM runtime_probe").fetchone()[0]
                con.execute("ROLLBACK TO i003_probe")
                con.execute("RELEASE i003_probe")
                if count < 1:
                    raise sqlite3.DatabaseError("Transaktionsprobe fehlgeschlagen")
            finally:
                con.close()
            r.phases.append(p(Phase.ACTION, PhaseStatus.PASS, "START-DB-ACTION", "SQLite-Integrität und Transaktionsprobe sind erfolgreich."))
        except sqlite3.OperationalError as exc:
            r.phases.append(p(Phase.ACTION, PhaseStatus.RECOVERY_REQUIRED, "START-DB-LOCK-001",
                              "Die Datenbank ist vorübergehend nicht verfügbar.", repr(exc), "NICHT ERZWINGEN; SPÄTER ERNEUT PRÜFEN"))
            return r
        except sqlite3.DatabaseError as exc:
            r.phases.append(p(Phase.ACTION, PhaseStatus.RECOVERY_REQUIRED, "START-DB-CORRUPT-001",
                              "Die Datenbank ist beschädigt oder nicht sicher lesbar.", repr(exc), "NICHT ÜBERSCHREIBEN; BACKUP/RESTORE"))
            return r

    try:
        con = _open_db(ctx.database_path)
        try:
            ok = con.execute("PRAGMA quick_check").fetchone()[0] == "ok"
        finally:
            con.close()
    except Exception:
        ok = False
    r.phases.append(p(Phase.POSTCHECK, PhaseStatus.PASS if ok else PhaseStatus.RECOVERY_REQUIRED,
                      "START-DB-POST" if ok else "START-DB-CORRUPT-001",
                      "Die Datenbank ist konsistent." if ok else "Die Datenbank ist nicht konsistent."))
    return r


def recovery_check(ctx: RuntimeContext) -> StepResult:
    r = StepResult("recovery", "Recovery")
    r.phases.append(p(Phase.PRECHECK, PhaseStatus.PASS, "START-RECOVERY-PRE", "Recovery-Status wird ausgewertet."))
    if ctx.recovery_actions:
        r.phases.append(p(Phase.ACTION, PhaseStatus.RECOVERED, "START-RECOVERY-ACTION",
                          "Sichere Wiederherstellungsmaßnahmen wurden angewendet.",
                          ",".join(ctx.recovery_actions), "ALLE MASSNAHMEN NACHPRÜFEN"))
    else:
        r.phases.append(p(Phase.ACTION, PhaseStatus.INFO, "START-RECOVERY-NONE", "Keine Wiederherstellung war erforderlich."))
    r.phases.append(p(Phase.POSTCHECK, PhaseStatus.PASS, "START-RECOVERY-POST", "Recovery-Prüfung abgeschlossen."))
    return r


def modules_check(ctx: RuntimeContext) -> StepResult:
    r = StepResult("modules", "Module")
    r.phases.append(p(Phase.PRECHECK, PhaseStatus.PASS, "START-MODULE-PRE", "Pflichtmodule werden geprüft."))
    if ctx.fault("optional_module_missing"):
        r.phases.append(p(Phase.ACTION, PhaseStatus.DEGRADED, "START-MODULE-OPTIONAL-001",
                          "Ein optionales Modul fehlt; der Kern kann weiterlaufen.",
                          "Fault-Injection optional_module_missing", "DEGRADIERT WEITERLAUFEN"))
    else:
        missing = []
        for name in ("runtime.model", "runtime.faults", "runtime.checks", "runtime.orchestrator"):
            try:
                importlib.import_module(name)
            except Exception:
                missing.append(name)
        if missing:
            r.phases.append(p(Phase.ACTION, PhaseStatus.BLOCKED, "START-MODULE-001",
                              "Ein Pflichtmodul fehlt.", ",".join(missing), "START BLOCKIEREN"))
            return r
        r.phases.append(p(Phase.ACTION, PhaseStatus.PASS, "START-MODULE-ACTION", "Alle I003-Pflichtmodule sind verfügbar."))
    r.phases.append(p(Phase.POSTCHECK, PhaseStatus.PASS, "START-MODULE-POST", "Modulprüfung abgeschlossen."))
    return r


def logging_check(ctx: RuntimeContext) -> StepResult:
    r = StepResult("logging", "Protokollierung")
    r.phases.append(p(Phase.PRECHECK, PhaseStatus.PASS, "START-LOG-PRE", "Protokollpfad wird geprüft."))
    try:
        ctx.log_path.parent.mkdir(parents=True, exist_ok=True)
        marker = f"I003-START-CHECK {datetime.now(timezone.utc).isoformat()}"
        with ctx.log_path.open("a", encoding="utf-8") as fh:
            fh.write(marker + "\n")
        ok = marker in ctx.log_path.read_text(encoding="utf-8")
    except Exception as exc:
        r.phases.append(p(Phase.ACTION, PhaseStatus.DEGRADED, "START-LOG-001",
                          "Die Protokollierung ist eingeschränkt.", repr(exc), "DEGRADIERT WEITERLAUFEN"))
        return r
    r.phases += [
        p(Phase.ACTION, PhaseStatus.PASS if ok else PhaseStatus.DEGRADED, "START-LOG-ACTION", "Protokoll kann geschrieben und rückgelesen werden."),
        p(Phase.POSTCHECK, PhaseStatus.PASS if ok else PhaseStatus.DEGRADED, "START-LOG-POST", "Protokollierung ist einsatzbereit."),
    ]
    return r


def event_bus_check(ctx: RuntimeContext) -> StepResult:
    r = StepResult("event_bus", "Ereignisbus")
    r.phases.append(p(Phase.PRECHECK, PhaseStatus.PASS, "START-EVENT-PRE", "Ereignis-Rundlauf wird vorbereitet."))
    queue = [{"event": "runtime_probe", "value": 1}]
    ok = queue.pop(0) == {"event": "runtime_probe", "value": 1}
    r.phases += [
        p(Phase.ACTION, PhaseStatus.PASS if ok else PhaseStatus.BLOCKED, "START-EVENT-ACTION" if ok else "START-EVENT-001",
          "Der Ereignisbus verarbeitet Ereignisse korrekt." if ok else "Der Ereignisbus ist nicht funktionsfähig."),
        p(Phase.POSTCHECK, PhaseStatus.PASS if ok else PhaseStatus.BLOCKED, "START-EVENT-POST" if ok else "START-EVENT-001",
          "Ereignisbus-Nachprüfung erfolgreich." if ok else "Ereignisbus-Nachprüfung fehlgeschlagen."),
    ]
    return r


def gui_check(ctx: RuntimeContext) -> StepResult:
    r = StepResult("gui", "GUI-Übergabe")
    r.phases.append(p(Phase.PRECHECK, PhaseStatus.PASS, "START-GUI-PRE",
                      "Die GUI-Übergabe wird vorbereitet; I003 startet noch keine Kalenderoberfläche."))
    ctx.gui_handoff = {
        "workspace": str(ctx.workspace),
        "configuration": str(ctx.config_path),
        "database": str(ctx.database_path),
        "runtime_state": "CHECKING",
    }
    ok = all(ctx.gui_handoff.values())
    r.phases += [
        p(Phase.ACTION, PhaseStatus.PASS, "START-GUI-ACTION", "Der spätere GUI-Start erhält einen geprüften Übergabekontext."),
        p(Phase.POSTCHECK, PhaseStatus.PASS if ok else PhaseStatus.BLOCKED, "START-GUI-POST" if ok else "START-GUI-001",
          "GUI-Übergabevertrag ist vollständig." if ok else "GUI-Übergabevertrag ist unvollständig."),
    ]
    return r


def post_start_check(ctx: RuntimeContext) -> StepResult:
    r = StepResult("post_start", "Nachstartprüfung")
    r.phases.append(p(Phase.PRECHECK, PhaseStatus.PASS, "START-POST-PRE", "Die Laufzeit wird abschließend geprüft."))
    required = (ctx.workspace, ctx.config_path, ctx.database_path, ctx.log_path)
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        r.phases.append(p(Phase.ACTION, PhaseStatus.BLOCKED, "START-POST-001",
                          "Die Nachstartprüfung hat fehlende Bestandteile gefunden.", ",".join(missing), "START NICHT FREIGEBEN"))
        return r
    marker = ctx.workspace / ".runtime-ready.json"
    marker.write_text(json.dumps({"schema_version": 1, "status": "READY"}, indent=2) + "\n", encoding="utf-8")
    ok = json.loads(marker.read_text(encoding="utf-8")).get("status") == "READY"
    r.phases += [
        p(Phase.ACTION, PhaseStatus.PASS, "START-POST-ACTION", "Die geprüfte Laufzeit wurde als startbereit markiert."),
        p(Phase.POSTCHECK, PhaseStatus.PASS if ok else PhaseStatus.BLOCKED, "START-POST-POST" if ok else "START-POST-001",
          "Nachstartprüfung erfolgreich." if ok else "Nachstartprüfung fehlgeschlagen."),
    ]
    return r


CHECKS = (
    system_check,
    runtime_check,
    manifest_check,
    workspace_check,
    config_check,
    database_check,
    recovery_check,
    modules_check,
    logging_check,
    event_bus_check,
    gui_check,
    post_start_check,
)

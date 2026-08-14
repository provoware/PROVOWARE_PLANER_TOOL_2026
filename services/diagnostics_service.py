from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from diagnostics_core.model import DiagnosisItem, DiagnosisSnapshot, DiagnosisState
from services.history_service import SyncJournalService
from storage.database import Database
from sync_core.history import JournalIntegrityState, RecoveryMode, RecoveryPlanState


class DiagnosticsService:
    """I012: bündelt bestehende Nachweise ausschließlich lesend."""

    def __init__(
        self,
        database: Database,
        journal: SyncJournalService,
        *,
        workspace: Path,
        backup_dir: Path | None = None,
        start_report_path: Path | None = None,
    ) -> None:
        self.database = database
        self.journal = journal
        self.workspace = Path(workspace)
        self.backup_dir = Path(backup_dir) if backup_dir else self.database.path.parent / "backups"
        self.start_report_path = (
            Path(start_report_path)
            if start_report_path
            else self.workspace / "LETZTER_STARTBERICHT.json"
        )

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def _readonly_quick_check(path: Path) -> tuple[bool, str]:
        if not path.is_file():
            return False, "Datei fehlt."
        connection: sqlite3.Connection | None = None
        try:
            connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
            connection.execute("PRAGMA query_only = ON")
            result = str(connection.execute("PRAGMA quick_check").fetchone()[0])
            return result == "ok", result
        except sqlite3.DatabaseError as exc:
            return False, f"{type(exc).__name__}: {exc}"
        finally:
            if connection is not None:
                connection.close()

    def _start_item(self) -> DiagnosisItem:
        if not self.start_report_path.is_file():
            return DiagnosisItem(
                "START",
                "Startzustand",
                DiagnosisState.LIMITED,
                "Noch kein gespeicherter Startbericht vorhanden.",
                "Beim nächsten normalen Start wird der letzte Startbericht im Arbeitsbereich abgelegt.",
            )
        try:
            payload = json.loads(self.start_report_path.read_text(encoding="utf-8"))
            state = str(payload.get("state", "UNKNOWN"))
            summary = str(payload.get("user_summary", "Startbericht ohne Kurztext."))
        except (OSError, ValueError, TypeError) as exc:
            return DiagnosisItem(
                "START",
                "Startzustand",
                DiagnosisState.BLOCKED,
                "Gespeicherter Startbericht ist nicht lesbar.",
                f"{type(exc).__name__}: {exc}",
            )
        if state == "READY":
            status = DiagnosisState.READY
        elif state == "DEGRADED":
            status = DiagnosisState.LIMITED
        else:
            status = DiagnosisState.BLOCKED
        return DiagnosisItem("START", "Startzustand", status, summary, f"Startstatus: {state}")

    def _database_item(self) -> DiagnosisItem:
        ok, detail = self._readonly_quick_check(self.database.path)
        if not ok:
            return DiagnosisItem(
                "DATABASE",
                "Datenbank",
                DiagnosisState.BLOCKED,
                "SQLite-Integritätsprüfung ist fehlgeschlagen.",
                detail,
            )
        try:
            connection = sqlite3.connect(f"file:{self.database.path}?mode=ro", uri=True)
            try:
                connection.execute("PRAGMA query_only = ON")
                row = connection.execute("SELECT COALESCE(MAX(version), 0) FROM schema_migrations").fetchone()
                schema = int(row[0])
            finally:
                connection.close()
        except sqlite3.DatabaseError as exc:
            return DiagnosisItem(
                "DATABASE",
                "Datenbank",
                DiagnosisState.BLOCKED,
                "Schema-Stand konnte nicht lesend bestimmt werden.",
                f"{type(exc).__name__}: {exc}",
            )
        return DiagnosisItem(
            "DATABASE",
            "Datenbank",
            DiagnosisState.READY,
            "SQLite quick_check ist erfolgreich.",
            f"Schema-Version: {schema}; Zugriff: read-only/query_only.",
        )

    def _journal_item(self) -> DiagnosisItem:
        try:
            records = self.journal.list_records()
        except Exception as exc:
            return DiagnosisItem(
                "JOURNAL",
                "Synchronisationsjournal",
                DiagnosisState.BLOCKED,
                "Journal konnte nicht verifiziert gelesen werden.",
                f"{type(exc).__name__}: {exc}",
            )
        tampered = sum(record.integrity is JournalIntegrityState.TAMPERED for record in records)
        legacy = sum(record.integrity is JournalIntegrityState.LEGACY_NO_SNAPSHOT for record in records)
        verified = sum(record.integrity is JournalIntegrityState.VERIFIED for record in records)
        if tampered:
            state = DiagnosisState.BLOCKED
            summary = f"{tampered} Journalnachweis(e) sind manipuliert oder inkonsistent."
        elif legacy:
            state = DiagnosisState.LIMITED
            summary = f"Journal ist intakt; {legacy} ältere Nachweis(e) besitzen keinen I011-Snapshot."
        else:
            state = DiagnosisState.READY
            summary = "Alle vorhandenen Journalnachweise sind konsistent."
        return DiagnosisItem(
            "JOURNAL",
            "Synchronisationsjournal",
            state,
            summary,
            f"Gesamt: {len(records)}; verifiziert: {verified}; Legacy: {legacy}; manipuliert: {tampered}.",
            len(records),
        )

    def _backup_item(self) -> DiagnosisItem:
        if not self.backup_dir.is_dir():
            return DiagnosisItem(
                "BACKUP",
                "Sicherungen",
                DiagnosisState.LIMITED,
                "Noch kein Sicherungsordner vorhanden.",
                f"Erwarteter Ordner: {self.backup_dir}",
                0,
            )
        candidates = sorted(self.backup_dir.glob("*.sqlite3"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not candidates:
            return DiagnosisItem(
                "BACKUP",
                "Sicherungen",
                DiagnosisState.LIMITED,
                "Noch keine SQLite-Sicherung gefunden.",
                f"Ordner: {self.backup_dir}",
                0,
            )
        valid = 0
        invalid: list[str] = []
        newest_valid: Path | None = None
        for candidate in candidates:
            ok, detail = self._readonly_quick_check(candidate)
            manifest = candidate.with_suffix(candidate.suffix + ".json")
            if ok and manifest.is_file():
                try:
                    data = json.loads(manifest.read_text(encoding="utf-8"))
                    expected = str(data.get("database_sha256", ""))
                    ok = len(expected) == 64 and self._sha256(candidate) == expected
                    if not ok:
                        detail = "SHA-256 stimmt nicht mit dem Sicherungsmanifest überein."
                except (OSError, ValueError, TypeError) as exc:
                    ok = False
                    detail = f"Manifestfehler: {type(exc).__name__}: {exc}"
            elif ok:
                ok = False
                detail = "Sicherungsmanifest fehlt."
            if ok:
                valid += 1
                newest_valid = newest_valid or candidate
            else:
                invalid.append(f"{candidate.name}: {detail}")
        if valid == 0:
            state = DiagnosisState.BLOCKED
            summary = "Keine vorhandene Sicherung besteht Integritäts- und Hashprüfung."
        elif invalid:
            state = DiagnosisState.LIMITED
            summary = f"{valid} gültige Sicherung(en); {len(invalid)} Sicherung(en) auffällig."
        else:
            state = DiagnosisState.READY
            summary = f"Alle {valid} Sicherung(en) sind integritäts- und hashgeprüft."
        detail = f"Neueste gültige Sicherung: {newest_valid.name if newest_valid else 'keine'}."
        if invalid:
            detail += " Auffällig: " + " | ".join(invalid[:5])
        return DiagnosisItem("BACKUP", "Sicherungen", state, summary, detail, len(candidates))

    def _recovery_item(self) -> DiagnosisItem:
        try:
            records = tuple(record for record in self.journal.list_records() if record.recovery_available)
        except Exception as exc:
            return DiagnosisItem(
                "RECOVERY",
                "Recovery-Pläne",
                DiagnosisState.BLOCKED,
                "Recovery-Voraussetzungen konnten nicht gelesen werden.",
                f"{type(exc).__name__}: {exc}",
            )
        if not records:
            return DiagnosisItem(
                "RECOVERY",
                "Recovery-Pläne",
                DiagnosisState.LIMITED,
                "Noch keine I011-Transaktion mit Recovery-Snapshot vorhanden.",
                "Ältere Receipts werden absichtlich nicht rückwirkend mit Werten ergänzt.",
                0,
            )
        ready = 0
        blocked = 0
        reasons: list[str] = []
        for record in records[:20]:
            for mode in (RecoveryMode.REAPPLY_AFTER, RecoveryMode.RESTORE_BEFORE):
                try:
                    plan = self.journal.build_recovery(record.receipt_id, mode)
                except Exception as exc:
                    blocked += 1
                    reasons.append(f"{record.receipt_id[:12]}: {type(exc).__name__}")
                    continue
                if plan.state is RecoveryPlanState.READY:
                    ready += 1
                else:
                    blocked += 1
                    if plan.blocking_reason:
                        reasons.append(plan.blocking_reason)
        state = DiagnosisState.LIMITED if blocked else DiagnosisState.READY
        summary = (
            f"{ready} RecoveryPlan-Variante(n) bereit; {blocked} sicher blockiert."
            if blocked
            else f"Alle {ready} geprüften RecoveryPlan-Varianten sind aktuell ausführbar."
        )
        details = "Blockierungen sind Schutzentscheidungen, keine automatische Reparaturanforderung."
        if reasons:
            details += " Beispiele: " + " | ".join(dict.fromkeys(reasons))[:1200]
        return DiagnosisItem("RECOVERY", "Recovery-Pläne", state, summary, details, ready + blocked)

    def snapshot(self) -> DiagnosisSnapshot:
        return DiagnosisSnapshot(
            generated_at=datetime.now(timezone.utc),
            items=(
                self._start_item(),
                self._database_item(),
                self._journal_item(),
                self._backup_item(),
                self._recovery_item(),
            ),
        )

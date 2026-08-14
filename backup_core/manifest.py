from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


BACKUP_MANIFEST_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class BackupManifest:
    schema_version: int
    created_at: str
    database_sha256: str
    size: int
    source: str

    @classmethod
    def create(cls, *, database_sha256: str, size: int, source: Path) -> BackupManifest:
        return cls(
            schema_version=BACKUP_MANIFEST_SCHEMA_VERSION,
            created_at=datetime.now(timezone.utc).isoformat(),
            database_sha256=database_sha256,
            size=size,
            source=str(source),
        )

    @classmethod
    def from_dict(cls, data: object) -> BackupManifest:
        if not isinstance(data, dict):
            raise ValueError("Manifest muss ein JSON-Objekt sein")
        if type(data.get("schema_version")) is not int:
            raise ValueError("schema_version muss eine Ganzzahl sein")
        if type(data.get("size")) is not int or data["size"] < 0:
            raise ValueError("size muss eine nichtnegative Ganzzahl sein")
        text_fields = ("created_at", "database_sha256", "source")
        if any(not isinstance(data.get(field), str) or not data[field].strip() for field in text_fields):
            raise ValueError("Textfelder dürfen nicht leer sein")

        manifest = cls(**{field: data[field] for field in cls.__dataclass_fields__})
        if manifest.schema_version != BACKUP_MANIFEST_SCHEMA_VERSION:
            raise ValueError("Unbekannte Manifestversion")
        created_at = datetime.fromisoformat(manifest.created_at)
        if created_at.utcoffset() is None:
            raise ValueError("created_at benötigt eine Zeitzone")
        return manifest

    def to_dict(self) -> dict:
        return asdict(self)

    def matches(self, *, database_sha256: str, size: int) -> bool:
        return self.database_sha256 == database_sha256 and self.size == size

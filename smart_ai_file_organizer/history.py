"""Append-only operation history for safe undo."""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Literal

from .duplicate_detector import compute_md5

logger = logging.getLogger(__name__)

SCHEMA_VERSION = 1
DEFAULT_HISTORY_DIR = ".smart-organizer"
DEFAULT_HISTORY_FILE = "history.jsonl"

OperationAction = Literal["move", "rename"]


@dataclass(frozen=True)
class OperationRecord:
    schema_version: int
    run_id: str
    timestamp: str
    action: OperationAction
    source_path: str
    destination_path: str
    source_hash: str | None
    destination_hash: str | None
    original_name: str
    final_name: str


def new_run_id() -> str:
    """Create a compact run id for grouping one organize/watch operation."""
    return uuid.uuid4().hex


def default_history_path(target_dir: str | Path) -> Path:
    """Return the default per-folder operation history path."""
    return Path(target_dir).resolve() / DEFAULT_HISTORY_DIR / DEFAULT_HISTORY_FILE


class OperationHistory:
    """Write and read structured file-operation records."""

    def __init__(self, path: str | Path):
        self.path = Path(path).expanduser().resolve()

    @classmethod
    def for_target(cls, target_dir: str | Path, path: str | Path | None = None) -> "OperationHistory":
        return cls(path if path is not None else default_history_path(target_dir))

    def record(
        self,
        *,
        run_id: str,
        action: OperationAction,
        source_path: str | Path,
        destination_path: str | Path,
        source_hash: str | None = None,
        destination_hash: str | None = None,
    ) -> OperationRecord:
        src = Path(source_path)
        dest = Path(destination_path)
        if source_hash is None and src.exists():
            source_hash = compute_md5(str(src))
        if destination_hash is None and dest.exists():
            destination_hash = compute_md5(str(dest))

        record = OperationRecord(
            schema_version=SCHEMA_VERSION,
            run_id=run_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            action=action,
            source_path=str(src.resolve()),
            destination_path=str(dest.resolve()),
            source_hash=source_hash,
            destination_hash=destination_hash,
            original_name=src.name,
            final_name=dest.name,
        )
        self.append(record)
        return record

    def append(self, record: OperationRecord) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(record), ensure_ascii=False, sort_keys=True) + "\n")

    def read_records(self) -> list[OperationRecord]:
        if not self.path.exists():
            return []
        records: list[OperationRecord] = []
        with self.path.open("r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    if data.get("schema_version") != SCHEMA_VERSION:
                        logger.warning("Skipping unsupported history record at line %d", line_no)
                        continue
                    records.append(OperationRecord(**data))
                except (TypeError, json.JSONDecodeError) as exc:
                    logger.warning("Skipping invalid history record at line %d: %s", line_no, exc)
        return records

    def latest_run_id(self) -> str | None:
        records = self.read_records()
        return records[-1].run_id if records else None

    def records_for_undo(self, run_id: str | None = None) -> list[OperationRecord]:
        records = self.read_records()
        if not records:
            return []
        selected_run_id = run_id or records[-1].run_id
        selected = [record for record in records if record.run_id == selected_run_id]
        return list(reversed(selected))


def group_run_ids(records: Iterable[OperationRecord]) -> list[str]:
    """Return run ids in the order they first appear."""
    seen: set[str] = set()
    run_ids: list[str] = []
    for record in records:
        if record.run_id not in seen:
            seen.add(record.run_id)
            run_ids.append(record.run_id)
    return run_ids

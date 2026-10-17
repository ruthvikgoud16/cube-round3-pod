"""Where workflow state and evidence live. Three implementations of one tiny interface.

MemoryStore: tests and library use.
FileStore: the CLI and default API (JSON files under out/).
SqliteStore: durable single-file persistence for deploy (STORE_BACKEND=sqlite).

Swap in another database by implementing the same methods. Evidence is IMMUTABLE:
a record_id, once written, can only be written again with identical content.
"""
from __future__ import annotations

import json
import os
import shutil
import sqlite3
import threading
from pathlib import Path


class EvidenceConflict(Exception):
    pass


class MemoryStore:
    def __init__(self) -> None:
        self.workflows: dict[str, dict] = {}
        self.evidence: dict[str, dict] = {}

    def list_workflow_ids(self) -> list[str]:
        return sorted(self.workflows)

    def load_workflow(self, workflow_id: str) -> dict | None:
        wf = self.workflows.get(workflow_id)
        return json.loads(json.dumps(wf)) if wf else None

    def save_workflow(self, wf: dict) -> None:
        self.workflows[wf["workflow_id"]] = json.loads(json.dumps(wf))

    def get_evidence(self, record_id: str) -> dict | None:
        return self.evidence.get(record_id)

    def put_evidence(self, record: dict) -> None:
        existing = self.evidence.get(record["record_id"])
        if existing and existing["content_hash"] != record["content_hash"]:
            raise EvidenceConflict(f"{record['record_id']} already exists with different content; evidence is immutable")
        self.evidence.setdefault(record["record_id"], record)


class FileStore(MemoryStore):
    def __init__(self, root: str | Path | None = None) -> None:
        super().__init__()
        self.root = Path(root or os.environ.get("OUT_DIR", "out"))
        (self.root / "workflows").mkdir(parents=True, exist_ok=True)
        (self.root / "evidence").mkdir(parents=True, exist_ok=True)
        if os.environ.get("SEED_DIR"):
            self._seed(Path(os.environ["SEED_DIR"]))

    def _seed(self, seed: Path) -> None:
        """Copy already-recorded runs into an empty store. A deployed disk starts empty on every boot, so the
        stored workflow and evidence JSON ship inside the image. A store that already holds runs is left alone."""
        if any((self.root / "workflows").glob("*.json")):
            return
        for sub in ("workflows", "evidence"):
            for src in sorted((seed / sub).glob("*.json")):
                shutil.copyfile(src, self.root / sub / src.name)

    def list_workflow_ids(self) -> list[str]:
        folder = self.root / "workflows"
        return sorted(path.stem for path in folder.glob("*.json") if path.is_file())

    def load_workflow(self, workflow_id: str) -> dict | None:
        p = self.root / "workflows" / f"{workflow_id}.json"
        return json.loads(p.read_text()) if p.exists() else None

    def save_workflow(self, wf: dict) -> None:
        p = self.root / "workflows" / f"{wf['workflow_id']}.json"
        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps(wf, indent=2))
        tmp.replace(p)  # atomic: a crash never leaves half a workflow

    def get_evidence(self, record_id: str) -> dict | None:
        p = self.root / "evidence" / f"{record_id}.json"
        return json.loads(p.read_text()) if p.exists() else None

    def put_evidence(self, record: dict) -> None:
        existing = self.get_evidence(record["record_id"])
        if existing and existing["content_hash"] != record["content_hash"]:
            raise EvidenceConflict(f"{record['record_id']} already exists with different content; evidence is immutable")
        if not existing:
            (self.root / "evidence" / f"{record['record_id']}.json").write_text(json.dumps(record, indent=2))


class SqliteStore:
    """Same four (+ list) methods as FileStore, backed by one SQLite file.

    Why SQLite: survives process restart, single deploy volume, no extra service.
    Evidence immutability is enforced with a UNIQUE record_id and content_hash check.
    """

    def __init__(self, path: str | Path | None = None) -> None:
        root = Path(os.environ.get("OUT_DIR", "out"))
        root.mkdir(parents=True, exist_ok=True)
        self.path = Path(path or os.environ.get("SQLITE_PATH") or (root / "pod.sqlite3"))
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS workflows (
                workflow_id TEXT PRIMARY KEY,
                body TEXT NOT NULL,
                updated_at TEXT
            )
            """
        )
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS evidence (
                record_id TEXT PRIMARY KEY,
                content_hash TEXT NOT NULL,
                body TEXT NOT NULL
            )
            """
        )
        self._conn.commit()
        if os.environ.get("SEED_DIR"):
            self._seed(Path(os.environ["SEED_DIR"]))

    def _seed(self, seed: Path) -> None:
        if self.list_workflow_ids():
            return
        for src in sorted((seed / "workflows").glob("*.json")):
            self.save_workflow(json.loads(src.read_text()))
        for src in sorted((seed / "evidence").glob("*.json")):
            try:
                self.put_evidence(json.loads(src.read_text()))
            except EvidenceConflict:
                pass

    def list_workflow_ids(self) -> list[str]:
        with self._lock:
            rows = self._conn.execute("SELECT workflow_id FROM workflows ORDER BY workflow_id").fetchall()
        return [r[0] for r in rows]

    def load_workflow(self, workflow_id: str) -> dict | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT body FROM workflows WHERE workflow_id = ?", (workflow_id,)
            ).fetchone()
        return json.loads(row[0]) if row else None

    def save_workflow(self, wf: dict) -> None:
        body = json.dumps(wf)
        updated = ((wf.get("timestamps") or {}).get("updated_at")) or ""
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO workflows(workflow_id, body, updated_at) VALUES (?, ?, ?)
                ON CONFLICT(workflow_id) DO UPDATE SET body = excluded.body, updated_at = excluded.updated_at
                """,
                (wf["workflow_id"], body, updated),
            )
            self._conn.commit()

    def get_evidence(self, record_id: str) -> dict | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT body FROM evidence WHERE record_id = ?", (record_id,)
            ).fetchone()
        return json.loads(row[0]) if row else None

    def put_evidence(self, record: dict) -> None:
        existing = self.get_evidence(record["record_id"])
        if existing and existing["content_hash"] != record["content_hash"]:
            raise EvidenceConflict(
                f"{record['record_id']} already exists with different content; evidence is immutable"
            )
        if existing:
            return
        with self._lock:
            self._conn.execute(
                "INSERT OR IGNORE INTO evidence(record_id, content_hash, body) VALUES (?, ?, ?)",
                (record["record_id"], record["content_hash"], json.dumps(record)),
            )
            self._conn.commit()


def build_store():
    """Factory used by the API and CLI. STORE_BACKEND=file|sqlite|memory."""
    backend = (os.environ.get("STORE_BACKEND") or "file").strip().lower()
    if backend == "sqlite":
        return SqliteStore()
    if backend == "memory":
        return MemoryStore()
    return FileStore()

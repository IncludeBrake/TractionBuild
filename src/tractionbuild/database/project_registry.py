from __future__ import annotations
import contextlib, json, time, uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional, List, Set

from src.tractionbuild.utils.fs import (
    ensure_dir, is_within, read_bytes, write_bytes,
    copy_file, remove_path, sha256_bytes
)
from src.tractionbuild.observability.events import emit, mk_event

PROJECT_ROOT = Path("output")  # change if different

@dataclass
class _TxJournal:
    tx_id: str
    started_at: float
    project_id: str
    base_dir: Path               # output/project_{id}
    rollback_dir: Path           # .rollback/{project}/{tx_id}
    created: Set[Path] = field(default_factory=set)
    modified: Dict[Path, str] = field(default_factory=dict)  # path -> preimage hash
    pre_graph: Dict[str, Any] = field(default_factory=dict)

class ProjectRegistry:
    """
    A thin facade you likely already have; we add tx support + safe write wrappers.
    """
    def __init__(self, storage_dir: Path = PROJECT_ROOT):
        self.storage_dir = storage_dir
        ensure_dir(self.storage_dir)
        self._graph: Dict[str, Dict[str, Any]] = {}     # project_id -> attrs
        self._tx: Dict[str, _TxJournal] = {}            # tx_id -> journal

    # -------- Project graph (fake or backed by Neo4j adapter) --------
    def create_project(self, name: str) -> str:
        pid = str(uuid.uuid4())
        self._graph[pid] = {"name": name, "stage": "created"}
        ensure_dir(self._project_dir(pid))
        return pid

    def get_attr(self, project_id: str, key: str) -> Any:
        return self._graph.get(project_id, {}).get(key)

    def set_attr(self, project_id: str, key: str, val: Any, tx_id: Optional[str] = None) -> None:
        # Record original graph snapshot at tx start only
        self._graph.setdefault(project_id, {})
        self._graph[project_id][key] = val

    # -------- Safe file writes (MUST be used by generators/tools) --------
    def write_file(self, project_id: str, rel_path: str, data: bytes, tx_id: Optional[str] = None) -> Path:
        base = self._project_dir(project_id)
        dest = (base / rel_path).resolve()
        if not is_within(dest, base):
            raise ValueError(f"Refusing to write outside project dir: {dest}")

        # If in tx, snapshot preimage
        if tx_id and tx_id in self._tx:
            j = self._tx[tx_id]
            before = read_bytes(dest) if dest.exists() else None
            if before is None:
                j.created.add(dest)
            else:
                j.modified.setdefault(dest, sha256_bytes(before))
                # persist a copy of original to rollback_dir
                rb = j.rollback_dir / "files" / rel_path
                copy_file(dest, rb)
        write_bytes(dest, data)
        return dest

    # -------- Transactions --------
    def begin_tx(self, project_id: str) -> str:
        tx_id = str(uuid.uuid4())
        base = self._project_dir(project_id)
        rbdir = Path(".rollback") / project_id / tx_id
        ensure_dir(rbdir)
        j = _TxJournal(
            tx_id=tx_id,
            started_at=time.time(),
            project_id=project_id,
            base_dir=base,
            rollback_dir=rbdir,
            pre_graph=json.loads(json.dumps(self._graph.get(project_id, {})))
        )
        self._tx[tx_id] = j
        emit(mk_event("eval.run", "registry", project_id, {"action": "begin_tx", "tx_id": tx_id}))
        return tx_id

    def commit_tx(self, tx_id: str) -> None:
        j = self._require_tx(tx_id)
        self._write_manifest(j, committed=True)
        del self._tx[tx_id]
        emit(mk_event("eval.run", "registry", j.project_id, {"action": "commit_tx", "tx_id": tx_id}))

    def rollback_tx(self, tx_id: str) -> None:
        j = self._require_tx(tx_id)
        # Restore files: remove created, restore modified
        for p in sorted(j.created, key=lambda x: len(str(x)), reverse=True):
            if p.exists():
                remove_path(p)
        for p, _prehash in j.modified.items():
            rel = str(p.relative_to(j.base_dir))
            backup = j.rollback_dir / "files" / rel
            if backup.exists():
                copy_file(backup, p)
        # Restore graph
        self._graph[j.project_id] = json.loads(json.dumps(j.pre_graph))
        self._write_manifest(j, committed=False, rolled_back=True)
        del self._tx[tx_id]
        emit(mk_event("eval.run", "registry", j.project_id, {"action": "rollback_tx", "tx_id": tx_id}))

    @contextlib.contextmanager
    def transaction(self, project_id: str):
        tx = self.begin_tx(project_id)
        try:
            yield tx
        except Exception:
            self.rollback_tx(tx)
            raise
        else:
            self.commit_tx(tx)

    # -------- Internals --------
    def _project_dir(self, project_id: str) -> Path:
        return (self.storage_dir / f"project_{project_id}")

    def _require_tx(self, tx_id: str) -> _TxJournal:
        if tx_id not in self._tx:
            raise RuntimeError(f"Unknown tx: {tx_id}")
        return self._tx[tx_id]

    def _write_manifest(self, j: _TxJournal, committed: bool, rolled_back: bool = False) -> None:
        manifest = {
            "tx_id": j.tx_id,
            "project_id": j.project_id,
            "started_at": j.started_at,
            "ended_at": time.time(),
            "created": [str(p.relative_to(j.base_dir)) for p in sorted(j.created)],
            "modified": [str(p.relative_to(j.base_dir)) for p in sorted(j.modified.keys())],
            "pre_graph": j.pre_graph,
            "post_graph": self._graph.get(j.project_id, {}),
            "committed": committed,
            "rolled_back": rolled_back,
        }
        ensure_dir(j.rollback_dir)
        (j.rollback_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

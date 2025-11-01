from __future__ import annotations
import hashlib, io, os, shutil
from pathlib import Path
from typing import Iterable

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

def is_within(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except Exception:
        return False

def read_bytes(path: Path) -> bytes:
    return path.read_bytes() if path.exists() else b""

def write_bytes(path: Path, data: bytes) -> None:
    ensure_dir(path.parent)
    with io.open(path, "wb") as f:
        f.write(data)

def copy_file(src: Path, dst: Path) -> None:
    ensure_dir(dst.parent)
    shutil.copy2(src, dst)

def remove_path(p: Path) -> None:
    if p.is_file():
        p.unlink(missing_ok=True)
    elif p.exists():
        shutil.rmtree(p)

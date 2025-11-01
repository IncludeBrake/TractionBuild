from pathlib import Path
import pytest, json
from src.tractionbuild.database.project_registry import ProjectRegistry

@pytest.fixture()
def reg(tmp_path: Path):
    return ProjectRegistry(storage_dir=tmp_path)

def test_commit_keeps_changes_and_manifest(reg: ProjectRegistry, tmp_path: Path):
    pid = reg.create_project("demo")
    with reg.transaction(pid) as tx:
        reg.set_attr(pid, "stage", "building", tx_id=tx)
        reg.write_file(pid, "a.txt", b"hello", tx_id=tx)
    # committed
    assert reg.get_attr(pid, "stage") == "building"
    assert (tmp_path / f"project_{pid}" / "a.txt").read_text() == "hello"
    # manifest exists
    manifests = list((Path(".rollback") / pid).rglob("manifest.json"))
    assert manifests, "manifest should be written"
    m = json.loads(manifests[-1].read_text())
    assert m["committed"] is True and m["rolled_back"] is False

def test_rollback_restores_files_and_graph(reg: ProjectRegistry, tmp_path: Path):
    pid = reg.create_project("demo")
    pdir = tmp_path / f"project_{pid}"
    # seed a file
    (pdir / "keep.txt").parent.mkdir(parents=True, exist_ok=True)
    (pdir / "keep.txt").write_text("seed", encoding="utf-8")
    reg.set_attr(pid, "stage", "seeded")

    with pytest.raises(RuntimeError):
        with reg.transaction(pid) as tx:
            # change stage + modify file + create new file
            reg.set_attr(pid, "stage", "broken", tx_id=tx)
            reg.write_file(pid, "keep.txt", b"changed", tx_id=tx)
            reg.write_file(pid, "new.txt", b"temp", tx_id=tx)
            raise RuntimeError("boom")

    # graph restored
    assert reg.get_attr(pid, "stage") == "seeded"
    # file restored
    assert (pdir / "keep.txt").read_text(encoding="utf-8") == "seed"
    # created file removed
    assert not (pdir / "new.txt").exists()

def test_refuse_escape_from_project_dir(reg: ProjectRegistry, tmp_path: Path):
    pid = reg.create_project("demo")
    with reg.transaction(pid) as tx:
        with pytest.raises(ValueError):
            reg.write_file(pid, "../escape.txt", b"bad", tx_id=tx)

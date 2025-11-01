from pathlib import Path
from src.tractionbuild.database.project_registry import ProjectRegistry
from src.tractionbuild.tools.code_tools import CodeGenerator, CodeSpec
import importlib.util
import sys

def test_codegen_fastapi_elite(tmp_path, monkeypatch):
    r = ProjectRegistry(storage_dir=tmp_path)
    pid = r.create_project("demo")
    gen = CodeGenerator(r)
    with r.transaction(pid) as tx:
        gen.generate_service(CodeSpec(project_id=pid, app_name="svc", profile="elite"), tx)

    # Import check: app.main must import
    svc_dir = tmp_path / f"project_{pid}" / "service"
    
    # Temporarily add svc_dir to sys.path to allow relative imports within the generated app
    sys.path.insert(0, str(svc_dir))
    try:
        spec = importlib.util.spec_from_file_location("app.main", svc_dir / "app" / "main.py")
        assert spec is not None and spec.loader is not None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        # Smoke run tests with TestClient via dynamic import
        from fastapi.testclient import TestClient
        client = TestClient(mod.create_app(["http://localhost:3000"]))
        assert client.get("/health").status_code == 200
    finally:
        sys.path.remove(str(svc_dir))
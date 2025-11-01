from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Literal, Dict, Any
from pathlib import Path

from src.tractionbuild.database.project_registry import ProjectRegistry
from src.tractionbuild.core.settings import get_settings
from src.tractionbuild.utils.fs import write_bytes
import json, textwrap

Lang = Literal["python"]
Framework = Literal["fastapi"]

@dataclass
class CodeSpec:
    project_id: str
    app_name: str
    language: Lang = "python"
    framework: Framework = "fastapi"
    profile: str = "elite"             # default upgraded
    root_rel: str = "service"          # where to generate within project dir

class CodeGenError(Exception): ...

class CodeGenerator:
    def __init__(self, registry: ProjectRegistry):
        self.r = registry

    def generate_service(self, spec: CodeSpec, tx_id: str) -> dict:
        if spec.language != "python" or spec.framework != "fastapi":
            raise CodeGenError("Unsupported language/framework")

        # Layout
        base = Path(spec.root_rel)
        files: Dict[str, bytes] = self._render_fastapi_elite(spec)

        # Write via registry (Phase-2 safety)
        for rel, data in files.items():
            self.r.write_file(spec.project_id, str(base / rel), data, tx_id=tx_id)

        # Stamp manifest-ish hint for humans
        self.r.write_file(spec.project_id, str(base / "TB_GENERATED.json"),
                          json.dumps({"app": spec.app_name, "profile": spec.profile}, indent=2).encode(),
                          tx_id=tx_id)

        return {"written": list(files.keys()), "profile": spec.profile}

    def _render_fastapi_elite(self, spec: CodeSpec) -> Dict[str, bytes]:
        files = {}

        # Create directories for the generated service
        app_dir = Path("app")
        routes_dir = app_dir / "routes"
        tests_dir = Path("tests")

        # app/__init__.py
        files[str(app_dir / "__init__.py")] = b""

        # app/settings.py
        files[str(app_dir / "settings.py")] = textwrap.dedent('''
            from pydantic import BaseModel, Field
            from src.tractionbuild.core.settings import get_settings

            class AppConfig(BaseModel):
                allowed_origins: list[str] = Field(default_factory=lambda: get_settings().ALLOWED_ORIGINS.split(","))
                rate_limit_rpm: int = 60
                token_budget_calls: int = 50
                token_budget_in: int = 120_000
                token_budget_out: int = 32_000

            def load_app_config() -> AppConfig:
                return AppConfig()
        ''').encode()

        # app/security.py
        files[str(app_dir / "security.py")] = textwrap.dedent('''
            from fastapi import Header, HTTPException, status
            from fastapi.middleware.cors import CORSMiddleware
            from src.tractionbuild.core.settings import get_settings

            def require_api_key(x_tb_key: str = Header(None)):
                expected = get_settings().API_KEY
                if not expected or x_tb_key is None:
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing API key")
                # constant-time compare (hmac.compare_digest recommended)
                import hmac
                if not hmac.compare_digest(x_tb_key, expected):
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API key")

            def cors_middleware(app, allowed_origins: list[str]):
                app.add_middleware(
                    CORSMiddleware,
                    allow_origins=allowed_origins,
                    allow_credentials=True,
                    allow_methods=["GET","POST","OPTIONS"],
                    allow_headers=["*"],
                )
        ''').encode()

        # app/limits.py
        files[str(app_dir / "limits.py")] = textwrap.dedent('''
            import time, collections
            from fastapi import Request, HTTPException
            from src.tractionbuild.observability.events import emit, mk_event

            class TokenBucket:
                def __init__(self, capacity: int, refill_per_min: int):
                    self.capacity = capacity
                    self.tokens = capacity
                    self.refill = refill_per_min
                    self.ts = time.time()

                def consume(self, n=1) -> bool:
                    now = time.time()
                    elapsed = now - self.ts
                    self.ts = now
                    self.tokens = min(self.capacity, self.tokens + elapsed * (self.refill / 60.0))
                    if self.tokens >= n:
                        self.tokens -= n
                        return True
                    return False

            _BUCKETS = collections.defaultdict(lambda: TokenBucket(60, 60))

            async def rate_limit(request: Request, rpm: int):
                ip = request.client.host if request.client else "unknown"
                b = _BUCKETS[ip]
                b.capacity = rpm; b.refill = rpm
                if not b.consume(1):
                    emit(mk_event("security.violation", "gateway", None, {"ip": ip, "kind":"rate_limit"}))
                    raise HTTPException(status_code=429, detail="Rate limit exceeded")

            class TokenBudget:
                calls = 0
                in_tokens = 0
                out_tokens = 0

                @classmethod
                def check(cls, max_calls, max_in, max_out):
                    if cls.calls > max_calls or cls.in_tokens > max_in or cls.out_tokens > max_out:
                        raise HTTPException(status_code=429, detail="Token budget exceeded")
        ''').encode()

        # app/logging_conf.py
        files[str(app_dir / "logging_conf.py")] = textwrap.dedent('''
            from src.tractionbuild.utils.logging import setup_logging
            setup_logging()
        ''').encode()

        # app/metrics.py
        files[str(app_dir / "metrics.py")] = textwrap.dedent('''
            from prometheus_client import Counter, Histogram

            REQUESTS = Counter("tb_http_requests_total", "HTTP requests", ["path","method","status"])
            LATENCY = Histogram("tb_http_request_seconds", "HTTP request latency", buckets=(.05,.1,.25,.5,1,2,5))

            def instrument(app):
                @app.middleware("http")
                async def _mw(req, call_next):
                    import time
                    start = time.time()
                    resp = await call_next(req)
                    LATENCY.observe(time.time()-start)
                    REQUESTS.labels(path=req.url.path, method=req.method, status=resp.status_code).inc()
                    return resp
        ''').encode()

        # app/routes/health.py
        files[str(routes_dir / "health.py")] = textwrap.dedent('''
            from fastapi import APIRouter
            router = APIRouter()
            
            @router.get("/health")
            def health(): return {"ok": True}
        ''').encode()

        # app/routes/sample.py
        files[str(routes_dir / "sample.py")] = textwrap.dedent('''
            from fastapi import APIRouter, Depends, Request
            from .. import security # Corrected import statement
            from .. import limits # Corrected import statement
            router = APIRouter()

            @router.get("/echo")
            async def echo(q: str, request: Request, _auth=Depends(security.require_api_key)):
                await limits.rate_limit(request, rpm=60)
                return {"echo": q}
        ''').encode()

        # app/main.py
        files[str(app_dir / "main.py")] = textwrap.dedent('''
            from fastapi import FastAPI
            from .security import cors_middleware
            from .metrics import instrument
            from .routes import health, sample

            def create_app(allowed_origins: list[str]) -> FastAPI:
                app = FastAPI()
                cors_middleware(app, allowed_origins)
                instrument(app)
                app.include_router(health.router, tags=["ops"])
                app.include_router(sample.router, tags=["demo"])
                return app

            app = create_app(allowed_origins=["http://localhost:3000"])
        ''').encode()

        # tests/test_imports.py
        files[str(tests_dir / "test_imports.py")] = textwrap.dedent('''
            def test_imports():
                import importlib
                importlib.import_module("app.main")
        ''').encode()

        # tests/test_health.py
        files[str(tests_dir / "test_health.py")] = textwrap.dedent('''
            from fastapi.testclient import TestClient
            from app.main import create_app
            def test_health():
                client = TestClient(create_app(["http://localhost:3000"]))
                r = client.get("/health")
                assert r.status_code == 200 and r.json()["ok"] is True
        ''').encode()

        # tests/test_security.py
        files[str(tests_dir / "test_security.py")] = textwrap.dedent('''
            from fastapi.testclient import TestClient
            from app.main import create_app
            def test_requires_api_key():
                client = TestClient(create_app(["http://localhost:3000"]))
                assert client.get("/echo", params={"q":"x"}).status_code in (401,403)
        ''').encode()

        # tests/test_rate_limit.py
        files[str(tests_dir / "test_rate_limit.py")] = textwrap.dedent('''
            from fastapi.testclient import TestClient
            from app.main import create_app
            def test_rate_limit_trips():
                client = TestClient(create_app(["http://localhost:3000"]))
                headers={"X-TB-Key":"dummy_key"}
                ok=0; blocked=False
                for _ in range(100):
                    r = client.get("/echo", params={"q":"a"}, headers=headers)
                    if r.status_code==200: ok+=1
                    if r.status_code==429: blocked=True; break
                assert ok>0 and blocked
        ''').encode()

        return files
import json, logging, os, sys, time
from pathlib import Path

def _line(rec: logging.LogRecord) -> str:
    payload = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "level": rec.levelname, "logger": rec.name, "msg": rec.getMessage(),
        "run_id": os.getenv("RUN_ID", "dev"), "module": rec.module,
        "func": rec.funcName, "line": rec.lineno,
    }
    extra = getattr(rec, "extra_fields", None)
    if isinstance(extra, dict): payload.update(extra)
    return json.dumps(payload, ensure_ascii=False)

class _JsonStream(logging.StreamHandler):
    def emit(self, rec): self.stream.write(_line(rec) + "\n"); self.flush()

def configure_logging():
    level = os.getenv("TB_LOG_LEVEL", "INFO").upper()
    log_dir = Path(os.getenv("TB_LOG_DIR", f"runs/{os.getenv('RUN_ID','dev')}/logs"))
    log_dir.mkdir(parents=True, exist_ok=True)
    logfile = log_dir / "run.jsonl"

    root = logging.getLogger(); root.handlers.clear(); root.setLevel(level)
    console = _JsonStream(sys.stdout); console.setLevel(level); root.addHandler(console)
    fh = logging.FileHandler(logfile, encoding="utf-8"); fh.setLevel(level)
    fh.setFormatter(logging.Formatter("%(message)s")); root.addHandler(fh)

    for n in ("uvicorn","httpx","watchfiles"): logging.getLogger(n).setLevel("WARNING")
    logging.getLogger("tractionbuild.boot").info("logging_ready",
        extra={"extra_fields":{"phase":"bootstrap","logfile":str(logfile)}})

from src.tractionbuild.observability.log import configure_logging
import logging, json, io, sys

def test_pii_redaction(monkeypatch, capsys):
    configure_logging()
    logging.getLogger("test").info("email=%s", {"email":"user @example.com"})
    out = capsys.readouterr().out
    rec = json.loads(out)
    assert "[REDACTED]" in json.dumps(rec)
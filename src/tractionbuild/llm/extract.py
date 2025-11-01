from __future__ import annotations
import json, hmac, hashlib
from typing import Dict, Any, Callable, List
from pydantic import ValidationError
from src.tractionbuild.llm.client import JsonChatClient
from src.tractionbuild.llm.schemas import ExtractCompanySignals, ExtractEnvelope, Abstention
from src.tractionbuild.llm.prompts import SYS_EXTRACT, USR_EXTRACT_TEMPLATE, SYS_EXTRACT_GROUNDED, USR_EXTRACT_WITH_CONTEXT_TEMPLATE
from src.tractionbuild.core.settings import get_settings
from src.tractionbuild.observability.events import emit, mk_event
from src.tractionbuild.utils.logging import setup_logging
from src.tractionbuild.agents.evaluators import simple_groundedness_eval
from src.tractionbuild.llm.context_pack import pack_contexts, deterministic_seed_from
from src.tractionbuild.rag.retrieve import retrieve as rag_retrieve, ContextItem
from src.tractionbuild.rag.redact import Redactor
from src.tractionbuild.rag.embed import MockEmbedder
from src.tractionbuild.rag.index import MiniIndex
from src.tractionbuild.rag.pack import pack_context

setup_logging()

def _hash_blob(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]

def _resolve_citations(cites: list[str] | None, index: MiniIndex | None) -> list[dict]:
    if not cites or not index:
        return []
    out = []
    # Accept forms like "docA:0" or full chunk ids "chunk_3_ab12cd34"
    for c in cites:
        entry = None
        # Try chunk id match
        if c in getattr(index, "ids", []):
            i = index.ids.index(c)
            entry = {"citation": c, "doc_id": index.metas[i].get("doc_id"), "chunk_idx": index.metas[i].get("chunk_idx"),
                     "sha1": index.metas[i].get("sha1")}
        else:
            # Try "doc:chunk_idx"
            if ":" in c:
                doc, pos = c.split(":", 1)
                try:
                    pos_i = int(pos)
                    for i, m in enumerate(index.metas):
                        if m.get("doc_id") == doc and m.get("chunk_idx") == pos_i:
                            entry = {"citation": c, "doc_id": doc, "chunk_idx": pos_i, "sha1": m.get("sha1"),
                                     "chunk_id": index.ids[i]}
                            break
                except ValueError:
                    pass
        if entry:
            out.append(entry)
    return out

def extract_company_signals(payload_text: str,
                            use_grounding: bool = True,
                            index: MiniIndex | None = None,
                            embedder=None,
                            redactor=None) -> ExtractEnvelope:
    s = get_settings()
    # choose model from settings or fall back
    model = getattr(s, "DEFAULT_LLM_MODEL", "gpt-4o-mini")
    client = JsonChatClient(model=model, timeout=20)

    # === Optional grounding
    context_block = ""
    contexts_used = []
    if use_grounding and index is not None:
        E = embedder or MockEmbedder(dim=index.dim)
        R = redactor or Redactor(salt=getattr(s, "REDACTION_SALT", ""))
        k = getattr(s, "RAG_TOP_K", 5)
        min_score = getattr(s, "RAG_MIN_SCORE", 0.3)
        ctx = rag_retrieve(payload_text, index=index, embedder=E, redactor=R, k=k, min_score=min_score)
        context_block, packed = pack_contexts(ctx, max_chars=getattr(s, "EXTRACTOR_MAX_CONTEXT_CHARS", 1200))
        contexts_used = [p.model_dump() for p in packed]

    user = USR_EXTRACT_TEMPLATE.format(
        payload=payload_text[:8000],
        context_block=context_block or "### CONTEXT\n(none)"
    )

    # === Call
    # --- Pre-flight budget check (if an external app provides one)
    TB = None
    try:
        from app.limits import TokenBudget as TB  # optional
    except Exception:
        pass

    pending_estimate = 512  # conservative default; adjust if you track prompt len
    if TB and not TB.can_spend(pending_estimate):
        abst = Abstention(abstained=True, reasons=["token_hard_cap"])
        _audit(payload_text, obj=None, abst=abst, model=model, usage={"prompt_tokens":0,"completion_tokens":0})
        return ExtractEnvelope(ok=False, model=model, usage={"prompt_tokens":0,"completion_tokens":0}, abstain=abst, raw=None)

    # If soft cap is exceeded, optionally lower model or context size
    if TB and TB.over_soft():
        try:
            model = getattr(s, "DEFAULT_LLM_MODEL_SOFT", model)  # allow downgrade via settings
        except Exception:
            pass
    seed = deterministic_seed_from(payload_text)
    resp = client.complete_json(system=SYS_EXTRACT, user=user, seed=seed)

    # === Budget bookkeeping (control points; Phase 7 wires real counters)
    try:
        from app.limits import TokenBudget  # if running inside generated app
    except Exception:
        TokenBudget = None
    if TokenBudget:
        TokenBudget.calls += 1
        TokenBudget.in_tokens += resp["usage"]["prompt_tokens"]
        TokenBudget.out_tokens += resp["usage"]["completion_tokens"]

    # === Parse + validate
    raw_content = resp["content"] or "{}"
    try:
        obj = json.loads(raw_content)
    except json.JSONDecodeError:
        abst = Abstention(abstained=True, reasons=["invalid_json"])
        _audit(payload_text, obj=None, abst=abst, model=model, usage=resp["usage"])
        return ExtractEnvelope(ok=False, model=model, usage=resp["usage"], abstain=abst, raw={"content": raw_content})

    # explicit abstention path
    if obj.get("abstained") is True:
        abst = Abstention.model_validate(obj)
        _audit(payload_text, obj=None, abst=abst, model=model, usage=resp["usage"])
        return ExtractEnvelope(ok=False, model=model, usage=resp["usage"], abstain=abst, raw=obj)

    # schema validation
    try:
        data = ExtractCompanySignals.model_validate(obj)
    except ValidationError as ve:
        abst = Abstention(abstained=True, reasons=["schema_validation_failed"])
        _audit(payload_text, obj=obj, abst=abst, model=model, usage=resp["usage"])
        return ExtractEnvelope(ok=False, model=model, usage=resp["usage"], abstain=abst, raw={"errors": ve.errors()})

    # groundedness / hedging check -> optional abstention
    score, reasons = simple_groundedness_eval(
        text=" ".join([payload_text[:2000], json.dumps(obj, ensure_ascii=False)]),
        citations=[],
        anchors=[data.company] if data.company else [],
        contexts=[c["text"] for c in contexts_used] if contexts_used else [],
    )
    if score >= get_settings().ANOMALY_SCORE_THRESH:
        abst = Abstention(abstained=True, reasons=["low_groundedness", *reasons])
        _audit(payload_text, obj=obj, abst=abst, model=model, usage=resp["usage"])
        return ExtractEnvelope(ok=False, model=model, usage=resp["usage"], abstain=abst, raw=obj)

    _audit(payload_text, obj=data.model_dump(), abst=None, model=model, usage=resp["usage"])
    raw = {"llm_obj": obj, "contexts": contexts_used}
    return ExtractEnvelope(ok=True, model=model, usage=resp["usage"], data=data, raw=raw)

def _audit(src_text: str, obj: Dict[str, Any] | None, abst: Abstention | None, model: str, usage: Dict[str,int]):
    # never log raw PII; log hashes + shapes only
    h = _hash_blob(src_text[:2000])
    event = mk_event(
        "extract.company_signals",
        actor="extractor",
        project_id=None,
        payload={
            "src_hash": h,
            "ok": obj is not None and abst is None,
            "abstained": abst.model_dump() if abst else None,
            "model": model,
            "usage": usage,
            "keys": list(obj.keys()) if obj else None
        }
    )
    emit(event)

def extract_company_signals_grounded(
    payload_text: str,
    retriever: Callable[[str, int], List[ContextItem]],
    k: int | None = None
) -> ExtractEnvelope:
    s = get_settings()
    model = getattr(s, "DEFAULT_LLM_MODEL", "gpt-4o-mini")
    k = k or getattr(s, "RAG_K", 4)

    # 1) Retrieve context
    items = retriever(payload_text, k)
    if not items:
        # Fall back to abstain if no context
        abst = Abstention(abstained=True, reasons=["no_context"])
        _audit(payload_text, obj=None, abst=abst, model=model, usage={"prompt_tokens":0,"completion_tokens":0})
        return ExtractEnvelope(ok=False, model=model, usage={"prompt_tokens":0,"completion_tokens":0}, abstain=abst, raw=None)

    # 2) Pack deterministic context block (truncate each snippet a bit)
    from src.tractionbuild.llm.tokens import count_tokens
    max_ctx_tokens = getattr(s, "RAG_CTX_MAX_TOKENS", 600)
    pairs = pack_context(items, max_tokens=max_ctx_tokens, per_snippet_cap=getattr(s, "RAG_MAX_CONTEXT_CHARS", 800))
    if not pairs:
        abst = Abstention(abstained=True, reasons=["no_context"])
        _audit(payload_text, obj=None, abst=abst, model=model, usage={"prompt_tokens":0,"completion_tokens":0})
        return ExtractEnvelope(ok=False, model=model, usage={"prompt_tokens":0,"completion_tokens":0}, abstain=abst, raw=None)

    ctx_lines = []
    for i, (snippet, ci) in enumerate(pairs):
        ctx_lines.append(f"[{ci.doc_id}:{ci.chunk_idx}|{i}] {snippet}")
    context_block = "\n".join(ctx_lines)

    user = USR_EXTRACT_WITH_CONTEXT_TEMPLATE.format(
        context=context_block,
        payload=payload_text[:4000]
    )

    client = JsonChatClient(model=model, timeout=20)
    resp = client.complete_json(system=SYS_EXTRACT_GROUNDED, user=user)

    raw_content = resp["content"] or "{}"
    try:
        obj = json.loads(raw_content)
    except json.JSONDecodeError:
        abst = Abstention(abstained=True, reasons=["invalid_json"])
        _audit(payload_text, obj=None, abst=abst, model=model, usage=resp["usage"])
        return ExtractEnvelope(ok=False, model=model, usage=resp["usage"], abstain=abst, raw={"content": raw_content})

    # Explicit abstain
    if obj.get("abstained") is True:
        abst = Abstention.model_validate(obj)
        _audit(payload_text, obj=None, abst=abst, model=model, usage=resp["usage"])
        return ExtractEnvelope(ok=False, model=model, usage=resp["usage"], abstain=abst, raw=obj)

    # Schema validate
    try:
        data = ExtractCompanySignals.model_validate(obj)
    except ValidationError as ve:
        abst = Abstention(abstained=True, reasons=["schema_validation_failed"])
        _audit(payload_text, obj=obj, abst=abst, model=model, usage=resp["usage"])
        return ExtractEnvelope(ok=False, model=model, usage=resp["usage"], abstain=abst, raw={"errors": ve.errors()})

    # Try to resolve citations against an index if the retriever carries one (optional duck-typing)
    index = getattr(retriever, "__index__", None)
    resolved = _resolve_citations(getattr(data, "citations", []), index)
    raw_obj = obj.copy()
    raw_obj["resolved_citations"] = resolved

    # 3) Post-guards: must cite & must be present in at least one context
    name_ok = bool(data.company) and any(data.company.lower() in (ci.text or "").lower() for ci in items)
    cites_ok = bool(data.citations)

    if not (name_ok and cites_ok):
        reasons = []
        if not name_ok: reasons.append("entity_not_in_context")
        if not cites_ok: reasons.append("missing_citations")
        abst = Abstention(abstained=True, reasons=reasons or ["low_groundedness"])
        _audit(payload_text, obj=obj, abst=abst, model=model, usage=resp["usage"])
        return ExtractEnvelope(ok=False, model=model, usage=resp["usage"], abstain=abst, raw=raw_obj)

    # OK
    _audit(payload_text, obj=data.model_dump(), abst=None, model=model, usage=resp["usage"])
    return ExtractEnvelope(ok=True, model=model, usage=resp["usage"], data=data, raw=raw_obj)
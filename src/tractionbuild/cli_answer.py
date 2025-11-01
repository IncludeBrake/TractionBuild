import argparse, json, sys
from src.tractionbuild.rag.redact import Redactor
from src.tractionbuild.rag.embed import MockEmbedder
from src.tractionbuild.rag.index import MiniIndex
from src.tractionbuild.rag.retrieve import prepare_corpus, retrieve
from src.tractionbuild.llm.extract import extract_company_signals
from src.tractionbuild.llm.answers import compose_answer

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--doc-id", required=True)
    ap.add_argument("--infile", required=True)
    ap.add_argument("--q", required=True, help="query prompt / task")
    ap.add_argument("--k", type=int, default=5)
    args = ap.parse_args()

    text = open(args.infile, "r", encoding="utf-8").read()
    red = Redactor()
    E = MockEmbedder()
    idx = MiniIndex(dim=8)

    # index
    prepare_corpus(args.doc_id, text, red, E, idx)

    # retrieve
    items = retrieve(args.q, idx, E, red, k=args.k, min_score=0.3, scope=None)

    # stitch a simple context block for the extractor input (deterministic)
    ctx_lines = [f"[{ci.doc_id}:{ci.chunk_idx}] {ci.text}" for ci in items]
    payload_text = "\n".join(ctx_lines)

    # extract
    env = extract_company_signals(payload_text)

    # compose
    ans = compose_answer(env, items)
    print(json.dumps(ans.model_dump(), ensure_ascii=False, indent=2))

if __name__ == "__main__":
    sys.exit(main())

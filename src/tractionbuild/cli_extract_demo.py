import argparse, sys
from src.tractionbuild.llm.extract import extract_company_signals
from src.tractionbuild.rag.index import MiniIndex
from src.tractionbuild.rag.embed import MockEmbedder
from src.tractionbuild.rag.redact import Redactor
from src.tractionbuild.rag.retrieve import prepare_corpus

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--doc-id", required=True)
    ap.add_argument("--ctx", required=True, help="Path to context txt")
    ap.add_argument("--input", required=True, help="Path to input txt")
    args = ap.parse_args()

    with open(args.ctx, "r", encoding="utf-8") as f: ctx_text = f.read()
    with open(args.input, "r", encoding="utf-8") as f: payload = f.read()

    idx = MiniIndex(dim=8)
    E = MockEmbedder(dim=8)
    R = Redactor()
    prepare_corpus(args.doc_id, ctx_text, R, E, idx)

    out = extract_company_signals(payload, use_grounding=True, index=idx, embedder=E, redactor=R)
    print(out.model_dump_json(indent=2))

if __name__ == "__main__":
    sys.exit(main())

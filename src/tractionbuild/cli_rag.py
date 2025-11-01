import argparse
from src.tractionbuild.rag.retrieve import prepare_corpus
from src.tractionbuild.rag.redact import Redactor
from src.tractionbuild.rag.embed import MockEmbedder
from src.tractionbuild.rag.index import MiniIndex

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--doc-id", required=True)
    ap.add_argument("--infile", required=True)
    ap.add_argument("--profile", default="elite")
    args = ap.parse_args()

    with open(args.infile, "r", encoding="utf-8") as f:
        text = f.read()

    redactor = Redactor()
    embedder = MockEmbedder()
    index = MiniIndex(dim=8) # MockEmbedder dim is 8

    prepare_corpus(args.doc_id, text, redactor, embedder, index, profile=args.profile)

    print(f"Indexed {args.infile} with doc_id {args.doc_id}")
    print(f"Index size: {len(index.chunks)} chunks")

if __name__ == "__main__":
    main()

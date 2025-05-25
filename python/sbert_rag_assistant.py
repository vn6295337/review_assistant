#!/usr/bin/env python3
"""
SBERT‑powered RAG Assistant
---------------------------
Requires: sentence-transformers, torch (heavy).

Usage:
  ./sbert_rag_assistant.py                # uses CHUNKS_DIR from config.sh
  ./sbert_rag_assistant.py --chunks-dir ./my_chunks --top-k 8
"""

import argparse, json, os
from pathlib import Path

# Grab default CHUNKS_DIR from config.sh if present
CFG = Path(__file__).resolve().parents[1] / "scripts" / "config.sh"
DEFAULT_CHUNKS = "./outputs/chunks"
if CFG.is_file():
    with open(CFG) as f:
        for ln in f:
            if ln.startswith("export CHUNKS_DIR"):
                DEFAULT_CHUNKS = ln.split("=",1)[1].strip().strip('"')
                break

def load_chunks(dir_path: Path):
    items = []
    for fp in dir_path.glob("*.json"):
        data = json.loads(fp.read_text())
        text = data.get("text") or data.get("content") or ""
        items.append({"text": text, "file": fp.name})
    return items

def build_embeddings(chunks, model):
    embs = model.encode([c["text"] for c in chunks], convert_to_tensor=True)
    for c,e in zip(chunks, embs): c["emb"] = e
    return chunks

def search(query, chunks, model, k):
    qv = model.encode(query, convert_to_tensor=True)
    from sentence_transformers import util
    sims = util.cos_sim(qv, [c["emb"] for c in chunks])[0]
    top = sims.argsort(descending=True)[:k]
    return [(chunks[i], float(sims[i])) for i in top]

def interactive(chunks, model, k):
    print("💬 Ask me about your codebase (exit/quit to stop)")
    while True:
        q = input("\n> ").strip()
        if q.lower() in {"exit","quit"}: break
        res = search(q, chunks, model, k)
        for i,(chunk,score) in enumerate(res,1):
            snippet = chunk["text"][:500] + ("..." if len(chunk["text"])>500 else "")
            print(f"\n#{i} • {chunk['file']} • score {score:.2f}\n{snippet}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chunks-dir", default=DEFAULT_CHUNKS, help="Directory with chunks")
    ap.add_argument("--top-k", type=int, default=5, help="Number of results")
    args = ap.parse_args()

    dir_path = Path(args.chunks_dir)
    if not dir_path.is_dir():
        print(f"❌ {dir_path} not found"); return
    chunks = load_chunks(dir_path)
    if not chunks:
        print("❌ No chunks found."); return

    print("📡 Loading SBERT model…")
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")

    chunks = build_embeddings(chunks, model)
    interactive(chunks, model, args.top_k)

if __name__ == "__main__":
    main()

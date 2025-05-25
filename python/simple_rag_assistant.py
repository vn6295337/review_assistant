#!/usr/bin/env python3
"""
Simple RAG Assistant (pure‑Python)
----------------------------------
Lightweight TF‑IDF + cosine search; no external ML libraries.

Usage:
  ./simple_rag_assistant.py             # uses CHUNKS_DIR from config.sh
  ./simple_rag_assistant.py --chunks-dir /path/to/chunks
"""

import argparse, glob, json, math, os, re, sys
from datetime import datetime
from pathlib import Path

# ───────────────────────────────────────────────────────────
# 1. Pull CHUNKS_DIR from config.sh if we’re inside repo
# ───────────────────────────────────────────────────────────
CONFIG_PATH = Path(__file__).resolve().parents[1] / "scripts" / "config.sh"
if CONFIG_PATH.is_file():
    # crude parse of "export VAR=value"
    with open(CONFIG_PATH) as cf:
        for line in cf:
            if line.startswith("export CHUNKS_DIR"):
                CHUNKS_DIR_DEFAULT = line.split("=", 1)[1].strip().strip('"')
                break
else:
    CHUNKS_DIR_DEFAULT = "./outputs/chunks"

# ───────────────────────────────────────────────────────────
# 2. Tiny TF‑IDF implementation
# ───────────────────────────────────────────────────────────
class SimpleVectorizer:
    stop_words = {
        'a','an','the','and','or','but','if','because','as','what','when','where','how',
        'which','who','whom','this','that','these','those','again','about','for','is',
        'of','while','during','to','from','in','out','on','off','over','under','through',
        'no','not','only','own','same','so','than','too','very','can','will','just','now',
        'with','by','be','been','being','am','are','was','were'
    }

    def __init__(self):
        self.doc_cnt, self.df, self.vocab = 0, {}, set()

    def _tokenise(self, txt:str):
        txt = re.sub(r'[^\w\s]', ' ', txt.lower())
        return [w for w in txt.split() if w not in self.stop_words and len(w) > 1]

    def _tf(self, tokens):
        tf = {}
        for t in tokens: tf[t] = tf.get(t, 0) + 1
        return tf

    def fit(self, docs):
        self.doc_cnt = len(docs)
        for doc in docs:
            toks = set(self._tokenise(doc))
            for tok in toks:
                self.vocab.add(tok)
                self.df[tok] = self.df.get(tok, 0) + 1

    def vector(self, doc):
        tokens = self._tokenise(doc)
        tf_raw = self._tf(tokens)
        vec, denom = {}, max(len(tokens), 1)
        for tok, freq in tf_raw.items():
            tf = freq / denom
            idf = math.log((self.doc_cnt + 1) / (self.df.get(tok, 0) + 1)) + 1
            vec[tok] = tf * idf
        return vec

    @staticmethod
    def cosine(a, b):
        common = set(a) & set(b)
        dot = sum(a[t]*b[t] for t in common)
        mag = math.sqrt(sum(v*v for v in a.values())) * math.sqrt(sum(v*v for v in b.values()))
        return 0.0 if mag == 0 else dot / mag

class VectorStore:
    def __init__(self, texts, meta):
        self.vect = SimpleVectorizer(); self.vect.fit(texts)
        self.vecs = [self.vect.vector(t) for t in texts]
        self.meta, self.texts = meta, texts

    def search(self, query, k=3):
        qv = self.vect.vector(query)
        sims = [self.vect.cosine(qv, v) for v in self.vecs]
        ranked = sorted(range(len(sims)), key=lambda i: sims[i], reverse=True)[:k]
        return [(self.texts[i], self.meta[i], sims[i]) for i in ranked]

# ───────────────────────────────────────────────────────────
# 3. Assistant class
# ───────────────────────────────────────────────────────────
class SimpleRAGAssistant:
    def __init__(self, chunks_dir):
        self.chunks_dir = Path(chunks_dir)
        self.chunks, self.meta, self.store = [], [], None

    def _load_chunks(self):
        files = list(self.chunks_dir.glob("*.json"))
        if not files:
            print(f"❌ No chunks in {self.chunks_dir}")
            return False
        for fp in files:
            try:
                data = json.loads(fp.read_text())
                self.chunks.append(data["content"])
                src = Path(data.get("metadata", {}).get("source", fp.name)).name
                self.meta.append({"source": src, "chunk_id": data.get("metadata", {}).get("chunk_id", fp.stem)})
            except Exception as e:
                print(f"⚠️  Skipped {fp.name}: {e}")
        return bool(self.chunks)

    def setup(self):
        if not self._load_chunks(): return False
        self.store = VectorStore(self.chunks, self.meta)
        return True

    def ask(self, q, k=3):
        if not self.store: return "Assistant not initialised."
        results = self.store.search(q, k)
        if not results: return "No relevant information found."
        ans = "Based on the codebase:\n\n"
        for txt, meta, sim in results:
            ans += f"From **{meta['source']}** (similarity {sim:.2f}):\n```python\n{txt.strip()}\n```\n\n"
        ans += "\nFollow‑ups you might ask:\n• Usage of these classes/functions?\n• Key dependencies?\n"
        return ans

# ───────────────────────────────────────────────────────────
# 4. CLI
# ───────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(description="Simple (dependency‑free) RAG assistant")
    p.add_argument("--chunks-dir", default=CHUNKS_DIR_DEFAULT, help="Directory with *.json chunks")
    args = p.parse_args()

    assistant = SimpleRAGAssistant(args.chunks_dir)
    if not assistant.setup(): sys.exit(1)

    print("\n🔸 RAG assistant ready.  Type your question, or 'exit'.")
    while True:
        try:
            q = input("\nQuestion> ").strip()
            if q.lower() in {"exit", "quit"}: break
            if q: print("\n" + assistant.ask(q))
        except (KeyboardInterrupt, EOFError):
            break
    print("👋 Goodbye!")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Simple RAG Assistant (pure‑Python)
----------------------------------
Lightweight TF‑IDF + cosine search; no external ML libraries.

Usage:
  ./simple_rag_assistant.py             # uses CHUNKS_DIR from config.sh
  ./simple_rag_assistant.py --chunks-dir /path/to/chunks
"""

import argparse, glob, json, math, os, re, sys
from datetime import datetime
from pathlib import Path

# ───────────────────────────────────────────────────────────
# 1. Pull CHUNKS_DIR from config.sh if we’re inside repo
# ───────────────────────────────────────────────────────────
CONFIG_PATH = Path(__file__).resolve().parents[1] / "scripts" / "config.sh"
if CONFIG_PATH.is_file():
    # crude parse of "export VAR=value"
    with open(CONFIG_PATH) as cf:
        for line in cf:
            if line.startswith("export CHUNKS_DIR"):
                CHUNKS_DIR_DEFAULT = line.split("=", 1)[1].strip().strip('"')
                break
else:
    CHUNKS_DIR_DEFAULT = "./outputs/chunks"

# ───────────────────────────────────────────────────────────
# 2. Tiny TF‑IDF implementation
# ───────────────────────────────────────────────────────────
class SimpleVectorizer:
    stop_words = {
        'a','an','the','and','or','but','if','because','as','what','when','where','how',
        'which','who','whom','this','that','these','those','again','about','for','is',
        'of','while','during','to','from','in','out','on','off','over','under','through',
        'no','not','only','own','same','so','than','too','very','can','will','just','now',
        'with','by','be','been','being','am','are','was','were'
    }

    def __init__(self):
        self.doc_cnt, self.df, self.vocab = 0, {}, set()

    def _tokenise(self, txt:str):
        txt = re.sub(r'[^\w\s]', ' ', txt.lower())
        return [w for w in txt.split() if w not in self.stop_words and len(w) > 1]

    def _tf(self, tokens):
        tf = {}
        for t in tokens: tf[t] = tf.get(t, 0) + 1
        return tf

    def fit(self, docs):
        self.doc_cnt = len(docs)
        for doc in docs:
            toks = set(self._tokenise(doc))
            for tok in toks:
                self.vocab.add(tok)
                self.df[tok] = self.df.get(tok, 0) + 1

    def vector(self, doc):
        tokens = self._tokenise(doc)
        tf_raw = self._tf(tokens)
        vec, denom = {}, max(len(tokens), 1)
        for tok, freq in tf_raw.items():
            tf = freq / denom
            idf = math.log((self.doc_cnt + 1) / (self.df.get(tok, 0) + 1)) + 1
            vec[tok] = tf * idf
        return vec

    @staticmethod
    def cosine(a, b):
        common = set(a) & set(b)
        dot = sum(a[t]*b[t] for t in common)
        mag = math.sqrt(sum(v*v for v in a.values())) * math.sqrt(sum(v*v for v in b.values()))
        return 0.0 if mag == 0 else dot / mag

class VectorStore:
    def __init__(self, texts, meta):
        self.vect = SimpleVectorizer(); self.vect.fit(texts)
        self.vecs = [self.vect.vector(t) for t in texts]
        self.meta, self.texts = meta, texts

    def search(self, query, k=3):
        qv = self.vect.vector(query)
        sims = [self.vect.cosine(qv, v) for v in self.vecs]
        ranked = sorted(range(len(sims)), key=lambda i: sims[i], reverse=True)[:k]
        return [(self.texts[i], self.meta[i], sims[i]) for i in ranked]

# ───────────────────────────────────────────────────────────
# 3. Assistant class
# ───────────────────────────────────────────────────────────
class SimpleRAGAssistant:
    def __init__(self, chunks_dir):
        self.chunks_dir = Path(chunks_dir)
        self.chunks, self.meta, self.store = [], [], None

    def _load_chunks(self):
        files = list(self.chunks_dir.glob("*.json"))
        if not files:
            print(f"❌ No chunks in {self.chunks_dir}")
            return False
        for fp in files:
            try:
                data = json.loads(fp.read_text())
                self.chunks.append(data["content"])
                src = Path(data.get("metadata", {}).get("source", fp.name)).name
                self.meta.append({"source": src, "chunk_id": data.get("metadata", {}).get("chunk_id", fp.stem)})
            except Exception as e:
                print(f"⚠️  Skipped {fp.name}: {e}")
        return bool(self.chunks)

    def setup(self):
        if not self._load_chunks(): return False
        self.store = VectorStore(self.chunks, self.meta)
        return True

    def ask(self, q, k=3):
        if not self.store: return "Assistant not initialised."
        results = self.store.search(q, k)
        if not results: return "No relevant information found."
        ans = "Based on the codebase:\n\n"
        for txt, meta, sim in results:
            ans += f"From **{meta['source']}** (similarity {sim:.2f}):\n```python\n{txt.strip()}\n```\n\n"
        ans += "\nFollow‑ups you might ask:\n• Usage of these classes/functions?\n• Key dependencies?\n"
        return ans

# ───────────────────────────────────────────────────────────
# 4. CLI
# ───────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(description="Simple (dependency‑free) RAG assistant")
    p.add_argument("--chunks-dir", default=CHUNKS_DIR_DEFAULT, help="Directory with *.json chunks")
    args = p.parse_args()

    assistant = SimpleRAGAssistant(args.chunks_dir)
    if not assistant.setup(): sys.exit(1)

    print("\n🔸 RAG assistant ready.  Type your question, or 'exit'.")
    while True:
        try:
            q = input("\nQuestion> ").strip()
            if q.lower() in {"exit", "quit"}: break
            if q: print("\n" + assistant.ask(q))
        except (KeyboardInterrupt, EOFError):
            break
    print("👋 Goodbye!")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
file_chunker.py ─ Break large files into overlapping JSON chunks
----------------------------------------------------------------
* Pure‑Python; zero external dependencies
* Defaults come from scripts/config.sh (if available) but can be overridden
* Adds rich metadata (source path, char offsets, timestamp, SHA256 of content)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict

# ───────────────────────────────────────────────────────────
# 1.  Pull default CHUNKS_DIR from config.sh if present
# ───────────────────────────────────────────────────────────
CONFIG_FILE = Path(__file__).resolve().parents[1] / "scripts" / "config.sh"
DEFAULT_CHUNKS_DIR = "./outputs/chunks"
if CONFIG_FILE.is_file():
    with CONFIG_FILE.open() as cf:
        for line in cf:
            if line.startswith("export CHUNKS_DIR"):
                DEFAULT_CHUNKS_DIR = line.split("=", 1)[1].strip().strip("\"")
                break

# ───────────────────────────────────────────────────────────
# 2.  Core logic
# ───────────────────────────────────────────────────────────

def chunk_text(
    text: str,
    file_path: Path,
    chunk_size: int = 2000,
    overlap: int = 200,
) -> List[Dict]:
    """Return a list of chunk dicts ready for JSON serialisation."""
    # Hash of *content* (stable even if file moves)
    file_hash = hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()[:12]

    chunks = []
    pos = 0
    chunk_idx = 0
    text_len = len(text)

    while pos < text_len:
        end = min(pos + chunk_size, text_len)
        chunk_dict = {
            "content": text[pos:end],
            "metadata": {
                "source": str(file_path.resolve()),
                "chunk_id": f"{file_hash}_{chunk_idx}",
                "start_char": pos,
                "end_char": end,
                "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            },
        }
        chunks.append(chunk_dict)
        if end == text_len:
            break
        pos = end - overlap  # step forward with overlap
        chunk_idx += 1
    return chunks


def write_chunks(
    chunks: List[Dict],
    output_dir: Path,
    append_mode: bool = False,
    verbose: bool = False,
) -> int:
    """Write each chunk as a separate JSON file; return # actually written."""
    written = 0
    for ch in chunks:
        fname = output_dir / f"{ch['metadata']['chunk_id']}.json"
        if append_mode and fname.exists():
            if verbose:
                print(f"↩︎  Skipping existing chunk {fname.name}")
            continue
        with fname.open("w", encoding="utf-8") as f:
            json.dump(ch, f, ensure_ascii=False, indent=2)
        written += 1
        if verbose:
            print(f"✓ Wrote {fname.name}")
    return written

# ───────────────────────────────────────────────────────────
# 3.  CLI helper
# ───────────────────────────────────────────────────────────

def parse_cli(argv: List[str] | None = None):
    p = argparse.ArgumentParser(
        description="Chunk a large text/code file into overlapping JSON chunks",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--input-file", "-i", required=True, help="Path to source file")
    p.add_argument(
        "--output-dir",
        "-o",
        default=DEFAULT_CHUNKS_DIR,
        help="Directory to store chunk files",
    )
    p.add_argument("--chunk-size", "-c", type=int, default=2000, help="Chunk size (chars)")
    p.add_argument("--overlap", "-l", type=int, default=200, help="Overlap size (chars)")
    p.add_argument(
        "--append-mode",
        "-a",
        action="store_true",
        help="Do not overwrite existing chunks; skip instead",
    )
    p.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    return p.parse_args(argv)


# ───────────────────────────────────────────────────────────
# 4.  Main entry
# ───────────────────────────────────────────────────────────

def main(argv: List[str] | None = None) -> int:  # pragma: no cover
    args = parse_cli(argv)
    infile = Path(args.input_file)
    if not infile.is_file():
        print(f"❌ Source file not found: {infile}")
        return 1

    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    if args.verbose:
        print(f"Reading {infile}…")
    text = infile.read_text(encoding="utf-8", errors="replace")

    chunks = chunk_text(text, infile, args.chunk_size, args.overlap)
    written = write_chunks(chunks, outdir, append_mode=args.append_mode, verbose=args.verbose)

    print(f"✓ {written}/{len(chunks)} chunks written to {outdir}")
    return 0 if written else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())

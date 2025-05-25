#!/usr/bin/env python3
"""
chat_exporter.py - Interactive chat session ingestor for the RAG pipeline.

1. Opens a blank nano buffer.
2. User pastes the chat and exits nano.
3. The content is saved to codebase/chat_sessions/ as a timestamped file.
4. The file is passed to file_chunker.py → outputs/chunks/
5. Then to file_summarizer.py → outputs/summaries/
"""

import os
import subprocess
import shutil
import datetime
from pathlib import Path
import argparse
import sys

# === Load environment-based configuration ===
def require_env(key):
    val = os.environ.get(key)
    if not val:
        print(f"❌ Environment variable '{key}' is not set. Did you source config.sh?")
        sys.exit(1)
    return Path(val)

CHAT_SESSIONS_DIR = require_env("CHAT_SESSIONS_DIR")
CHUNKS_DIR = require_env("CHUNKS_DIR")
SUMMARIES_DIR = require_env("SUMMARIES_DIR")
PYTHON_DIR = require_env("PYTHON_DIR")

FILE_CHUNKER = PYTHON_DIR / "file_chunker.py"
FILE_SUMMARIZER = PYTHON_DIR / "file_summarizer.py"


def open_nano(tmp_file: Path):
    try:
        subprocess.run(["nano", str(tmp_file)])
        return True
    except FileNotFoundError:
        print("❌ nano not found. Install it with `sudo apt install nano`.")
        return False


def is_file_nonempty(path: Path) -> bool:
    return path.exists() and path.stat().st_size > 5


def run_python(script: Path, *args):
    cmd = [sys.executable, str(script), *map(str, args)]
    result = subprocess.run(cmd)
    if result.returncode != 0:
        raise RuntimeError(f"Helper script failed: {' '.join(cmd)}")


def main():
    parser = argparse.ArgumentParser(description="Paste chat via nano and run RAG workflow.")
    parser.add_argument("--title", type=str, default="Chat",
                        help="Base filename prefix (default: Chat)")
    args = parser.parse_args()

    # Ensure directories exist
    CHAT_SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    CHUNKS_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARIES_DIR.mkdir(parents=True, exist_ok=True)

    # Open blank nano session
    tmp_file = Path("/tmp") / f"chat_input_{datetime.datetime.now():%Y%m%d_%H%M%S}.txt"
    print("\n📋 Paste chat content into the nano window. Save and exit when done (Ctrl-O, Enter, Ctrl-X).")
    if not open_nano(tmp_file):
        return

    if not is_file_nonempty(tmp_file):
        print("❌ No content captured. Exiting.")
        tmp_file.unlink(missing_ok=True)
        return

    # Save to codebase/chat_sessions
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = args.title.strip().replace(" ", "_")
    dest_file = CHAT_SESSIONS_DIR / f"{safe_title}_{timestamp}.txt"
    shutil.move(tmp_file, dest_file)
    print(f"✅ Chat saved to: {dest_file}")

    # Run file_chunker
    print("🔗 Chunking the chat file …")
    run_python(FILE_CHUNKER,
               "--input-file", dest_file,
               "--output-dir", CHUNKS_DIR,
               "--chunk-size", os.environ.get("DEFAULT_CHUNK_SIZE", "2000"),
               "--overlap", os.environ.get("DEFAULT_OVERLAP", "200"))

    # Run file_summarizer
    print("📝 Summarising chunks …")
    run_python(FILE_SUMMARIZER,
               "--input-dir", CHUNKS_DIR,
               "--output-dir", SUMMARIES_DIR)

    # Completion message
    print("\n🎉 RAG preprocessing complete!")
    print("Next: run mcp_helper.py to generate a structured prompt.")
    print(f"python3 {PYTHON_DIR / 'mcp_helper.py'} --template-file {os.environ.get('DEFAULT_TEMPLATE')} "
          f"--summaries-dir {SUMMARIES_DIR} --output-dir {os.environ.get('PROMPTS_DIR')}\n")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as err:
        print(f"❌ {err}")
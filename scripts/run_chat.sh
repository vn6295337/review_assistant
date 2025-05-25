#!/bin/bash
# run_chat.sh – one-click chat-to-prompt workflow
# Usage: ./run_chat.sh "Chat Title"

set -e

# ─── Load configuration ──────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/config.sh"        # config.sh lives in same folder
if [ ! -f "$CONFIG_FILE" ]; then
  echo "❌ config.sh not found at: $CONFIG_FILE"
  exit 1
fi
# shellcheck source=/dev/null
source "$CONFIG_FILE"                         # sets RAG_ROOT, PYTHON_DIR, etc.

# ─── Title (first CLI arg or default) ─────────────────────────────────
TITLE="${1:-Chat}"

echo "🚀  Starting RAG workflow for: $TITLE"
cd "$PYTHON_DIR"

# ─── 1. Chat ingestion via nano ──────────────────────────────────────
python3 chat_exporter.py --title "$TITLE"

# ─── 2. Identify newest chat file ────────────────────────────────────
LATEST_CHAT_FILE=$(ls -t "$CHAT_SESSIONS_DIR"/*.{md,txt,json} 2>/dev/null | head -n 1)
if [[ ! -f "$LATEST_CHAT_FILE" ]]; then
  echo "❌  No chat file found in $CHAT_SESSIONS_DIR . Aborting."
  exit 1
fi
echo "✅  Latest chat file: $LATEST_CHAT_FILE"

# ─── 3. Chunking ─────────────────────────────────────────────────────
echo "🔪  Chunking chat file…"
python3 "$PYTHON_DIR/file_chunker.py" \
        --input-file "$LATEST_CHAT_FILE" \
        --output-dir "$CHUNKS_DIR" \
        --chunk-size "$DEFAULT_CHUNK_SIZE" \
        --overlap "$DEFAULT_OVERLAP"

# ─── 4. Summarisation ────────────────────────────────────────────────
echo "🧠  Summarising chunks…"
python3 "$PYTHON_DIR/file_summarizer.py" \
        --input-dir "$CHUNKS_DIR" \
        --output-dir "$SUMMARIES_DIR"

# ─── 5. Prompt generation ────────────────────────────────────────────
echo "📝  Generating final MCP prompt…"
python3 "$PYTHON_DIR/mcp_helper.py" \
        --template-file "$DEFAULT_TEMPLATE" \
        --summaries-dir "$SUMMARIES_DIR" \
        --output-dir "$PROMPTS_DIR" \
        --title "$TITLE – $(date +%F)"

# ─── 6. Open newest prompt in nano ───────────────────────────────────
LATEST_PROMPT=$(ls -t "$PROMPTS_DIR"/*.txt 2>/dev/null | head -n 1)
if [[ -f "$LATEST_PROMPT" ]]; then
  echo "📂  Opening prompt in nano → $LATEST_PROMPT"
  nano "$LATEST_PROMPT"
else
  echo "⚠️  No prompt found in $PROMPTS_DIR"
fi

echo "✅  RAG workflow complete."

#!/usr/bin/env bash
set -euo pipefail

# ───────────────────────────────────────────────────────────
# debug.sh — RAG Directory & Script Checker
# ───────────────────────────────────────────────────────────

# Load central config
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

print_header() {
  echo -e "${CYAN}=== RAG Debug Checker ===${NC}"
  echo -e "Project root: ${GREEN}$RAG_ROOT${NC}"
  echo
}

check_dir() {
  local dir="$1"
  if [[ -d "$dir" ]]; then
    echo -e "${GREEN}✔ Directory exists:${NC} $dir"
    ls -la "$dir" 2>/dev/null | head -n10
  else
    echo -e "${RED}✖ Missing directory:${NC} $dir"
  fi
  echo
}

check_file() {
  local file="$1"
  if [[ -f "$file" ]]; then
    echo -e "${GREEN}✔ File exists:${NC} $file"
    echo "   Size: $(du -h "$file" | cut -f1)"
  else
    echo -e "${RED}✖ Missing file:${NC} $file"
  fi
  echo
}

# ───────────────────────────────────────────────────────────
# Main
# ───────────────────────────────────────────────────────────
print_header

echo -e "${YELLOW}-- Checking core directories --${NC}"
check_dir "$SCRIPTS_DIR"
check_dir "$TEMPLATES_DIR"
check_dir "$OUTPUTS_DIR"
check_dir "$CHUNKS_DIR"
check_dir "$SUMMARIES_DIR"
check_dir "$PROMPTS_DIR"
check_dir "$ROOT/codebase"

echo -e "${YELLOW}-- Checking core scripts --${NC}"
check_file "$SCRIPTS_DIR/rag_assistant.sh"
check_file "$PYTHON_DIR/file_chunker.py"
check_file "$PYTHON_DIR/file_summarizer.py"
check_file "$PYTHON_DIR/chunk_searcher.py"
check_file "$PYTHON_DIR/mcp_helper.py"

echo -e "${YELLOW}-- Checking template files --${NC}"
check_file "$TEMPLATES_DIR/summary_prompt_template.md"
check_file "$TEMPLATES_DIR/structured_prompt_template.md"

echo -e "${YELLOW}-- Scanning codebase for Python files --${NC}"
find "$ROOT/codebase" -type f -name "*.py" ! -path "*/venv/*" | while read -r f; do
  echo -e "${CYAN}•${NC} $f ($(du -h "$f" | cut -f1))"
done
echo

echo -e "${YELLOW}-- Inspecting rag_assistant.sh variables --${NC}"
if [[ -f "$SCRIPTS_DIR/rag_assistant.sh" ]]; then
  grep -E '^[A-Z_]+=.+' "$SCRIPTS_DIR/rag_assistant.sh" || true
  echo
  echo "Chunker invocation:"
  grep -n "file_chunker.py" "$SCRIPTS_DIR/rag_assistant.sh" -m3 || true
else
  echo -e "${RED}✖ rag_assistant.sh not found to inspect.${NC}"
fi
echo

echo -e "${GREEN}=== Debug complete ===${NC}"

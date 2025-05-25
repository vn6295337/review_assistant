#!/bin/bash

# rag_assistant.sh — Main entry point for RAG codebase assistant
# Usage:
#   ./scripts/rag_assistant.sh          # full mode
#   ./scripts/rag_assistant.sh --simple # simple mode

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Locate project root (one level above this script)
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CORE_DIR="$ROOT/python"
PY_DIR="$ROOT/python"
OUT_DIR="$ROOT/outputs/chunks"
SRC_DIR="$ROOT/codebase"

# === SIMPLE MODE ===
if [[ "$1" == "--simple" ]]; then
  echo -e "${BLUE}=== Simple RAG Mode ===${NC}"
  mkdir -p "$OUT_DIR"
  python3 "$CORE_DIR/file_chunker.py" "$SRC_DIR" --output "$OUT_DIR"
  python3 "$PY_DIR/simple_rag_assistant.py" --chunks-dir "$OUT_DIR"
  exit 0
fi

# === FULL MODE ===

echo -e "${BLUE}==============================================${NC}"
echo -e "${BLUE}       Codebase RAG Assistant Setup          ${NC}"
echo -e "${BLUE}==============================================${NC}"

echo -e "\n${YELLOW}Creating necessary directories...${NC}"
mkdir -p "$OUT_DIR"

# Check for file_chunker.py
if [ ! -f "$CORE_DIR/file_chunker.py" ]; then
  echo -e "${RED}Error: file_chunker.py not found in $CORE_DIR${NC}"
  exit 1
fi

# Check for rag_assistant.py
if [ ! -f "$PY_DIR/rag_assistant.py" ]; then
  echo -e "${RED}Error: rag_assistant.py not found in $PY_DIR${NC}"
  exit 1
fi

# Check codebase dir
if [ ! -d "$SRC_DIR" ]; then
  echo -e "${RED}Error: Codebase directory $SRC_DIR does not exist!${NC}"
  echo -e "Please create it and add your files."
  exit 1
fi

# Chunk the source files
echo -e "\n${YELLOW}Chunking files in $SRC_DIR...${NC}"
python3 "$CORE_DIR/file_chunker.py" "$SRC_DIR" --output "$OUT_DIR" --extensions .py,.js,.html,.css,.md,.txt --chunk-size 500 --overlap 50 --verbose
if [ $? -ne 0 ]; then
  echo -e "${RED}Error: File chunking failed!${NC}"
  exit 1
fi

NUM_CHUNKS=$(ls -1 "$OUT_DIR"/*.json 2>/dev/null | wc -l)
if [ "$NUM_CHUNKS" -eq 0 ]; then
  echo -e "${RED}Error: No chunks were created!${NC}"
  exit 1
fi
echo -e "${GREEN}Successfully created $NUM_CHUNKS chunks!${NC}"

# Dependency checks
echo -e "\n${YELLOW}Checking Python dependencies...${NC}"
for pkg in numpy sentence_transformers; do
  python3 -c "import $pkg" 2>/dev/null || {
    echo -e "${RED}Missing Python package: $pkg${NC}"
    echo -e "Install with: python3 -m pip install $pkg"
    exit 1
  }
done

# Python env info
echo -e "\n${YELLOW}Python environment:${NC}"
echo -e "Python: $(which python3)"
echo -e "Python version: $(python3 --version)"

# Launch assistant
echo -e "\n${YELLOW}Starting RAG Assistant...${NC}"
python3 "$PY_DIR/rag_assistant.py" --chunks-dir "$OUT_DIR"

echo -e "\n${GREEN}RAG Assistant session ended.${NC}"

#!/usr/bin/env bash
set -euo pipefail

# ───────────────────────────────────────────────────────────
# rag_menu.sh — Interactive RAG Helper Menu
# ───────────────────────────────────────────────────────────

# Load central config
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'  # No Color

show_menu() {
  clear
  echo -e "${CYAN}=== RAG Helper Tools ===${NC}"
  echo "1) Search chunks"
  echo "2) Multi-chunk prompts"
  echo "3) Exit"
  echo
  echo -n "Enter choice [1-3]: "
}

pause() {
  echo -e "\n${YELLOW}Press any key to continue...${NC}"
  read -n1 -r
}

search_chunks() {
  echo -n "Enter search query: "
  read -r QUERY
  if [[ -z "$QUERY" ]]; then
    echo -e "${RED}Query cannot be empty${NC}"
    return
  fi
  echo -e "${CYAN}Searching for:${NC} $QUERY"
  python3 "$PYTHON_DIR/chunk_searcher.py" search \
    --chunks-dir "$CHUNKS_DIR" \
    --query "$QUERY" \
    --limit 10
  pause
}

list_prompts() {
  python3 "$PYTHON_DIR/mcp_helper.py" list --dir "$MCP_DATA_DIR"
}

create_prompt() {
  echo -n "New prompt name: "
  read -r NAME
  [[ -z "$NAME" ]] && { echo -e "${RED}Name cannot be empty${NC}"; return; }
  python3 "$PYTHON_DIR/mcp_helper.py" create "$NAME" --dir "$MCP_DATA_DIR"
  pause
}

add_context() {
  echo "Available prompts:"; list_prompts
  echo -n "Prompt name to add context: "
  read -r NAME
  [[ -z "$NAME" ]] && { echo -e "${RED}Name cannot be empty${NC}"; return; }
  echo -n "Search chunks query: "
  read -r QUERY
  [[ -z "$QUERY" ]] && { echo -e "${RED}Query cannot be empty${NC}"; return; }
  python3 "$PYTHON_DIR/chunk_searcher.py" search --chunks-dir "$CHUNKS_DIR" --query "$QUERY" --limit 5
  echo -n "Path of chunk to add: "
  read -r CHUNK_PATH
  [[ -z "$CHUNK_PATH" ]] && { echo "Cancelled"; return; }
  python3 "$PYTHON_DIR/mcp_helper.py" add-context "$NAME" "$CHUNK_PATH" --dir "$MCP_DATA_DIR"
  pause
}

generate_prompt() {
  echo "Available prompts:"; list_prompts
  echo -n "Prompt name to generate: "
  read -r NAME
  [[ -z "$NAME" ]] && { echo -e "${RED}Name cannot be empty${NC}"; return; }
  python3 "$PYTHON_DIR/mcp_helper.py" generate "$NAME" --dir "$MCP_DATA_DIR" --output "$PROMPTS_DIR"
  pause
}

export_prompt() {
  echo "Available prompts:"; list_prompts
  echo -n "Prompt name to export: "
  read -r NAME
  [[ -z "$NAME" ]] && { echo -e "${RED}Name cannot be empty${NC}"; return; }
  python3 "$PYTHON_DIR/mcp_helper.py" export "$NAME" --dir "$MCP_DATA_DIR" "$PROMPTS_DIR/$NAME.json"
  echo -e "${GREEN}Exported to $PROMPTS_DIR/$NAME.json${NC}"
  pause
}

import_prompt() {
  echo -n "Path to JSON to import: "
  read -r FILE
  [[ ! -f "$FILE" ]] && { echo -e "${RED}Invalid file${NC}"; return; }
  python3 "$PYTHON_DIR/mcp_helper.py" import "$FILE" --dir "$MCP_DATA_DIR"
  pause
}

mcp_help() {
  CMD=\${1:-}
  if [[ -z "$CMD" ]]; then
    python3 "$PYTHON_DIR/mcp_helper.py" -h
  else
    python3 "$PYTHON_DIR/mcp_helper.py" "$CMD" -h
  fi
  pause
}

# ───────────────────────────────────────────────────────────
# Main loop
# ───────────────────────────────────────────────────────────
while true; do
  show_menu
  read -r CHOICE
  case $CHOICE in
    1) search_chunks ;; 
    2)
      clear
      echo -e "${CYAN}=== Multi-chunk Prompts ===${NC}"
      echo "1) List prompts"
      echo "2) Create prompt"
      echo "3) Add context"
      echo "4) Generate"
      echo "5) Export"
      echo "6) Import"
      echo "7) Help"
      echo "8) Back"
      echo -n "Choice [1-8]: "
      read -r SUB
      case $SUB in
        1) list_prompts ;; 
        2) create_prompt ;; 
        3) add_context ;; 
        4) generate_prompt ;; 
        5) export_prompt ;; 
        6) import_prompt ;; 
        7) clear; echo "MCP Helper Commands:"; mcp_help; ;; 
        8) ;; 
        *) echo -e "${RED}Invalid${NC}"; pause ;; 
      esac
      ;;
    3) echo "${GREEN}Goodbye!${NC}"; exit 0 ;;
    *) echo -e "${RED}Invalid choice${NC}"; sleep 1 ;;
  esac
done

#!/bin/bash
set -euo pipefail

# === Configuration ===
EXPORT_DIR="/mnt/chromeos/removable/USB Drive/review_assistant/codebase/chat_sessions"
TMP_FILE="/tmp/claude_chat.txt"
ROOT_DIR="/mnt/chromeos/removable/USB Drive/review_assistant"
PYTHON_DIR="$ROOT_DIR/python"
CHUNKS_DIR="$ROOT_DIR/chunks"
SUMMARIES_DIR="$ROOT_DIR/outputs/summaries"

mkdir -p "$EXPORT_DIR" "$CHUNKS_DIR" "$SUMMARIES_DIR"

# === Colors for output ===
GREEN='\033[0;32m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# === Show user instructions ===
show_instructions() {
  echo -e "${CYAN}=== Claude Chat Exporter ===${NC}"
  echo "Save your Claude chat as text:"
  echo "1. Open a terminal text editor (e.g., nano)"
  echo "2. Paste copied chat into: $TMP_FILE"
  echo "3. Save and exit"
  echo
  echo "Press any key once ready..."
  read -n 1 -r
  echo
}

# === Prompt for export format with validation ===
prompt_export_format() {
  while true; do
    echo "Select export format:"
    echo "1) Markdown (recommended)"
    echo "2) Plain text"
    echo "3) JSON"
    read -r choice
    case "$choice" in
      1) echo "md"; return ;;
      2) echo "txt"; return ;;
      3) echo "json"; return ;;
      *)
        echo -e "${RED}Invalid choice, please enter 1, 2, or 3.${NC}"
        ;;
    esac
  done
}

# === Export chat in Markdown format ===
export_markdown() {
  local input_file="$1"
  local output_file="$2"
  local title="$3"

  {
    echo "# $title"
    echo "*Exported on: $(date)*"
    awk '{
      if ($0 ~ /^Human:/) {
        print "## Human\n"; $1=""; print $0 "\n";
      } else if ($0 ~ /^Claude:/) {
        print "## Claude\n"; $1=""; print $0 "\n---\n";
      } else {
        print $0;
      }
    }' "$input_file"
  } > "$output_file"
}

# === Export chat in JSON format (basic example) ===
export_json() {
  local input_file="$1"
  local output_file="$2"
  local title="$3"

  # Basic JSON array of messages with role and content extracted from lines starting with "Human:" or "Claude:"
  {
    echo "{"
    echo "  \"title\": \"$title\","
    echo "  \"messages\": ["
    awk '
      function json_escape(str) {
        gsub(/\\/,"\\\\",str)
        gsub(/"/,"\\\"",str)
        return str
      }
      /^Human:/ {
        sub(/^Human:[ ]*/, "")
        printf "    {\"role\": \"human\", \"content\": \"%s\"},\n", json_escape($0)
      }
      /^Claude:/ {
        sub(/^Claude:[ ]*/, "")
        printf "    {\"role\": \"claude\", \"content\": \"%s\"},\n", json_escape($0)
      }
    ' "$input_file" | sed '$ s/,$//'
    echo "  ]"
    echo "}"
  } > "$output_file"
}

# === Prompt yes/no question with validation ===
prompt_yes_no() {
  local prompt_msg="$1"
  while true; do
    echo -n "$prompt_msg (y/n): "
    read -r answer
    case "$answer" in
      [Yy]*) return 0 ;;
      [Nn]*) return 1 ;;
      *) echo -e "${RED}Please answer y or n.${NC}" ;;
    esac
  done
}

# === Process the chat export and optionally run RAG tools ===
process_file() {
  if [[ ! -f "$TMP_FILE" ]]; then
    echo -e "${RED}❌ Error: $TMP_FILE not found! Please save your chat to that file first.${NC}"
    exit 1
  fi

  echo "Enter a title for this chat (or press Enter for default):"
  read -r CHAT_TITLE
  CHAT_TITLE=${CHAT_TITLE:-"Claude Chat Export"}

  FORMAT=$(prompt_export_format)

  TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
  SAFE_TITLE=$(echo "$CHAT_TITLE" | tr -cd '[:alnum:] _-' | tr ' ' '_')
  OUTPUT_FILE="$EXPORT_DIR/${SAFE_TITLE}_${TIMESTAMP}.$FORMAT"

  echo -e "${CYAN}Processing chat export...${NC}"
  case "$FORMAT" in
    md)
      export_markdown "$TMP_FILE" "$OUTPUT_FILE" "$CHAT_TITLE"
      ;;
    json)
      export_json "$TMP_FILE" "$OUTPUT_FILE" "$CHAT_TITLE"
      ;;
    txt)
      {
        echo "$CHAT_TITLE"
        echo "Exported on: $(date)"
        echo
        cat "$TMP_FILE"
      } > "$OUTPUT_FILE"
      ;;
  esac

  echo -e "${GREEN}✅ Chat exported to: $OUTPUT_FILE${NC}"

  if prompt_yes_no "Do you want to process this file with your RAG tools?"; then
    echo -e "${CYAN}🚀 Running file_chunker.py...${NC}"
    python3 "$PYTHON_DIR/file_chunker.py" "$OUTPUT_FILE" --output "$CHUNKS_DIR"

    if prompt_yes_no "Do you want to generate summaries as well?"; then
      echo -e "${CYAN}📚 Running file_summarizer.py...${NC}"
      python3 "$PYTHON_DIR/file_summarizer.py" "$CHUNKS_DIR" --output "$SUMMARIES_DIR"
    fi

    echo -e "${GREEN}✅ Processing complete!${NC}"
  else
    echo "Skipping RAG processing."
  fi
}

# === Main script execution ===
clear
show_instructions
process_file

echo -e "${GREEN}🎉 Done! You can now use chunk_searcher.py and mcp_helper.py.${NC}"

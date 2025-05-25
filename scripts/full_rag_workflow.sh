#!/bin/bash
#
# full_rag_workflow.sh  ─  Orchestrates the complete local RAG pipeline
#
# Location   : review_assistant/scripts
# Depends on : review_assistant/scripts/config.sh
#

set -euo pipefail
trap 'echo -e "\033[0;31m❌ Workflow aborted (${BASH_SOURCE[1]}:${LINENO})\033[0m"' ERR

# ───────────────────────────────────────────────────────────
# 1. Load central configuration
# ───────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/config.sh"

# ───────────────────────────────────────────────────────────
# 2. Colours for pretty output
# ───────────────────────────────────────────────────────────
GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; NC='\033[0m' # No colour / reset

# ───────────────────────────────────────────────────────────
# 3. Banner
# ───────────────────────────────────────────────────────────
echo -e "\n${BLUE}======================================================${NC}"
echo -e "${BLUE}  Running Full RAG Workflow${NC}"
echo -e "${BLUE}======================================================${NC}\n"

# ───────────────────────────────────────────────────────────
# 4. First‑run sanity checks
# ───────────────────────────────────────────────────────────
for dir in "$PYTHON_DIR" "$CHUNKS_DIR" "$SUMMARIES_DIR" "$PROMPTS_DIR"; do
  if [[ ! -d "$dir" ]]; then
    echo -e "${YELLOW}Creating missing directory:${NC} $dir"
    mkdir -p "$dir"
  fi
done

# Ensure we have at least a fallback prompt template
if [[ ! -f "$DEFAULT_TEMPLATE" ]]; then
  echo -e "${YELLOW}Creating fallback template at:${NC} $DEFAULT_TEMPLATE"
  mkdir -p "$(dirname "$DEFAULT_TEMPLATE")"
  cat > "$DEFAULT_TEMPLATE" <<'EOL'
# {title}

## Context Information
{summaries}

## Tasks
1. High‑level overview  
2. Key insights  
3. Issues / risks  
4. Recommended next steps  
EOL
fi

# ───────────────────────────────────────────────────────────
# 5.  STEP 1 – Chunk files
# ───────────────────────────────────────────────────────────
echo -e "${BLUE}Step 1 • Checking for chunks…${NC}"
chunk_count=$(find "$CHUNKS_DIR" -type f -name "*.json" | wc -l)

if [[ "$chunk_count" -eq 0 ]]; then
  echo -e "${YELLOW}No chunks found in ${CHUNKS_DIR}${NC}"
  read -rp "$(echo -e "${BLUE}Create chunks from a source file? (y/n) ${NC}")" create_chunks
  if [[ "$create_chunks" =~ ^[Yy]$ ]]; then
    read -rp "$(echo -e "${BLUE}Path to source file: ${NC}")" source_file
    [[ -f "$source_file" ]] || { echo -e "${RED}Source file not found${NC}"; exit 1; }

    echo -e "${BLUE}Choose chunk size:${NC}
    1)  500 chars  (code/very technical)
    2) 2000 chars  (balanced)   [default]
    3) 4000 chars  (narrative)\n"
    read -rp "Selection: " sz
    case "$sz" in
      1) chunk_size=500 ; overlap=50  ;;
      3) chunk_size=4000; overlap=400 ;;
      *) chunk_size=$DEFAULT_CHUNK_SIZE ; overlap=$DEFAULT_OVERLAP ;;
    esac

    echo -e "${GREEN}→ Chunking with size $chunk_size / overlap $overlap…${NC}"
    python3 "${PYTHON_DIR}/file_chunker.py" \
        --input-file "$source_file" \
        --output-dir "$CHUNKS_DIR" \
        --chunk-size "$chunk_size" \
        --overlap "$overlap" \
        --verbose
  else
    echo -e "${RED}No chunks – aborting workflow.${NC}"
    exit 0
  fi
fi

# Re‑count after possible creation
chunk_count=$(find "$CHUNKS_DIR" -type f -name "*.json" | wc -l)
echo -e "${GREEN}✓ Found $chunk_count chunk files${NC}"

# ───────────────────────────────────────────────────────────
# 6.  STEP 2 – Summaries
# ───────────────────────────────────────────────────────────
echo -e "\n${BLUE}Step 2 • Generating summaries…${NC}"

summary_count=$(find "$SUMMARIES_DIR" -type f -name "summary_*.json" | wc -l)
if [[ "$summary_count" -gt 0 ]]; then
  read -rp "$(echo -e "${BLUE}$summary_count summaries exist. Re‑generate all? (y/n) ${NC}")" regen
  if [[ "$regen" =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Deleting old summaries…${NC}"
    rm -f "${SUMMARIES_DIR}"/summary_*.json
  fi
fi

echo -e "${GREEN}→ Running summariser…${NC}"
python3 "${PYTHON_DIR}/file_summarizer.py" \
    --input-dir "$CHUNKS_DIR" \
    --output-dir "$SUMMARIES_DIR" \
    --skip-existing \
    --verbose

# ───────────────────────────────────────────────────────────
# 7.  STEP 3 – Build master prompt
# ───────────────────────────────────────────────────────────
echo -e "\n${BLUE}Step 3 • Building master prompt…${NC}"
read -rp "$(echo -e "${BLUE}Title for this review [enter for default]: ${NC}")" review_title
review_title=${review_title:-"Content Analysis $(date +%Y-%m-%d)"}

python3 "${PYTHON_DIR}/mcp_helper.py" \
    --summaries-dir "$SUMMARIES_DIR" \
    --template-file "$DEFAULT_TEMPLATE" \
    --output-dir "$PROMPTS_DIR" \
    --title "$review_title"

# ───────────────────────────────────────────────────────────
# 8.  STEP 4 – Offer post‑prompt actions
# ───────────────────────────────────────────────────────────
latest_prompt=$(find "$PROMPTS_DIR" -type f -name "summary_prompt_*.txt" -printf "%T@ %p\n" \
                | sort -nr | head -1 | cut -d' ' -f2-)

if [[ -n "$latest_prompt" ]]; then
  echo -e "\n${GREEN}✓ Prompt generated:${NC} $latest_prompt\n"
  echo -e "${BLUE}Choose an action:${NC}
  1) View in terminal
  2) Copy to clipboard
  3) Open in nano/vim
  4) Exit"
  read -rp "Selection: " act
  case "$act" in
    1) cat "$latest_prompt" ;;
    2) if command -v xclip >/dev/null 2>&1; then
         xclip -selection clipboard < "$latest_prompt"
         echo -e "${GREEN}Copied to clipboard.${NC}"
       else
         echo -e "${RED}xclip not found; displaying instead.${NC}"
         cat "$latest_prompt"
       fi ;;
    3) ${EDITOR:-nano} "$latest_prompt" ;;
    *) ;;  # nothing
  esac
else
  echo -e "${RED}❌ Prompt generation failed.${NC}"
  exit 1
fi

# ───────────────────────────────────────────────────────────
# 9.  Wrap‑up
# ───────────────────────────────────────────────────────────
echo -e "\n${BLUE}======================================================${NC}"
echo -e "${GREEN}  RAG Workflow Complete${NC}"
echo -e "${BLUE}======================================================${NC}\n"
echo -e "${YELLOW}Next steps:${NC}
• Paste the prompt into ChatGPT, Claude, or Gemini.
• To search chunks interactively, run:  bash ${SCRIPTS_DIR}/rag_assistant.sh\n"

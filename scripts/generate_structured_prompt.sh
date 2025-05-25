#!/usr/bin/env bash
set -euo pipefail

# ───────────────────────────────────────────────────────────
# generated_structured_prompt.sh ─ Build a structured prompt
# ───────────────────────────────────────────────────────────

# Load central config
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

# ───────────────────────────────────────────────────────────
# 1. Find latest summary
# ───────────────────────────────────────────────────────────
find_latest_summary() {
  local latest
  latest=$(ls -1t "$SUMMARIES_DIR"/summary_*.json 2>/dev/null | head -n1 || true)
  if [[ -z "$latest" ]]; then
    echo -e "${RED}❌ No summary file found in $SUMMARIES_DIR${NC}" >&2
    exit 1
  fi
  echo "$latest"
}

# ───────────────────────────────────────────────────────────
# 2. Prompt user for fields
# ───────────────────────────────────────────────────────────
prompt_input() {
  local var_name=$1
  local prompt_msg=$2
  local default=$3
  local input

  read -rp "$prompt_msg" input
  # If user just presses Enter and default exists, use it
  if [[ -z "$input" && -n "$default" ]]; then
    input="$default"
  fi
  printf '%s' "$input"
}

# ───────────────────────────────────────────────────────────
# 3. Generate the structured prompt
# ───────────────────────────────────────────────────────────
generate_prompt() {
  local summary_file=$1
  local title=$2
  local question=$3
  local notes=$4
  local conclusion=$5

  echo -e "${CYAN}🛠 Generating prompt using summary:${NC} $summary_file"

  python3 "$MCP_HELPER" \
    --summaries-dir "$SUMMARIES_DIR" \
    --template-file "$TEMPLATE" \
    --output-dir "$(dirname "$PROMPT_OUT")" \
    --title "$title" \
    --var question="$question" \
    --var notes="$notes" \
    --var conclusion="$conclusion"
}

# ───────────────────────────────────────────────────────────
#             Main Script Execution
# ───────────────────────────────────────────────────────────

latest_summary=$(find_latest_summary)

echo
title=$(prompt_input TITLE "Enter prompt title [default: Structured Review]: " "Structured Review")
echo
question=$(prompt_input QUESTION "Enter your main question: " "")
echo
notes=$(prompt_input NOTES "Enter any notes (or leave blank): " "")
echo
conclusion=$(prompt_input CONCLUSION "Enter a final comment or conclusion: " "")

generate_prompt "$latest_summary" "$title" "$question" "$notes" "$conclusion"

# ───────────────────────────────────────────────────────────
# 4. Display result
# ───────────────────────────────────────────────────────────
if [[ -f "$PROMPT_OUT" ]]; then
  echo -e "\n${GREEN}✅ Prompt saved to: $PROMPT_OUT${NC}"
  echo -e "\n${CYAN}Preview (first 30 lines):${NC}\n"
  head -n30 "$PROMPT_OUT"
else
  echo -e "${RED}❌ Failed to create prompt.${NC}"
  exit 1
fi

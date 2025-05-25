#!/bin/bash
# config.sh - Central configuration for RAG Assistant

# === Base directories ===
export RAG_ROOT="/mnt/chromeos/removable/USB Drive/review_assistant"
export PYTHON_DIR="${RAG_ROOT}/python"
export SCRIPTS_DIR="${RAG_ROOT}/scripts"
export TEMPLATES_DIR="${RAG_ROOT}/templates"
export OUTPUTS_DIR="${RAG_ROOT}/outputs"

# === Output subdirectories ===
export CHUNKS_DIR="${OUTPUTS_DIR}/chunks"
export SUMMARIES_DIR="${OUTPUTS_DIR}/summaries"
export PROMPTS_DIR="${OUTPUTS_DIR}/prompts"
export MCP_DATA_DIR="${OUTPUTS_DIR}/mcp_data"

# === Input directory for raw chats ===
export CHAT_SESSIONS_DIR="${RAG_ROOT}/codebase/chat_sessions"

# === Default settings ===
export DEFAULT_CHUNK_SIZE=2000
export DEFAULT_OVERLAP=200
export DEFAULT_TEMPLATE="${TEMPLATES_DIR}/summary_prompt_template.md"

# === Secret key for auth.py ===
export SECRET_KEY="${SECRET_KEY:-development-secret-key}"

# === Create directories if they don't exist ===
for dir in "$CHUNKS_DIR" "$SUMMARIES_DIR" "$PROMPTS_DIR" "$MCP_DATA_DIR" "$TEMPLATES_DIR" "$CHAT_SESSIONS_DIR"; do
  [ -d "$dir" ] || mkdir -p "$dir"
done

# === Function to print configuration ===
print_config() {
  echo "RAG Assistant Configuration:"
  echo "-----------------------------"
  echo "RAG_ROOT         = $RAG_ROOT"
  echo "PYTHON_DIR       = $PYTHON_DIR"
  echo "SCRIPTS_DIR      = $SCRIPTS_DIR"
  echo "TEMPLATES_DIR    = $TEMPLATES_DIR"
  echo "OUTPUTS_DIR      = $OUTPUTS_DIR"
  echo
  echo "CHUNKS_DIR       = $CHUNKS_DIR"
  echo "SUMMARIES_DIR    = $SUMMARIES_DIR"
  echo "PROMPTS_DIR      = $PROMPTS_DIR"
  echo "MCP_DATA_DIR     = $MCP_DATA_DIR"
  echo
  echo "DEFAULT_CHUNK_SIZE= $DEFAULT_CHUNK_SIZE"
  echo "DEFAULT_OVERLAP  = $DEFAULT_OVERLAP"
  echo "DEFAULT_TEMPLATE = $DEFAULT_TEMPLATE"
  echo
  echo "SECRET_KEY       = $SECRET_KEY"
  echo "-----------------------------"
}

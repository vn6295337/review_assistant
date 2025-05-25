#!/bin/bash
# rag_helper.sh - Helper utilities for the RAG Assistant system
# This script provides helper functions for working with the local file-based
# RAG pipeline, including file management, pipeline shortcuts, and 
# context assembly.

set -e  # Exit immediately if a command exits with a non-zero status

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
CHUNKS_DIR="$ROOT_DIR/outputs/chunks"
SUMMARIES_DIR="$ROOT_DIR/outputs/summaries"
PROMPTS_DIR="$ROOT_DIR/prompts"
LOG_FILE="$ROOT_DIR/logs/rag_helper.log"

# Create directories if they don't exist
mkdir -p "$CHUNKS_DIR" "$SUMMARIES_DIR" "$PROMPTS_DIR" "$(dirname "$LOG_FILE")"

# Logging function
log() {
  local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
  echo "$msg" | tee -a "$LOG_FILE"
}

# Help message
show_help() {
  cat << EOF
RAG Helper Script - Utilities for the local RAG pipeline

Usage: $(basename "$0") [OPTIONS] COMMAND [ARGS]

Commands:
  check                 Check and verify the RAG environment
  clean [--all]         Clean temporary files (--all includes outputs)
  stats                 Show statistics about chunks and summaries
  combine FILE1 FILE2   Combine multiple chunk files into single context
  extract TYPE PATH     Extract key information from file (types: code, doc, summary)
  regen PATH            Regenerate chunks and summaries for a file
  optimize FILE         Optimize a file for context window efficiency
  help                  Show this help message

Examples:
  $(basename "$0") check
  $(basename "$0") clean
  $(basename "$0") stats
  $(basename "$0") combine chunk_1.txt chunk_2.txt > combined.txt
  $(basename "$0") extract code ./my_script.py

EOF
}

# Check RAG environment
check_environment() {
  log "Checking RAG environment..."
  
  # Check for core Python scripts
  CORE_FILES=(
    "$ROOT_DIR/core/file_chunker.py"
    "$ROOT_DIR/core/file_summarizer.py" 
    "$ROOT_DIR/core/chunk_searcher.py"
    "$ROOT_DIR/core/mcp_helper.py"
    "$ROOT_DIR/scripts/rag_assistant.sh"
  )
  
  missing=0
  for file in "${CORE_FILES[@]}"; do
    if [[ ! -f "$file" ]]; then
      echo "❌ Missing core file: $file"
      missing=$((missing + 1))
    fi
  done
  
  # Check for Python environment
  if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found"
    missing=$((missing + 1))
  else
    python_version=$(python3 --version)
    echo "✅ $python_version found"
  fi
  
  # Check directory structure
  for dir in "$CHUNKS_DIR" "$SUMMARIES_DIR" "$PROMPTS_DIR"; do
    if [[ -d "$dir" ]]; then
      echo "✅ Directory exists: $(basename "$dir")"
    else
      echo "❌ Missing directory: $(basename "$dir")"
      missing=$((missing + 1))
    fi
  done
  
  if [[ $missing -eq 0 ]]; then
    echo "✅ RAG environment check passed."
  else
    echo "❌ RAG environment check failed with $missing issues."
    return 1
  fi
}

# Clean temporary files
clean_temp_files() {
  log "Cleaning temporary files..."
  
  # Always clean these temporary files
  find "$ROOT_DIR" -type f -name "*.pyc" -delete
  find "$ROOT_DIR" -type f -name "*.tmp" -delete
  find "$ROOT_DIR" -type f -name "*.temp" -delete
  find "$ROOT_DIR" -type f -name "*~" -delete
  find "$ROOT_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
  
  echo "✅ Temporary files cleaned."
  
  # Clean outputs if requested
  if [[ "$1" == "--all" ]]; then
    log "Cleaning all output files..."
    rm -rf "${CHUNKS_DIR:?}"/* 2>/dev/null || true
    rm -rf "${SUMMARIES_DIR:?}"/* 2>/dev/null || true
    echo "✅ All output files cleaned."
  fi
}

# Show statistics
show_stats() {
  log "Gathering statistics..."
  
  # Count chunks and summaries
  chunk_count=$(find "$CHUNKS_DIR" -type f | wc -l)
  summary_count=$(find "$SUMMARIES_DIR" -type f | wc -l)
  total_size=$(du -sh "$ROOT_DIR" | awk '{print $1}')
  
  # Find largest files
  echo "RAG Assistant Statistics:"
  echo "------------------------"
  echo "Total chunks: $chunk_count"
  echo "Total summaries: $summary_count"
  echo "Total project size: $total_size"
  
  echo -e "\nLargest chunks:"
  find "$CHUNKS_DIR" -type f -exec du -h {} \; | sort -hr | head -5
  
  echo -e "\nMost recent activity:"
  find "$ROOT_DIR" -type f -not -path "*/\.*" -mtime -7 | head -5
}

# Combine chunks
combine_chunks() {
  if [[ $# -lt 2 ]]; then
    echo "Error: Please provide at least two files to combine"
    return 1
  fi
  
  log "Combining chunks: $*"
  
  echo "### Combined Context ###"
  echo "# Generated on $(date)"
  echo "# Files: $*"
  echo "########################"
  echo ""
  
  # Combine all provided files with separators
  for file in "$@"; do
    if [[ -f "$file" ]]; then
      echo -e "\n--- BEGIN: $(basename "$file") ---\n"
      cat "$file"
      echo -e "\n--- END: $(basename "$file") ---\n"
    else
      echo "Warning: File not found: $file"
    fi
  done
}

# Extract information from file
extract_info() {
  local type="$1"
  local path="$2"
  
  if [[ ! -f "$path" ]]; then
    echo "Error: File not found: $path"
    return 1
  fi
  
  log "Extracting $type information from $path"
  
  case "$type" in
    code)
      # Extract function definitions and class definitions
      if [[ "$path" == *.py ]]; then
        echo "# Python definitions in $path"
        grep -n "^def \|^class " "$path" || echo "No definitions found"
      elif [[ "$path" == *.sh ]]; then
        echo "# Shell functions in $path"
        grep -n "^function\|() {" "$path" || echo "No functions found"
      else
        echo "# First 20 lines of $path"
        head -20 "$path"
      fi
      ;;
    doc)
      # Extract docstrings or comments
      if [[ "$path" == *.py ]]; then
        echo "# Documentation in $path"
        grep -n '"""' "$path" -A 1 || echo "No docstrings found"
      else
        echo "# Comments in $path"
        grep -n "^#" "$path" | head -20 || echo "No comments found"
      fi
      ;;
    summary)
      # Generate a quick summary using file_summarizer.py
      if [[ -f "$ROOT_DIR/core/file_summarizer.py" ]]; then
        python3 "$ROOT_DIR/core/file_summarizer.py" "$path" --quick
      else
        echo "Error: file_summarizer.py not found"
        return 1
      fi
      ;;
    *)
      echo "Error: Unknown extraction type. Use code, doc, or summary."
      return 1
      ;;
  esac
}

# Regenerate chunks and summaries
regenerate_file() {
  local path="$1"
  
  if [[ ! -f "$path" ]]; then
    echo "Error: File not found: $path"
    return 1
  fi
  
  log "Regenerating chunks and summaries for $path"
  
  # Check if the core scripts exist
  if [[ ! -f "$ROOT_DIR/core/file_chunker.py" || ! -f "$ROOT_DIR/core/file_summarizer.py" ]]; then
    echo "Error: Core RAG scripts not found"
    return 1
  fi
  
  # Run chunking and summarization
  echo "Chunking file..."
  python3 "$ROOT_DIR/core/file_chunker.py" "$path" --output-dir "$CHUNKS_DIR"
  
  echo "Creating summary..."
  python3 "$ROOT_DIR/core/file_summarizer.py" "$path" --output-dir "$SUMMARIES_DIR"
  
  echo "✅ Regeneration complete for $path"
}

# Optimize a file for context window efficiency
optimize_file() {
  local path="$1"
  
  if [[ ! -f "$path" ]]; then
    echo "Error: File not found: $path"
    return 1
  fi
  
  log "Optimizing $path for context window efficiency"
  
  # Get file extension
  ext="${path##*.}"
  
  # Create backup
  cp "$path" "${path}.bak"
  echo "✅ Created backup at ${path}.bak"
  
  case "$ext" in
    py)
      # Remove unnecessary whitespace and comments
      echo "Optimizing Python file..."
      # Remove blank lines and simplify whitespace
      sed -i '/^[[:space:]]*$/d' "$path"
      # Remove comments that are on their own line (not docstrings)
      sed -i '/^[[:space:]]*#/d' "$path"
      ;;
    sh)
      # Optimize shell scripts
      echo "Optimizing shell script..."
      # Remove blank lines and comments
      sed -i '/^[[:space:]]*$/d; /^[[:space:]]*#[^!]/d' "$path"
      ;;
    md|txt)
      # Optimize markdown/text
      echo "Optimizing text file..."
      # Remove excess blank lines (keep only single blank lines)
      sed -i '/^$/N;/^\n$/D' "$path"
      ;;
    *)
      echo "Warning: Unknown file type for optimization. Basic cleanup only."
      sed -i '/^[[:space:]]*$/d' "$path"
      ;;
  esac
  
  # Calculate space savings
  original_size=$(wc -c < "${path}.bak")
  new_size=$(wc -c < "$path")
  saved=$(( original_size - new_size ))
  percent=$(( saved * 100 / original_size ))
  
  echo "✅ Optimization complete"
  echo "Original size: $original_size bytes"
  echo "New size: $new_size bytes"
  echo "Saved: $saved bytes ($percent%)"
}

# Main function to parse arguments and call appropriate function
main() {
  # No arguments provided
  if [[ $# -eq 0 ]]; then
    show_help
    exit 0
  fi

  # Parse command
  cmd="$1"
  shift
  
  case "$cmd" in
    check)
      check_environment
      ;;
    clean)
      clean_temp_files "$1"
      ;;
    stats)
      show_stats
      ;;
    combine)
      combine_chunks "$@"
      ;;
    extract)
      if [[ $# -lt 2 ]]; then
        echo "Error: extract requires TYPE and PATH arguments"
        return 1
      fi
      extract_info "$1" "$2"
      ;;
    regen)
      if [[ $# -lt 1 ]]; then
        echo "Error: regen requires a PATH argument"
        return 1
      fi
      regenerate_file "$1"
      ;;
    optimize)
      if [[ $# -lt 1 ]]; then
        echo "Error: optimize requires a FILE argument"
        return 1
      fi
      optimize_file "$1"
      ;;
    help)
      show_help
      ;;
    *)
      echo "Error: Unknown command '$cmd'"
      show_help
      exit 1
      ;;
  esac
}

# Run main function
main "$@"

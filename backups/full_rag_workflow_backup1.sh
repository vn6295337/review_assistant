#!/bin/bash
# full_rag_workflow.sh - Improved RAG workflow for generating summaries and prompt templates

# Define directories
ROOT_DIR="/mnt/chromeos/removable/USB Drive/review_assistant"
PY_DIR="$ROOT_DIR/python"
TEMPLATES_DIR="$ROOT_DIR/templates"
SUMMARY_DIR="$ROOT_DIR/outputs/summaries"
CHUNKS_RAW="$ROOT_DIR/chunks"
CHUNKS_OUT="$ROOT_DIR/outputs/chunks"
PROMPTS_DIR="$ROOT_DIR/outputs/prompts"

# Create necessary directories if they don't exist
mkdir -p "$ROOT_DIR"
mkdir -p "$PY_DIR"
mkdir -p "$TEMPLATES_DIR"
mkdir -p "$SUMMARY_DIR"
mkdir -p "$CHUNKS_RAW"
mkdir -p "$CHUNKS_OUT"
mkdir -p "$PROMPTS_DIR"

# Ensure proper error handling
set -e
set -o pipefail

# Check if required executables exist
command -v python3 >/dev/null 2>&1 || { echo "Python 3 is required but not installed. Aborting."; exit 1; }

# Timestamp for output files
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Process input source (file or directory)
if [ $# -eq 0 ]; then
    echo "No input source provided. Creating a temporary file."
    TMP_CHAT="/tmp/claude_chat.txt"
    if [ ! -f "$TMP_CHAT" ]; then
        echo "Creating sample file at $TMP_CHAT"
        cat > "$TMP_CHAT" << EOF
This is a sample chat content for testing the RAG workflow.
EOF
    fi
    SOURCE="$TMP_CHAT"
else
    SOURCE="$1"
fi

echo "Using source: $SOURCE"

# Step 1: Chunk the content
echo "Step 1: Chunking content..."
if [ -f "$SOURCE" ]; then
    python3 "$PY_DIR/file_chunker.py" "$SOURCE" --output "$CHUNKS_RAW"
elif [ -d "$SOURCE" ]; then
    find "$SOURCE" -type f -name "*.txt" -o -name "*.md" -o -name "*.py" | while read file; do
        python3 "$PY_DIR/file_chunker.py" "$file" --output "$CHUNKS_RAW"
    done
else
    echo "Error: Source is neither a file nor a directory"
    exit 1
fi

# Step 2: Generate summaries for each chunk
echo "Step 2: Generating summaries..."
python3 "$PY_DIR/file_summarizer.py" "$CHUNKS_RAW" --output "$SUMMARY_DIR"

# Step 3: Find the latest summary file (most recently modified)
LATEST_SUMMARY=$(find "$SUMMARY_DIR" -type f -name "summary_*.json" -printf "%T@ %p\n" | sort -n | tail -1 | cut -f2- -d" ")

if [ -z "$LATEST_SUMMARY" ]; then
    echo "Error: No summary files found"
    exit 1
fi

echo "Using latest summary: $LATEST_SUMMARY"

# Step 4: Use the summary to generate a prompt template
echo "Step 4: Generating prompt template..."

# Create a template if it doesn't exist
if [ ! -f "$TEMPLATES_DIR/summary_prompt_template.md" ]; then
    cat > "$TEMPLATES_DIR/summary_prompt_template.md" << EOF
# Summary Prompt

## Title

{{title}}

## Context Summary

{{summary}}

## Instructions

Please generate a concise summary of the main ideas, key points, and recommendations. Keep it actionable and clear.
EOF
fi

# Generate the prompt using the template and summary
python3 "$PY_DIR/mcp_helper.py" create \
    --template "$TEMPLATES_DIR/summary_prompt_template.md" \
    --output "$PROMPTS_DIR/summary_prompt_${TIMESTAMP}.txt" \
    --var "title=Chat Review ${TIMESTAMP}" \
    --context-file "$LATEST_SUMMARY" summary

echo "Workflow complete!"
echo "Generated prompt at: $PROMPTS_DIR/summary_prompt_${TIMESTAMP}.txt"

# Display the generated prompt (optional)
echo "Preview of generated prompt:"
head -n 20 "$PROMPTS_DIR/summary_prompt_${TIMESTAMP}.txt"
echo "..."

exit 0

#!/bin/bash
#
# Full RAG Workflow Script
# This script orchestrates the complete RAG workflow for content processing
#

set -e  # Exit on any error

# Define paths
ROOT_DIR="/mnt/chromeos/removable/USB Drive/review_assistant"
PYTHON_DIR="${ROOT_DIR}/python"
CHUNKS_DIR="${ROOT_DIR}/chunks"
SUMMARIES_DIR="${ROOT_DIR}/outputs/summaries"
PROMPTS_DIR="${ROOT_DIR}/outputs/prompts"
TEMPLATE_FILE="${ROOT_DIR}/templates/summary_prompt_template.md"

# Print header
echo ""
echo "======================================================"
echo "  Running Full RAG Workflow"
echo "======================================================"
echo ""

# Check if all directories exist
for dir in "$ROOT_DIR" "$PYTHON_DIR" "$CHUNKS_DIR" "$SUMMARIES_DIR" "$PROMPTS_DIR"; do
  if [ ! -d "$dir" ]; then
    echo "❌ Directory does not exist: $dir"
    exit 1
  fi
done

# Check if template file exists
if [ ! -f "$TEMPLATE_FILE" ]; then
  echo "❌ Template file does not exist: $TEMPLATE_FILE"
  exit 1
fi

# Step 1: Check for JSON chunks
echo "Step 1: Checking for chunk files..."
chunk_count=$(find "$CHUNKS_DIR" -name "*.json" | wc -l)

if [ "$chunk_count" -eq 0 ]; then
  echo "⚠ No chunk files found in $CHUNKS_DIR"
  echo ""
  echo "Would you like to create chunks from a source file? (y/n)"
  read -r create_chunks
  
  if [ "$create_chunks" = "y" ]; then
    echo "Enter the path to your source file:"
    read -r source_file
    
    if [ ! -f "$source_file" ]; then
      echo "❌ Source file does not exist: $source_file"
      exit 1
    fi
    
    echo "Running file chunker..."
    python3 "${PYTHON_DIR}/file_chunker.py" \
      --input-file "$source_file" \
      --output-dir "$CHUNKS_DIR" \
      --chunk-size 2000 \
      --overlap 200 \
      --verbose
  else
    echo "Exiting workflow as no chunks are available."
    exit 0
  fi
else
  echo "✓ Found $chunk_count chunk files"
fi

# Step 2: Generate summaries
echo ""
echo "Step 2: Generating summaries..."

# Clean up existing summaries if needed
echo "Would you like to regenerate all summaries? (y/n)"
read -r regenerate_summaries

if [ "$regenerate_summaries" = "y" ]; then
  echo "Cleaning up existing summaries..."
  rm -f "${SUMMARIES_DIR}/summary_*.json"
fi

# Generate summaries for all chunks
python3 "${PYTHON_DIR}/file_summarizer.py" \
  --input-dir "$CHUNKS_DIR" \
  --output-dir "$SUMMARIES_DIR" \
  --verbose

# Step 3: Generate final prompt
echo ""
echo "Step 3: Generating master prompt..."

echo "Enter a title for this review (leave blank for auto-generated):"
read -r review_title

# Generate the prompt
if [ -z "$review_title" ]; then
  python3 "${PYTHON_DIR}/mcp_helper.py" \
    --summaries-dir "$SUMMARIES_DIR" \
    --template-file "$TEMPLATE_FILE" \
    --output-dir "$PROMPTS_DIR"
else
  python3 "${PYTHON_DIR}/mcp_helper.py" \
    --summaries-dir "$SUMMARIES_DIR" \
    --template-file "$TEMPLATE_FILE" \
    --output-dir "$PROMPTS_DIR" \
    --title "$review_title"
fi

# Step 4: Find the latest prompt file
latest_prompt=$(find "$PROMPTS_DIR" -name "summary_prompt_*.txt" -type f -printf "%T@ %p\n" | sort -nr | head -1 | cut -d' ' -f2-)

if [ -n "$latest_prompt" ]; then
  echo ""
  echo "✓ Workflow complete! Latest prompt available at:"
  echo "$latest_prompt"
  echo ""
  echo "You can now copy the content of this file to paste into an AI assistant."
  echo ""
  echo "Would you like to display the content of the prompt? (y/n)"
  read -r show_prompt
  
  if [ "$show_prompt" = "y" ]; then
    echo ""
    echo "============== PROMPT CONTENT ================"
    echo ""
    cat "$latest_prompt"
    echo ""
    echo "=============================================="
  fi
else
  echo ""
  echo "❌ No prompt file was generated. Please check for errors."
fi

echo ""
echo "======================================================"
echo "  RAG Workflow Complete"
echo "======================================================"
echo ""

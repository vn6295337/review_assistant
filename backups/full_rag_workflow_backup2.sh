#!/bin/bash
# full_rag_workflow.sh
# A complete RAG (Retrieval-Augmented Generation) workflow for local file processing
# This script chunks large files, generates summaries, and creates structured prompts
# for use with LLMs in resource-constrained environments

# Set up color formatting
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Define directories
ROOT_DIR="$(pwd)"
PYTHON_DIR="${ROOT_DIR}/python"
CHUNKS_DIR="${ROOT_DIR}/chunks"
SUMMARIES_DIR="${ROOT_DIR}/outputs/summaries"
PROMPTS_DIR="${ROOT_DIR}/outputs/prompts"
TEMPLATES_DIR="${ROOT_DIR}/templates"

# Check if file argument was provided
if [ "$#" -lt 1 ]; then
    echo -e "${RED}Error: No file specified${NC}"
    echo "Usage: $0 <file_to_process> [chunk_size] [chunk_overlap] [title]"
    echo "Example: $0 /path/to/large_file.txt 2000 200 \"My Document Analysis\""
    exit 1
fi

# Get arguments with defaults
FILE_PATH="$1"
CHUNK_SIZE="${2:-2000}"  # Default chunk size: 2000 characters
CHUNK_OVERLAP="${3:-200}" # Default chunk overlap: 200 characters
TITLE="${4:-""}"         # Default title: empty (will be auto-generated)

# Check if file exists
if [ ! -f "$FILE_PATH" ]; then
    echo -e "${RED}Error: File not found: $FILE_PATH${NC}"
    exit 1
fi

# Create directories if they don't exist
mkdir -p "$CHUNKS_DIR" "$SUMMARIES_DIR" "$PROMPTS_DIR"

# Step 1: Chunk the file
echo -e "\n${BLUE}Step 1: Chunking file${NC}"
echo -e "File: ${YELLOW}$FILE_PATH${NC}"
echo -e "Chunk size: ${YELLOW}$CHUNK_SIZE${NC} characters"
echo -e "Chunk overlap: ${YELLOW}$CHUNK_OVERLAP${NC} characters"

python3 "${PYTHON_DIR}/file_chunker.py" \
    --input-file "$FILE_PATH" \
    --output-dir "$CHUNKS_DIR" \
    --chunk-size "$CHUNK_SIZE" \
    --overlap "$CHUNK_OVERLAP" \
    --verbose

if [ $? -ne 0 ]; then
    echo -e "${RED}Error occurred during chunking step${NC}"
    exit 1
fi

# Step 2: Summarize chunks
echo -e "\n${BLUE}Step 2: Summarizing chunks${NC}"
python3 "${PYTHON_DIR}/file_summarizer.py" \
    --input-dir "$CHUNKS_DIR" \
    --output-dir "$SUMMARIES_DIR" \
    --verbose

if [ $? -ne 0 ]; then
    echo -e "${RED}Error occurred during summarization step${NC}"
    exit 1
fi

# Step 3: Create master context prompt
echo -e "\n${BLUE}Step 3: Creating master context prompt${NC}"

# Use filename as title if not provided
if [ -z "$TITLE" ]; then
    FILENAME=$(basename "$FILE_PATH")
    TITLE="Analysis of $FILENAME"
fi

python3 "${PYTHON_DIR}/mcp_helper.py" \
    --template "${TEMPLATES_DIR}/summary_prompt_template.md" \
    --summaries-dir "$SUMMARIES_DIR" \
    --output-dir "$PROMPTS_DIR" \
    --title "$TITLE" \
    --verbose

if [ $? -ne 0 ]; then
    echo -e "${RED}Error occurred during prompt creation step${NC}"
    exit 1
fi

# Success message
echo -e "\n${GREEN}RAG workflow completed successfully!${NC}"
echo -e "Your processed file is ready for LLM review."
echo -e "\nTo use the generated prompt:"
echo -e "1. Open your preferred LLM interface (ChatGPT, Claude, etc.)"
echo -e "2. Copy the content from the latest file in: ${YELLOW}$PROMPTS_DIR${NC}"
echo -e "3. Paste it to the LLM and await the response"

# Optional: Display the latest prompt file
LATEST_PROMPT=$(ls -t "$PROMPTS_DIR" | head -n 1)
if [ -n "$LATEST_PROMPT" ]; then
    echo -e "\nLatest prompt file: ${YELLOW}$PROMPTS_DIR/$LATEST_PROMPT${NC}"
    echo -e "View it with: ${BLUE}cat \"$PROMPTS_DIR/$LATEST_PROMPT\"${NC}"
fi

exit 0

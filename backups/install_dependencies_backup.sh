#!/bin/bash

# install_dependencies.sh - Script to install required Python packages for the RAG assistant

# Color output for better readability
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}==============================================${NC}"
echo -e "${BLUE}     Installing RAG Assistant Dependencies   ${NC}"
echo -e "${BLUE}==============================================${NC}"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}Error: pip3 not found. Please install Python and pip first.${NC}"
    exit 1
fi

# List of required packages
echo -e "\n${YELLOW}Installing required Python packages...${NC}"
python3 -m pip install --upgrade pip
python3 -m pip install numpy
python3 -m pip install sentence-transformers

# Verify installations
echo -e "\n${YELLOW}Verifying installations...${NC}"

# Check numpy
if python3 -c "import numpy" 2>/dev/null; then
    echo -e "${GREEN}numpy installed successfully${NC}"
else
    echo -e "${RED}Failed to install numpy${NC}"
fi

# Check sentence-transformers
if python3 -c "import sentence_transformers" 2>/dev/null; then
    echo -e "${GREEN}sentence-transformers installed successfully${NC}"
else
    echo -e "${RED}Failed to install sentence-transformers${NC}"
    echo -e "${YELLOW}Note: If you're on a Chromebook or restricted environment, you may need admin privileges${NC}"
fi

echo -e "\n${GREEN}Installation process completed!${NC}"
echo -e "${BLUE}You can now run ./rag_assistant.sh to start the RAG Assistant${NC}"

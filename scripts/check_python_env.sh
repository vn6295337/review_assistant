#!/bin/bash

# check_python_env.sh - Script to check Python environment and path settings

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

print_header() {
  echo -e "${BLUE}==============================================${NC}"
  echo -e "${BLUE}       Checking Python Environment           ${NC}"
  echo -e "${BLUE}==============================================${NC}"
}

print_footer() {
  echo -e "${BLUE}==============================================${NC}"
  echo -e "${BLUE}       Environment Check Complete             ${NC}"
  echo -e "${BLUE}==============================================${NC}"
}

check_package_installed() {
  local pkg=$1
  echo -e "\n${YELLOW}Checking for $pkg:${NC}"
  if python3 -m pip list | grep -q "$pkg"; then
    echo -e "${GREEN}$pkg is installed${NC}"
  else
    echo -e "${RED}$pkg not found in pip list${NC}"
  fi
}

test_import() {
  local module=$1
  echo -n "$module: "
  if python3 -c "import $module; print('OK')" 2>/dev/null; then
    echo -e "${GREEN}Available${NC}"
    return 0
  else
    echo -e "${RED}Not available${NC}"
    return 1
  fi
}

print_header

echo -e "\n${YELLOW}Python version:${NC}"
python3 --version

echo -e "\n${YELLOW}Python path:${NC}"
which python3

echo -e "\n${YELLOW}Pip path:${NC}"
which pip3

echo -e "\n${YELLOW}PYTHONPATH environment variable:${NC}"
echo "${PYTHONPATH:-<not set>}"

# Check packages
check_package_installed numpy
check_package_installed sentence-transformers

echo -e "\n${YELLOW}Testing imports:${NC}"
test_import numpy || exit 1
test_import sentence_transformers || exit 1

# Test numpy functionality
echo -e "\n${YELLOW}Testing numpy functionality:${NC}"
python3 -c "
try:
    import numpy as np
    arr = np.array([1, 2, 3])
    print(f'Created array: {arr}')
    print('Numpy is working correctly')
except Exception as e:
    print(f'Error with numpy: {e}')
    exit(1)
" || exit 1

print_footer

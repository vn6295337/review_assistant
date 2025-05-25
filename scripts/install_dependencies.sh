#!/usr/bin/env bash
set -euo pipefail

# ───────────────────────────────────────────────────────────
# install_dependencies.sh — Install Python dependencies
# ───────────────────────────────────────────────────────────

# Load config (for future path needs)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"  # optional, in case you want to reference PROJECT paths

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'  # No Color

# Packages to install via pip
EXTERNAL_PKGS=(
  "sentence-transformers"
)

# ───────────────────────────────────────────────────────────
# Utility functions
# ───────────────────────────────────────────────────────────

info()    { echo -e "${BLUE}ℹ${NC} $*"; }
success() { echo -e "${GREEN}✔${NC} $*"; }
warn()    { echo -e "${YELLOW}⚠${NC} $*"; }
error()   { echo -e "${RED}✖${NC} $*"; }

prompt_yes_no() {
  local msg="$1"
  while true; do
    read -rp "$msg (y/n): " ans
    case "$ans" in [Yy]*) return 0;; [Nn]*) return 1;; *) echo "Please answer y or n.";; esac
  done
}

# ───────────────────────────────────────────────────────────
# Check Python & pip
# ───────────────────────────────────────────────────────────

info "Checking for Python 3..."
if ! command -v python3 &>/dev/null; then
  error "Python 3 not found. Please install Python 3."
  exit 1
else
  PYVER=$(python3 --version)
  success "Python detected: $PYVER"
fi

info "Checking for pip..."
if ! python3 -m pip --version &>/dev/null; then
  warn "pip not found. Attempting to install..."
  if prompt_yes_no "Install pip via apt-get?"; then
    sudo apt-get update && sudo apt-get install -y python3-pip
    success "pip installed"
  else
    error "pip is required. Exiting."
    exit 1
  fi
else
  PIPVER=$(python3 -m pip --version)
  success "pip detected: $PIPVER"
fi

# ───────────────────────────────────────────────────────────
# Install external packages
# ───────────────────────────────────────────────────────────

missing=()
for pkg in "${EXTERNAL_PKGS[@]}"; do
  info "Checking for Python package: $pkg"
  if python3 -c "import ${pkg//-/_}" &>/dev/null; then
    success "$pkg is already installed"
  else
    warn "$pkg not found"
    if prompt_yes_no "Install $pkg now?"; then
      info "Installing $pkg..."
      if python3 -m pip install "$pkg"; then
        success "$pkg installed successfully"
      else
        error "Failed to install $pkg"
        missing+=("$pkg")
      fi
    else
      missing+=("$pkg")
    fi
  fi
done

# ───────────────────────────────────────────────────────────
# Final summary
# ───────────────────────────────────────────────────────────

echo
echo -e "${BLUE}======================================================${NC}"
if [ ${#missing[@]} -eq 0 ]; then
  success "All dependencies installed!"
else
  warn "Setup completed with missing packages: ${missing[*]}"
  warn "Some features may not work without those."
fi
echo -e "${BLUE}======================================================${NC}"
info "You can now run: bash full_rag_workflow.sh"
echo

#!/usr/bin/env bash
# install.sh — Install the Frinkiac thinking hook for Claude Code
#
# Usage:
#   ./install.sh          # interactive install
#   ./install.sh --global # install to ~/.claude/settings.json
#   ./install.sh --local  # install to .claude/settings.local.json (gitignored)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK_SCRIPT="$SCRIPT_DIR/hooks/frinkiac-thinking.sh"

# ── Colors ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { printf "${CYAN}[info]${NC}  %s\n" "$*"; }
ok()    { printf "${GREEN}[ok]${NC}    %s\n" "$*"; }
warn()  { printf "${YELLOW}[warn]${NC}  %s\n" "$*"; }
err()   { printf "${RED}[error]${NC} %s\n" "$*"; }

# ── Check dependencies ──────────────────────────────────────────────────────

info "Checking dependencies..."

MISSING=()
for cmd in curl jq; do
  if ! command -v "$cmd" &>/dev/null; then
    MISSING+=("$cmd")
  fi
done

if [[ ${#MISSING[@]} -gt 0 ]]; then
  err "Missing required dependencies: ${MISSING[*]}"
  echo ""
  echo "Install them with your package manager:"
  echo "  macOS:  brew install ${MISSING[*]}"
  echo "  Ubuntu: sudo apt install ${MISSING[*]}"
  echo "  Arch:   sudo pacman -S ${MISSING[*]}"
  exit 1
fi
ok "Required dependencies (curl, jq) found"

# Check for optional image renderers
HAS_IMG_RENDERER=false
for cmd in chafa timg viu catimg; do
  if command -v "$cmd" &>/dev/null; then
    ok "Image renderer found: $cmd"
    HAS_IMG_RENDERER=true
    break
  fi
done

if [[ "$HAS_IMG_RENDERER" == "false" ]]; then
  warn "No terminal image renderer found"
  echo "  The hook will work with text-only mode, but for the full"
  echo "  Simpsons GIF experience, install one of these:"
  echo ""
  echo "  macOS:  brew install chafa"
  echo "  Ubuntu: sudo apt install chafa"
  echo "  Arch:   sudo pacman -S chafa"
  echo ""
  echo "  Other options: timg, viu, catimg"
  echo ""
fi

# ── Determine settings file ─────────────────────────────────────────────────

MODE="${1:-}"

if [[ "$MODE" == "--global" ]]; then
  SETTINGS_FILE="$HOME/.claude/settings.json"
elif [[ "$MODE" == "--local" ]]; then
  SETTINGS_FILE=".claude/settings.local.json"
else
  echo ""
  echo "Where should the hook be installed?"
  echo ""
  echo "  1) Global  (~/.claude/settings.json) — works in all projects"
  echo "  2) Local   (.claude/settings.local.json) — this project only, gitignored"
  echo ""
  read -rp "Choice [1/2]: " choice
  case "$choice" in
    2) SETTINGS_FILE=".claude/settings.local.json" ;;
    *) SETTINGS_FILE="$HOME/.claude/settings.json" ;;
  esac
fi

# ── Build the hook config ───────────────────────────────────────────────────

HOOK_CMD="$HOOK_SCRIPT"

# Ensure settings dir exists
mkdir -p "$(dirname "$SETTINGS_FILE")"

# Read existing settings or start fresh
if [[ -f "$SETTINGS_FILE" ]]; then
  EXISTING=$(cat "$SETTINGS_FILE")
else
  EXISTING='{}'
fi

# Merge the Notification hook into existing settings using jq
HOOK_ENTRY=$(cat <<JSONEOF
{
  "matcher": "",
  "hooks": [
    {
      "type": "command",
      "command": "$HOOK_CMD",
      "timeout": 15
    }
  ]
}
JSONEOF
)

UPDATED=$(echo "$EXISTING" | jq --argjson hook "$HOOK_ENTRY" '
  .hooks //= {} |
  .hooks.Notification //= [] |
  # Remove any existing frinkiac hooks to avoid duplicates
  .hooks.Notification = [
    .hooks.Notification[] | select(.hooks[0].command | test("frinkiac") | not)
  ] + [$hook]
')

echo "$UPDATED" | jq '.' > "$SETTINGS_FILE"

ok "Hook installed to $SETTINGS_FILE"

# ── Done ─────────────────────────────────────────────────────────────────────

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
printf "  ${GREEN}Frinkiac thinking hook installed!${NC}\n"
echo ""
echo "  Now when Claude Code sends a notification (thinking, waiting"
echo "  for input, etc.), you'll see a random Simpsons screencap"
echo "  with caption instead of a beep."
echo ""
echo "  Test it:  bash $HOOK_SCRIPT"
echo "  Remove:   Edit $SETTINGS_FILE and delete the Notification hook"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

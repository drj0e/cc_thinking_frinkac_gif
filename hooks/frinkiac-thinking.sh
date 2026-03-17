#!/usr/bin/env bash
# frinkiac-thinking.sh — Show a random Simpsons screencap from Frinkiac
# in the terminal when Claude Code fires a notification (replaces the beep).
#
# Dependencies: curl, jq
# Optional:     chafa (for terminal image rendering)

set -euo pipefail

FRINKIAC_API="https://frinkiac.com"
CACHE_DIR="${TMPDIR:-/tmp}/frinkiac-cache"
mkdir -p "$CACHE_DIR"

# ── Helpers ──────────────────────────────────────────────────────────────────

stderr() { printf '%s\n' "$*" >&2; }

cleanup() {
  # Remove temp image if it exists
  [[ -n "${IMG_FILE:-}" && -f "${IMG_FILE:-}" ]] && rm -f "$IMG_FILE"
}
trap cleanup EXIT

# ── 1. Fetch a random screencap ─────────────────────────────────────────────

random_json=$(curl -sf --max-time 5 "${FRINKIAC_API}/api/random" 2>/dev/null) || {
  stderr "Could not reach Frinkiac API"
  exit 0  # non-blocking — exit 0 so Claude Code continues normally
}

EPISODE=$(echo "$random_json" | jq -r '.Frame.Episode')
TIMESTAMP=$(echo "$random_json" | jq -r '.Frame.Timestamp')

if [[ -z "$EPISODE" || "$EPISODE" == "null" ]]; then
  stderr "Bad response from Frinkiac"
  exit 0
fi

# ── 2. Get the caption / subtitle ───────────────────────────────────────────

caption_json=$(curl -sf --max-time 5 "${FRINKIAC_API}/api/caption?e=${EPISODE}&t=${TIMESTAMP}" 2>/dev/null) || true

# Extract subtitle lines and join them
SUBTITLE=$(echo "${caption_json:-}" | jq -r '
  [.Subtitles[]?.Content // empty] | join("\n")
' 2>/dev/null) || SUBTITLE=""

# If no subtitle found, use episode info
if [[ -z "$SUBTITLE" ]]; then
  SUBTITLE="(${EPISODE} @ ${TIMESTAMP})"
fi

# ── 3. Build the image URL ──────────────────────────────────────────────────

IMG_URL="${FRINKIAC_API}/img/${EPISODE}/${TIMESTAMP}.jpg"

# Also build a GIF URL (a few seconds around the timestamp)
# Frinkiac GIFs need start/end timestamps — use ±2000ms window
START_TS=$((TIMESTAMP - 2000))
END_TS=$((TIMESTAMP + 2000))
[[ $START_TS -lt 0 ]] && START_TS=0
GIF_URL="${FRINKIAC_API}/gif/${EPISODE}/${START_TS}/${END_TS}.gif?b64lines=$(echo "$SUBTITLE" | base64 -w0 2>/dev/null || echo "$SUBTITLE" | base64 2>/dev/null)"

# ── 4. Display in terminal ──────────────────────────────────────────────────

# Determine terminal width for sizing
TERM_COLS=${COLUMNS:-$(tput cols 2>/dev/null || echo 80)}
IMG_COLS=$((TERM_COLS > 60 ? 60 : TERM_COLS))

display_image() {
  local url="$1"
  local img_file="${CACHE_DIR}/frinkiac_$$.$2"
  IMG_FILE="$img_file"

  if ! curl -sf --max-time 8 -o "$img_file" "$url" 2>/dev/null; then
    return 1
  fi

  # Try chafa first (best terminal image renderer)
  if command -v chafa &>/dev/null; then
    chafa --size="${IMG_COLS}x" --animate=off "$img_file" >&2
    return 0
  fi

  # Try timg
  if command -v timg &>/dev/null; then
    timg -g"${IMG_COLS}x" "$img_file" >&2
    return 0
  fi

  # Try viu
  if command -v viu &>/dev/null; then
    viu -w "$IMG_COLS" "$img_file" >&2
    return 0
  fi

  # Try catimg
  if command -v catimg &>/dev/null; then
    catimg -w "$IMG_COLS" "$img_file" >&2
    return 0
  fi

  return 1
}

# ── Separator ────────────────────────────────────────────────────────────────
hr() {
  local c=${1:-─}
  printf '%*s' "$IMG_COLS" '' | tr ' ' "$c" >&2
  echo >&2
}

# ── Render ───────────────────────────────────────────────────────────────────

echo >&2  # blank line

# Try to show the captioned GIF from Frinkiac first (has burned-in text)
if display_image "$GIF_URL" "gif"; then
  : # success — caption is burned into the GIF
elif display_image "$IMG_URL" "jpg"; then
  : # showed still image — print caption below
  hr
  echo "$SUBTITLE" | fold -sw "$IMG_COLS" | while IFS= read -r line; do
    printf '  %s\n' "$line" >&2
  done
  hr
else
  # No image renderer available — show ASCII-framed caption
  hr "═"
  printf '  🍩 FRINKIAC — %s\n' "$EPISODE" >&2
  hr "─"
  echo "$SUBTITLE" | fold -sw "$((IMG_COLS - 4))" | while IFS= read -r line; do
    printf '  │ %s\n' "$line" >&2
  done
  hr "═"
  printf '  🔗 %s\n' "$IMG_URL" >&2
fi

echo >&2  # trailing blank line

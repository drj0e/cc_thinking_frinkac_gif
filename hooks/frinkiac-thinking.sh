#!/usr/bin/env bash
# frinkiac-thinking.sh — Show a random Simpsons screencap from Frinkiac
# in the terminal when Claude Code fires a notification (replaces the beep).
#
# Dependencies: curl, jq
# Optional:     chafa (for terminal image rendering)

set -euo pipefail

FRINKIAC_API="https://frinkiac.com"
CACHE_DIR="${TMPDIR:-/tmp}/frinkiac-cache"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$CACHE_DIR"

# ── Helpers ──────────────────────────────────────────────────────────────────

stderr() { printf '%s\n' "$*" >&2; }

cleanup() {
  # Remove temp image if it exists
  [[ -n "${IMG_FILE:-}" && -f "${IMG_FILE:-}" ]] && rm -f "$IMG_FILE"
}
trap cleanup EXIT

# ── Offline fallback: bundled ASCII art ─────────────────────────────────────
# When the API is unreachable, show a random bundled scene instead.

show_offline_fallback() {
  local TERM_COLS=${COLUMNS:-$(tput cols 2>/dev/null || echo 80)}
  local W=$((TERM_COLS > 60 ? 60 : TERM_COLS))
  local bar
  bar=$(printf '%*s' "$W" '' | tr ' ' "═")
  local thin
  thin=$(printf '%*s' "$W" '' | tr ' ' "─")

  # Pick a random bundled scene
  local scene=$((RANDOM % 3))

  echo >&2

  # Try to render a bundled PNG through chafa if available
  local bundled_dir="${SCRIPT_DIR}/../assets/screenshots"
  local imgs=("homer_doh.png" "bart_skateboard.png" "moes_tavern.png")
  local episodes=("S05E09" "S08E02" "S06E13")
  local titles=("D'oh!" "Eat my shorts!" "To alcohol!")

  local img_file="${bundled_dir}/${imgs[$scene]}"
  local ep="${episodes[$scene]}"

  printf '  %s\n' "$bar" >&2
  printf '  \xf0\x9f\x8d\xa9 FRINKIAC \xe2\x80\x94 %s (%s)\n' "${titles[$scene]}" "$ep" >&2
  printf '  %s\n' "$thin" >&2

  local showed_image=false
  if [[ -f "$img_file" ]]; then
    for renderer in chafa timg viu catimg; do
      if command -v "$renderer" &>/dev/null; then
        case "$renderer" in
          chafa)  chafa --size="${W}x" --animate=off "$img_file" >&2 ;;
          timg)   timg -g"${W}x" "$img_file" >&2 ;;
          viu)    viu -w "$W" "$img_file" >&2 ;;
          catimg) catimg -w "$W" "$img_file" >&2 ;;
        esac
        showed_image=true
        break
      fi
    done
  fi

  printf '  %s\n' "$thin" >&2

  case $scene in
    0)
      printf '  \xe2\x94\x82 Kids, you tried your best\n' >&2
      printf '  \xe2\x94\x82 and you failed miserably.\n' >&2
      printf '  \xe2\x94\x82 The lesson is, never try.\n' >&2
      ;;
    1)
      printf "  \xe2\x94\x82 Everything's coming up Milhouse!\n" >&2
      ;;
    2)
      printf '  \xe2\x94\x82 To alcohol!\n' >&2
      printf '  \xe2\x94\x82 The cause of, and solution to,\n' >&2
      printf "  \xe2\x94\x82 all of life's problems.\n" >&2
      ;;
  esac

  printf '  %s\n' "$bar" >&2
  echo >&2
  exit 0
}

# ── 1. Fetch a random screencap ─────────────────────────────────────────────

random_json=$(curl -sf --max-time 5 "${FRINKIAC_API}/api/random" 2>/dev/null) || {
  show_offline_fallback  # API down — use bundled art
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

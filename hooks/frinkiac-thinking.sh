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

# Frinkiac burns caption text into the GIF as a single line at the bottom.
# Long text gets truncated, so pick a short version for the burned-in caption
# while keeping the full SUBTITLE for display below the image.
GIF_CAPTION="$SUBTITLE"
# If the subtitle is too long for one line (~40 chars), try to pick the
# punchiest/last line (often the punchline), or truncate gracefully.
if [[ ${#GIF_CAPTION} -gt 40 ]]; then
  # Try the last subtitle line first (usually the punchline)
  LAST_LINE=$(echo "$SUBTITLE" | tail -1)
  if [[ ${#LAST_LINE} -le 40 && ${#LAST_LINE} -gt 5 ]]; then
    GIF_CAPTION="$LAST_LINE"
  else
    # Fall back to first line if it's short enough
    FIRST_LINE=$(echo "$SUBTITLE" | head -1)
    if [[ ${#FIRST_LINE} -le 40 ]]; then
      GIF_CAPTION="$FIRST_LINE"
    else
      # Truncate to ~38 chars on a word boundary
      GIF_CAPTION=$(echo "$SUBTITLE" | tr '\n' ' ' | cut -c1-38 | sed 's/ [^ ]*$//')
    fi
  fi
fi

GIF_URL="${FRINKIAC_API}/gif/${EPISODE}/${START_TS}/${END_TS}.gif?b64lines=$(echo "$GIF_CAPTION" | base64 -w0 2>/dev/null || echo "$GIF_CAPTION" | base64 2>/dev/null)"

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

  # Try img2sixel (Sixel protocol — works in mlterm, foot, xterm w/ sixel, WezTerm, etc.)
  if command -v img2sixel &>/dev/null; then
    img2sixel -w "$((IMG_COLS * 8))" "$img_file" >&2
    return 0
  fi

  # Try jp2a (converts images to ASCII art — the scene rendered in text characters!)
  if command -v jp2a &>/dev/null; then
    local jp2a_file="$img_file"
    # jp2a only handles JPEG; convert GIF to JPG first if needed
    if [[ "$img_file" == *.gif ]]; then
      local jpg_file="${img_file%.gif}.jpg"
      if command -v convert &>/dev/null; then
        convert "${img_file}[0]" "$jpg_file" 2>/dev/null && jp2a_file="$jpg_file"
      else
        jp2a_file=""  # can't convert, skip jp2a
      fi
    fi
    if [[ -n "$jp2a_file" ]]; then
      jp2a --width="$IMG_COLS" --colors "$jp2a_file" >&2 2>/dev/null \
        || jp2a --width="$IMG_COLS" "$jp2a_file" >&2
      return 0
    fi
  fi

  # Try ascii-image-converter
  if command -v ascii-image-converter &>/dev/null; then
    ascii-image-converter -C -W "$IMG_COLS" "$img_file" >&2
    return 0
  fi

  # Python + PIL fallback — render the image as ASCII art using block characters
  if command -v python3 &>/dev/null && python3 -c "from PIL import Image" 2>/dev/null; then
    python3 -c "
import sys
from PIL import Image

img = Image.open('$img_file')
# Use first frame for GIFs
if hasattr(img, 'n_frames') and img.n_frames > 1:
    img.seek(0)
img = img.convert('RGB')

cols = $IMG_COLS
# Half-block chars give ~2:1 aspect correction
rows = int(cols * img.height / img.width / 2)
img = img.resize((cols, rows))

for y in range(rows):
    line = []
    for x in range(cols):
        r, g, b = img.getpixel((x, y))
        line.append(f'\033[38;2;{r};{g};{b}m\u2588')
    print(''.join(line) + '\033[0m', file=sys.stderr)
" 2>/dev/null
    return $?
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
  # GIF has a short caption burned in — print the full subtitle below
  # so no meaning is lost when the burned-in text was truncated.
  if [[ "$GIF_CAPTION" != "$SUBTITLE" ]]; then
    hr
    echo "$SUBTITLE" | fold -sw "$IMG_COLS" | while IFS= read -r line; do
      printf '  %s\n' "$line" >&2
    done
    hr
  fi
elif display_image "$IMG_URL" "jpg"; then
  # Showed still image — always print caption below
  hr
  echo "$SUBTITLE" | fold -sw "$IMG_COLS" | while IFS= read -r line; do
    printf '  %s\n' "$line" >&2
  done
  hr
else
  # No image renderer available — show ASCII-framed caption with Homer art
  hr "═"
  printf '  🍩 FRINKIAC — %s\n' "$EPISODE" >&2
  hr "─"
  # Mini Homer ASCII art next to the quote
  printf '  │\n' >&2
  printf '  │    ╭────────╮\n' >&2
  printf '  │    │ (o  o) │   ' >&2
  # Print first line of subtitle inline
  FIRST_LINE=$(echo "$SUBTITLE" | head -1)
  REST_LINES=$(echo "$SUBTITLE" | tail -n +2)
  printf '"%s\n' "$FIRST_LINE" >&2
  printf '  │    │  \\__/  │' >&2
  if [[ -n "$REST_LINES" ]]; then
    SECOND_LINE=$(echo "$REST_LINES" | head -1)
    printf '    %s\n' "$SECOND_LINE" >&2
    echo "$REST_LINES" | tail -n +2 | fold -sw "$((IMG_COLS - 20))" | while IFS= read -r line; do
      printf '  │    │        │    %s\n' "$line" >&2
    done
  else
    printf '\n' >&2
  fi
  printf '  │    ╰────────╯\n' >&2
  printf '  │\n' >&2
  hr "═"
  printf '  🔗 %s\n' "$IMG_URL" >&2
fi

echo >&2  # trailing blank line

#!/usr/bin/env python3
"""Generate an animated GIF demo of the Frinkiac thinking hook.

Renders Simpsons pixel art through chafa to get real ASCII art,
then composites it with terminal UI chrome into an animated GIF.
"""

import os
import re
import subprocess
from PIL import Image, ImageDraw, ImageFont

# ── Config ───────────────────────────────────────────────────────────────────

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
SCREENSHOT_DIR = os.path.join(PROJECT_DIR, "assets", "screenshots")
OUTPUT = os.path.join(PROJECT_DIR, "assets", "demo.gif")

WIDTH = 740
BG = (30, 30, 46)
FG = (205, 214, 244)
GREEN = (166, 227, 161)
CYAN = (137, 220, 235)
YELLOW = (249, 226, 175)
DIM = (108, 112, 134)
ORANGE = (250, 179, 135)
RED = (243, 139, 168)

LINE_H = 18
PADDING = 16
FONT_SIZE = 14
CHAR_W = 8.4  # approximate width of monospace char at this size

# ANSI color mapping (basic + bright)
ANSI_FG = {
    30: (0, 0, 0), 31: (197, 57, 57), 32: (57, 181, 74), 33: (199, 169, 54),
    34: (45, 100, 245), 35: (175, 82, 222), 36: (85, 185, 199), 37: (180, 180, 180),
    90: (108, 112, 134), 91: (243, 139, 168), 92: (166, 227, 161), 93: (249, 226, 175),
    94: (137, 180, 250), 95: (245, 194, 231), 96: (148, 226, 213), 97: (255, 255, 255),
}
ANSI_BG = {
    40: (0, 0, 0), 41: (197, 57, 57), 42: (57, 181, 74), 43: (199, 169, 54),
    44: (45, 100, 245), 45: (175, 82, 222), 46: (85, 185, 199), 47: (180, 180, 180),
    100: (108, 112, 134), 101: (243, 139, 168), 102: (166, 227, 161), 103: (249, 226, 175),
    104: (137, 180, 250), 105: (245, 194, 231), 106: (148, 226, 213), 107: (255, 255, 255),
}


def get_font(size):
    """Find a monospace font."""
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
        "/usr/share/fonts/truetype/ubuntu/UbuntuMono-R.ttf",
        "/System/Library/Fonts/Menlo.ttc",
    ]
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


FONT = get_font(FONT_SIZE)

# Measure actual character width
_bbox = FONT.getbbox("M")
CHAR_W = _bbox[2] - _bbox[0]


def get_chafa_output(image_path, cols=50, rows=18):
    """Run chafa on an image and return raw ANSI output."""
    try:
        result = subprocess.run(
            ["chafa", f"--size={cols}x{rows}", "--animate=off", image_path],
            capture_output=True, text=True, timeout=10
        )
        return result.stdout
    except Exception:
        return None


def parse_ansi_line(line):
    """Parse an ANSI-colored line into a list of (text, fg_color, bg_color) segments."""
    segments = []
    current_fg = FG
    current_bg = BG
    reverse = False

    # Remove cursor show/hide sequences
    line = re.sub(r'\[\?25[lh]', '', line)

    parts = re.split(r'(\x1b\[[0-9;]*m)', line)

    for part in parts:
        if not part:
            continue
        m = re.match(r'\x1b\[([0-9;]*)m', part)
        if m:
            codes = [int(c) if c else 0 for c in m.group(1).split(';')]
            i = 0
            while i < len(codes):
                c = codes[i]
                if c == 0:
                    current_fg = FG
                    current_bg = BG
                    reverse = False
                elif c == 7:
                    reverse = True
                elif c == 27:
                    reverse = False
                elif c in ANSI_FG:
                    current_fg = ANSI_FG[c]
                elif c in ANSI_BG:
                    current_bg = ANSI_BG[c]
                i += 1
        else:
            fg = current_bg if reverse else current_fg
            bg = current_fg if reverse else current_bg
            segments.append((part, fg, bg))

    return segments


def render_ansi_art(draw, x, y, ansi_text, max_width=None):
    """Render ANSI-colored text onto a PIL image. Returns new y position."""
    lines = ansi_text.split('\n')
    for line in lines:
        if not line.strip():
            continue
        segments = parse_ansi_line(line)
        cx = x
        for text, fg, bg in segments:
            text_w = len(text) * CHAR_W
            if max_width and cx + text_w > x + max_width:
                break
            # Draw background
            if bg != BG:
                draw.rectangle([cx, y, cx + text_w, y + LINE_H], fill=bg)
            # Draw text
            draw.text((cx, y + 1), text, fill=fg, font=FONT)
            cx += text_w
        y += LINE_H
    return y


def draw_text_line(draw, x, y, text, color=FG):
    """Draw a simple text line."""
    draw.text((x, y + 1), text, fill=color, font=FONT)
    return y + LINE_H


def create_frame(prompt_lines, content_lines=None, ansi_art=None, art_width=None, bottom_lines=None, height=None):
    """Create a terminal frame with optional ASCII art."""
    # Calculate height
    n_lines = len(prompt_lines)
    if content_lines:
        n_lines += len(content_lines)
    if bottom_lines:
        n_lines += len(bottom_lines)

    art_height = 0
    if ansi_art:
        art_lines = [l for l in ansi_art.split('\n') if l.strip()]
        art_height = len(art_lines) * LINE_H

    calc_h = PADDING + n_lines * LINE_H + art_height + PADDING + 10
    h = height or calc_h

    img = Image.new("RGB", (WIDTH, h), BG)
    draw = ImageDraw.Draw(img)

    y = PADDING
    for text, color in prompt_lines:
        y = draw_text_line(draw, PADDING, y, text, color)

    if content_lines:
        for text, color in content_lines:
            y = draw_text_line(draw, PADDING, y, text, color)

    if ansi_art:
        y = render_ansi_art(draw, PADDING + 10, y, ansi_art, max_width=WIDTH - 2*PADDING - 20)

    if bottom_lines:
        for text, color in bottom_lines:
            y = draw_text_line(draw, PADDING, y, text, color)

    return img


# ── Scene data ───────────────────────────────────────────────────────────────

SCENES = [
    {
        "image": "homer_doh.png",
        "episode": "S05E09",
        "quote": ["Kids, you tried your best", "and you failed miserably.", "The lesson is, never try."],
    },
    {
        "image": "bart_skateboard.png",
        "episode": "S08E02",
        "quote": ["Everything's coming up Milhouse!"],
    },
    {
        "image": "moes_tavern.png",
        "episode": "S06E13",
        "quote": ["To alcohol!", "The cause of, and solution to,", "all of life's problems."],
    },
]

PROMPT_LINES = [
    ("$ claude", GREEN),
    ("", FG),
    ("> Refactor the auth module to use JWT tokens", CYAN),
    ("", FG),
]

# ── Generate frames ─────────────────────────────────────────────────────────

def main():
    # Pre-generate chafa ASCII art for each scene
    for scene in SCENES:
        img_path = os.path.join(SCREENSHOT_DIR, scene["image"])
        if os.path.exists(img_path):
            scene["ascii"] = get_chafa_output(img_path, cols=50, rows=16)
        else:
            scene["ascii"] = None

    frames = []
    durations = []

    # Compute a fixed height for all frames (use the tallest)
    FIXED_H = 480

    # Frame 1: Just the prompt (1.5s)
    frames.append(create_frame(PROMPT_LINES, height=FIXED_H))
    durations.append(1500)

    # Frames 2-5: Thinking spinner
    spinners = ["|", "/", "-", "\\"]
    for s in spinners:
        f = create_frame(
            PROMPT_LINES,
            content_lines=[(f"  {s} Thinking...", DIM)],
            height=FIXED_H
        )
        frames.append(f)
        durations.append(250)

    # Scene 1: Homer D'oh — typing in with ASCII art
    scene = SCENES[0]
    bar = "=" * 52
    thin = "-" * 52

    header = [
        (f"  {bar}", YELLOW),
        (f"  D'oh! FRINKIAC -- {scene['episode']}", ORANGE),
        (f"  {thin}", YELLOW),
    ]

    # Show ASCII art appear
    if scene["ascii"]:
        f = create_frame(
            PROMPT_LINES,
            content_lines=header,
            ansi_art=scene["ascii"],
            bottom_lines=[
                (f"  {thin}", YELLOW),
            ] + [(f"  | {line}", FG) for line in scene["quote"]] + [
                (f"  {bar}", YELLOW),
            ],
            height=FIXED_H
        )
        frames.append(f)
        durations.append(4000)

    # Quick thinking transition
    frames.append(create_frame(
        PROMPT_LINES,
        content_lines=[(f"  / Thinking...", DIM)],
        height=FIXED_H
    ))
    durations.append(600)

    # Scene 2: Bart skateboard
    scene = SCENES[1]
    header2 = [
        (f"  {bar}", YELLOW),
        (f"  Eat my shorts! FRINKIAC -- {scene['episode']}", ORANGE),
        (f"  {thin}", YELLOW),
    ]
    if scene["ascii"]:
        f = create_frame(
            PROMPT_LINES,
            content_lines=header2,
            ansi_art=scene["ascii"],
            bottom_lines=[
                (f"  {thin}", YELLOW),
            ] + [(f"  | {line}", FG) for line in scene["quote"]] + [
                (f"  {bar}", YELLOW),
            ],
            height=FIXED_H
        )
        frames.append(f)
        durations.append(3500)

    # Another thinking transition
    frames.append(create_frame(
        PROMPT_LINES,
        content_lines=[(f"  - Thinking...", DIM)],
        height=FIXED_H
    ))
    durations.append(600)

    # Scene 3: Moe's Tavern
    scene = SCENES[2]
    header3 = [
        (f"  {bar}", YELLOW),
        (f"  Moe's Tavern! FRINKIAC -- {scene['episode']}", ORANGE),
        (f"  {thin}", YELLOW),
    ]
    if scene["ascii"]:
        f = create_frame(
            PROMPT_LINES,
            content_lines=header3,
            ansi_art=scene["ascii"],
            bottom_lines=[
                (f"  {thin}", YELLOW),
            ] + [(f"  | {line}", FG) for line in scene["quote"]] + [
                (f"  {bar}", YELLOW),
            ],
            height=FIXED_H
        )
        frames.append(f)
        durations.append(4000)

    # Final: back to thinking briefly
    frames.append(create_frame(
        PROMPT_LINES,
        content_lines=[("  \\ Thinking...", DIM)],
        height=FIXED_H
    ))
    durations.append(1000)

    # Normalize frame sizes
    max_h = max(f.height for f in frames)
    normalized = []
    for f in frames:
        if f.height < max_h:
            new = Image.new("RGB", (WIDTH, max_h), BG)
            new.paste(f, (0, 0))
            normalized.append(new)
        else:
            normalized.append(f)

    # Save GIF
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    normalized[0].save(
        OUTPUT,
        save_all=True,
        append_images=normalized[1:],
        duration=durations,
        loop=0,
        optimize=True,
    )
    size = os.path.getsize(OUTPUT)
    print(f"Saved demo GIF to {OUTPUT} ({size:,} bytes, {len(frames)} frames)")


if __name__ == "__main__":
    main()

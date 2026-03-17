#!/usr/bin/env python3
"""Generate an animated GIF demo of the Frinkiac thinking hook.

Fetches real animated GIFs from Frinkiac and composites them into
a terminal-style demo showing the hook in action.
"""

import base64
import io
import os
import subprocess
from PIL import Image, ImageDraw, ImageFont

# ── Config ───────────────────────────────────────────────────────────────────

OUTPUT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "demo.gif")
WIDTH = 720
BG = (30, 30, 46)       # dark terminal background
FG = (205, 214, 244)    # main text
GREEN = (166, 227, 161)  # green accent
CYAN = (137, 220, 235)   # cyan accent
YELLOW = (249, 226, 175) # yellow accent
DIM = (108, 112, 134)    # dimmed text
ORANGE = (250, 179, 135) # orange

LINE_H = 22
PADDING = 20
FONT_SIZE = 16

# Max dimensions for embedded clip
CLIP_MAX_W = 420
CLIP_MAX_H = 240

# ── Simpsons scenes for the demo ─────────────────────────────────────────────

DEMOS = [
    {
        "episode": "S05E18",
        "timestamp": 433715,
        "quote": "Kids, you tried your best, and you failed miserably. The lesson is, never try.",
    },
    {
        "episode": "S10E19",
        "timestamp": 1234566,
        "quote": "Everything's comin' up Milhouse!",
    },
    {
        "episode": "S08E18",
        "timestamp": 1307739,
        "quote": "To alcohol-- The cause of and solution to all of life's problems.",
    },
    {
        "episode": "S11E10",
        "timestamp": 338960,
        "quote": "Stupid, sexy Flanders!",
    },
]


def get_font(size):
    """Try to find a monospace font."""
    mono_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
        "/usr/share/fonts/truetype/ubuntu/UbuntuMono-R.ttf",
        "/System/Library/Fonts/Menlo.ttc",
        "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
    ]
    for p in mono_paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    try:
        return ImageFont.truetype("DejaVuSansMono.ttf", size)
    except Exception:
        return ImageFont.load_default()


def draw_text(draw, y, text, color=FG):
    """Draw a line of terminal text and return the next y position."""
    draw.text((PADDING, y), text, fill=color, font=FONT)
    return y + LINE_H


# ── Fetch animated GIFs from Frinkiac ─────────────────────────────────────────

def fetch_gif(demo):
    """Fetch an animated GIF from Frinkiac for the given scene."""
    ep = demo["episode"]
    ts = demo["timestamp"]
    start = max(0, ts - 2000)
    end = ts + 2000
    b64 = base64.b64encode(demo["quote"].encode()).decode()
    url = f"https://frinkiac.com/gif/{ep}/{start}/{end}.gif?b64lines={b64}"
    print(f"  Fetching GIF: {ep}...")

    try:
        result = subprocess.run(
            ["curl", "-skL", "--max-time", "30", url],
            capture_output=True, timeout=35,
        )
        if result.returncode == 0 and len(result.stdout) > 1000:
            img = Image.open(io.BytesIO(result.stdout))
            if hasattr(img, "n_frames") and img.n_frames > 1:
                print(f"    Got {img.n_frames} frames, {img.size}")
                return img
            return img
    except Exception as e:
        print(f"    Warning: curl failed: {e}")
    return None


def extract_gif_frames(gif, max_frames=20, min_duration=130):
    """Extract and resize frames from an animated GIF.

    min_duration: minimum ms per frame — Frinkiac defaults to 40ms which
    is way too fast for a README demo. 130ms gives a comfortable pace.
    """
    n = gif.n_frames
    step = max(1, n // max_frames)
    frames = []
    durations = []

    for i in range(0, n, step):
        gif.seek(i)
        frame = gif.convert("RGB")
        frame.thumbnail((CLIP_MAX_W, CLIP_MAX_H), Image.LANCZOS)
        frames.append(frame)
        orig_dur = gif.info.get("duration", 80)
        durations.append(max(orig_dur, min_duration))

    if len(frames) > max_frames:
        frames = frames[:max_frames]
        durations = durations[:max_frames]

    return frames, durations


# ── Frame builders ───────────────────────────────────────────────────────────

def render_prompt_frame():
    """Render the initial prompt."""
    h = PADDING + LINE_H * 4 + PADDING
    img = Image.new("RGB", (WIDTH, h), BG)
    draw = ImageDraw.Draw(img)
    y = PADDING
    y = draw_text(draw, y, "$ claude", GREEN)
    y = draw_text(draw, y, "", FG)
    y = draw_text(draw, y, "> Refactor the auth module to use JWT tokens", CYAN)
    return img


def render_thinking_frame(label="Thinking..."):
    """Render a thinking spinner."""
    h = PADDING + LINE_H * 5 + PADDING
    img = Image.new("RGB", (WIDTH, h), BG)
    draw = ImageDraw.Draw(img)
    y = PADDING
    y = draw_text(draw, y, "$ claude", GREEN)
    y = draw_text(draw, y, "", FG)
    y = draw_text(draw, y, "> Refactor the auth module to use JWT tokens", CYAN)
    y = draw_text(draw, y, "", FG)
    y = draw_text(draw, y, f"  {label}", DIM)
    return img


def render_clip_frame(clip_frame, total_h):
    """Compose a single animated clip frame inside a terminal window.

    No extra text below — the caption is already burned into the GIF by Frinkiac.
    """
    frame = Image.new("RGB", (WIDTH, total_h), BG)
    draw = ImageDraw.Draw(frame)
    y = PADDING

    # Terminal prompt
    y = draw_text(draw, y, "$ claude", GREEN)
    y = draw_text(draw, y, "", FG)
    y = draw_text(draw, y, "> Refactor the auth module to use JWT tokens", CYAN)
    y = draw_text(draw, y, "", FG)

    # Paste the clip frame — that's it, no redundant caption
    img_x = PADDING + 20
    frame.paste(clip_frame, (img_x, y))

    return frame


def render_homer_text_frame(demo):
    """Render the text-only fallback with Homer face."""
    ep = demo["episode"]
    # Split quote into lines for display
    words = demo["quote"].split()
    quote = []
    line = ""
    for w in words:
        if len(line) + len(w) + 1 > 30:
            quote.append(line)
            line = w
        else:
            line = f"{line} {w}".strip()
    if line:
        quote.append(line)

    homer_lines = [
        "  \u2502",
        "  \u2502    \u256d\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u256e",
        "  \u2502    \u2502 (o  o) \u2502",
        "  \u2502    \u2502  \\__/  \u2502",
        "  \u2502    \u2570\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u256f",
        "  \u2502",
    ]

    total_lines = 4 + 1 + 1 + 1 + len(homer_lines) + 1 + 1
    h = PADDING + LINE_H * total_lines + PADDING
    img = Image.new("RGB", (WIDTH, h), BG)
    draw = ImageDraw.Draw(img)
    y = PADDING

    y = draw_text(draw, y, "$ claude", GREEN)
    y = draw_text(draw, y, "", FG)
    y = draw_text(draw, y, "> Refactor the auth module to use JWT tokens", CYAN)
    y = draw_text(draw, y, "", FG)

    bar = "\u2550" * 55
    thin = "\u2500" * 55
    y = draw_text(draw, y, f"  {bar}", YELLOW)
    y = draw_text(draw, y, f"  \U0001f369 FRINKIAC \u2014 {ep}", ORANGE)
    y = draw_text(draw, y, f"  {thin}", YELLOW)

    for i, homer_line in enumerate(homer_lines):
        if i == 2 and len(quote) > 0:
            y = draw_text(draw, y, f'{homer_line}   "{quote[0]}', FG)
        elif i == 3 and len(quote) > 1:
            y = draw_text(draw, y, f"{homer_line}    {quote[1]}", FG)
        elif i == 4 and len(quote) > 2:
            y = draw_text(draw, y, f"{homer_line}    {quote[2]}", FG)
        else:
            y = draw_text(draw, y, homer_line, YELLOW)

    y = draw_text(draw, y, f"  {bar}", YELLOW)

    return img


def add_clip_scene(frames, durations, demo, gif, max_frames=20):
    """Add an animated GIF clip scene to the frame list."""
    if gif and hasattr(gif, "n_frames") and gif.n_frames > 1:
        clip_frames, clip_durations = extract_gif_frames(gif, max_frames=max_frames)
        # Height = prompt area + clip + small bottom margin
        total_h = PADDING + LINE_H * 4 + clip_frames[0].height + PADDING
        for cf, cd in zip(clip_frames, clip_durations):
            frames.append(render_clip_frame(cf, total_h))
            durations.append(cd)
        print(f"  Embedded {len(clip_frames)} frames for {demo['episode']}")
        return True
    else:
        print(f"  No animated GIF for {demo['episode']}, using text fallback")
        frames.append(render_homer_text_frame(demo))
        durations.append(3000)
        return False


def make_gif():
    """Generate the animated demo GIF."""
    frames = []
    durations = []

    # ── Fetch all animated GIFs ──────────────────────────────────────────────
    print("Fetching animated GIFs from Frinkiac...")
    gifs = {}
    for demo in DEMOS:
        gifs[demo["episode"]] = fetch_gif(demo)

    # ── Prompt + thinking intro ──────────────────────────────────────────────

    frames.append(render_prompt_frame())
    durations.append(1500)

    for s in ["\u28fb Thinking...", "\u28fe Thinking..."]:
        frames.append(render_thinking_frame(s))
        durations.append(400)

    # ── Clip 1: "Never try" ──────────────────────────────────────────────────
    add_clip_scene(frames, durations, DEMOS[0], gifs.get(DEMOS[0]["episode"]), max_frames=22)

    # ── Thinking transition ──────────────────────────────────────────────────
    frames.append(render_thinking_frame("\u28fb Thinking..."))
    durations.append(500)

    # ── Clip 2: "Everything's comin' up Milhouse" ────────────────────────────
    add_clip_scene(frames, durations, DEMOS[1], gifs.get(DEMOS[1]["episode"]), max_frames=18)

    # ── Thinking transition ──────────────────────────────────────────────────
    frames.append(render_thinking_frame("\u28fe Thinking..."))
    durations.append(500)

    # ── Clip 3: "To alcohol" ─────────────────────────────────────────────────
    add_clip_scene(frames, durations, DEMOS[2], gifs.get(DEMOS[2]["episode"]), max_frames=18)

    # ── Thinking transition ──────────────────────────────────────────────────
    frames.append(render_thinking_frame("\u28fb Thinking..."))
    durations.append(500)

    # ── Clip 4: "Stupid sexy Flanders" ───────────────────────────────────────
    add_clip_scene(frames, durations, DEMOS[3], gifs.get(DEMOS[3]["episode"]), max_frames=18)

    # ── Text fallback demo (brief) ───────────────────────────────────────────
    frames.append(render_thinking_frame("\u28fe Thinking..."))
    durations.append(500)

    frames.append(render_homer_text_frame(DEMOS[2]))
    durations.append(3500)

    # ── Normalize frame sizes and save ───────────────────────────────────────

    max_h = max(f.height for f in frames)
    max_w = max(f.width for f in frames)
    normalized = []
    for f in frames:
        if f.height < max_h or f.width < max_w:
            new = Image.new("RGB", (max_w, max_h), BG)
            new.paste(f, (0, 0))
            normalized.append(new)
        else:
            normalized.append(f)

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    normalized[0].save(
        OUTPUT,
        save_all=True,
        append_images=normalized[1:],
        duration=durations,
        loop=0,
        optimize=True,
    )
    size_kb = os.path.getsize(OUTPUT) / 1024
    print(f"\nSaved demo GIF to {OUTPUT}")
    print(f"  {len(normalized)} frames, {size_kb:.0f} KB")


FONT = get_font(FONT_SIZE)
make_gif()

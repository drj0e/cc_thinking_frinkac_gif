#!/usr/bin/env python3
"""Generate a second demo GIF showing the smart caption truncation.

These scenes have long dialogue where the hook picks the punchline
for the burned-in GIF caption. Proves the truncation logic works.
"""

import base64
import io
import os
import subprocess
from PIL import Image, ImageDraw, ImageFont

# ── Config ───────────────────────────────────────────────────────────────────

OUTPUT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "demo2.gif")
WIDTH = 720
BG = (30, 30, 46)
FG = (205, 214, 244)
GREEN = (166, 227, 161)
CYAN = (137, 220, 235)
YELLOW = (249, 226, 175)
DIM = (108, 112, 134)
ORANGE = (250, 179, 135)

LINE_H = 22
PADDING = 20
FONT_SIZE = 16

CLIP_MAX_W = 420
CLIP_MAX_H = 240

# ── Scenes with LONG dialogue — punchline gets extracted ─────────────────────
# These demonstrate the smart truncation: the burned-in GIF text is just
# the punchline, and the full quote would be printed below in the terminal.

DEMOS = [
    {
        "episode": "S06E08",
        "timestamp": 209275,
        # Full: "THIS MEANS YOU'RE FAILING ENGLISH. / ME, FAIL ENGLISH? / THAT'S UNPOSSIBLE."
        # Hook picks last line: "THAT'S UNPOSSIBLE." (18 chars) ✓
        "quote": "That's unpossible.",
    },
    {
        "episode": "S07E21",
        "timestamp": 619835,
        # Full: "Good Lord! What is happening in there? / Aurora borealis. / Aurora borealis?!"
        # Hook picks last line: "Aurora borealis?!" (17 chars) ✓
        "quote": "Aurora borealis?!",
    },
    {
        "episode": "S08E14",
        "timestamp": 939337,
        # Full: "LAST NIGHT'S ITCHY & SCRATCHY WAS, / WITHOUT A DOUBT, THE WORST EPISODE EVER."
        # Hook picks last line: fits at 40 chars ✓
        "quote": "The worst episode ever.",
    },
    {
        "episode": "S05E03",
        "timestamp": 506271,
        # Full: "♪ I AM SO SMART I AM SO SMART ♪ / ♪ I AM SO SMART I AM SO SMART ♪"
        # Hook picks last line: 35 chars ✓
        "quote": "I am so smart! S-M-R-T!",
    },
]


def get_font(size):
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
    draw.text((PADDING, y), text, fill=color, font=FONT)
    return y + LINE_H


def fetch_gif(demo):
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


def render_prompt_frame():
    h = PADDING + LINE_H * 4 + PADDING
    img = Image.new("RGB", (WIDTH, h), BG)
    draw = ImageDraw.Draw(img)
    y = PADDING
    y = draw_text(draw, y, "$ claude", GREEN)
    y = draw_text(draw, y, "", FG)
    y = draw_text(draw, y, "> Fix the flaky integration tests", CYAN)
    return img


def render_thinking_frame(label="Thinking..."):
    h = PADDING + LINE_H * 5 + PADDING
    img = Image.new("RGB", (WIDTH, h), BG)
    draw = ImageDraw.Draw(img)
    y = PADDING
    y = draw_text(draw, y, "$ claude", GREEN)
    y = draw_text(draw, y, "", FG)
    y = draw_text(draw, y, "> Fix the flaky integration tests", CYAN)
    y = draw_text(draw, y, "", FG)
    y = draw_text(draw, y, f"  {label}", DIM)
    return img


def render_clip_frame(clip_frame, total_h):
    frame = Image.new("RGB", (WIDTH, total_h), BG)
    draw = ImageDraw.Draw(frame)
    y = PADDING
    y = draw_text(draw, y, "$ claude", GREEN)
    y = draw_text(draw, y, "", FG)
    y = draw_text(draw, y, "> Fix the flaky integration tests", CYAN)
    y = draw_text(draw, y, "", FG)
    img_x = PADDING + 20
    frame.paste(clip_frame, (img_x, y))
    return frame


def add_clip_scene(frames, durations, demo, gif, max_frames=20):
    if gif and hasattr(gif, "n_frames") and gif.n_frames > 1:
        clip_frames, clip_durations = extract_gif_frames(gif, max_frames=max_frames)
        total_h = PADDING + LINE_H * 4 + clip_frames[0].height + PADDING
        for cf, cd in zip(clip_frames, clip_durations):
            frames.append(render_clip_frame(cf, total_h))
            durations.append(cd)
        print(f"  Embedded {len(clip_frames)} frames for {demo['episode']}")
        return True
    return False


def make_gif():
    frames = []
    durations = []

    print("Fetching animated GIFs from Frinkiac...")
    gifs = {}
    for demo in DEMOS:
        gifs[demo["episode"]] = fetch_gif(demo)

    # Prompt
    frames.append(render_prompt_frame())
    durations.append(1500)

    for s in ["\u28fb Thinking...", "\u28fe Thinking..."]:
        frames.append(render_thinking_frame(s))
        durations.append(400)

    # Clip 1: That's unpossible
    add_clip_scene(frames, durations, DEMOS[0], gifs.get(DEMOS[0]["episode"]), max_frames=20)

    frames.append(render_thinking_frame("\u28fb Thinking..."))
    durations.append(500)

    # Clip 2: Aurora borealis
    add_clip_scene(frames, durations, DEMOS[1], gifs.get(DEMOS[1]["episode"]), max_frames=18)

    frames.append(render_thinking_frame("\u28fe Thinking..."))
    durations.append(500)

    # Clip 3: Worst episode ever
    add_clip_scene(frames, durations, DEMOS[2], gifs.get(DEMOS[2]["episode"]), max_frames=18)

    frames.append(render_thinking_frame("\u28fb Thinking..."))
    durations.append(500)

    # Clip 4: I am so smart
    add_clip_scene(frames, durations, DEMOS[3], gifs.get(DEMOS[3]["episode"]), max_frames=18)

    # Normalize
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

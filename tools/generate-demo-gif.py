#!/usr/bin/env python3
"""Generate an animated GIF demo of the Frinkiac thinking hook."""

import os
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

# ── Simpsons quotes for the demo ────────────────────────────────────────────

DEMOS = [
    {
        "episode": "S05E09",
        "quote": [
            "Kids, you tried your best",
            "and you failed miserably.",
            "The lesson is, never try.",
        ],
        "url": "https://frinkiac.com/img/S05E09/883882.jpg",
    },
    {
        "episode": "S08E02",
        "quote": [
            "Everything's coming up Milhouse!",
        ],
        "url": "https://frinkiac.com/img/S08E02/580646.jpg",
    },
    {
        "episode": "S06E13",
        "quote": [
            "To alcohol!",
            "The cause of, and solution to,",
            "all of life's problems.",
        ],
        "url": "https://frinkiac.com/img/S06E13/1089988.jpg",
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
    # Fallback
    try:
        return ImageFont.truetype("DejaVuSansMono.ttf", size)
    except Exception:
        return ImageFont.load_default()


def draw_terminal_frame(draw, y, text, color=FG):
    """Draw a line of terminal text."""
    draw.text((PADDING, y), text, fill=color, font=FONT)
    return y + LINE_H


def render_prompt_frame():
    """Render the initial prompt frame."""
    h = PADDING + LINE_H * 4 + PADDING
    img = Image.new("RGB", (WIDTH, h), BG)
    draw = ImageDraw.Draw(img)
    y = PADDING
    y = draw_terminal_frame(draw, y, "$ claude", GREEN)
    y = draw_terminal_frame(draw, y, "", FG)
    y = draw_terminal_frame(draw, y, "> Refactor the auth module to use JWT tokens", CYAN)
    y = draw_terminal_frame(draw, y, "", FG)
    return img


def render_thinking_frame(label="Thinking..."):
    """Render a 'thinking' spinner frame."""
    h = PADDING + LINE_H * 5 + PADDING
    img = Image.new("RGB", (WIDTH, h), BG)
    draw = ImageDraw.Draw(img)
    y = PADDING
    y = draw_terminal_frame(draw, y, "$ claude", GREEN)
    y = draw_terminal_frame(draw, y, "", FG)
    y = draw_terminal_frame(draw, y, "> Refactor the auth module to use JWT tokens", CYAN)
    y = draw_terminal_frame(draw, y, "", FG)
    y = draw_terminal_frame(draw, y, f"  {label}", DIM)
    return img


def render_frinkiac_frame(demo, typing_lines=None):
    """Render a Frinkiac quote frame (text mode)."""
    ep = demo["episode"]
    quote = demo["quote"]
    if typing_lines is not None:
        quote = quote[:typing_lines]

    quote_lines = len(quote)
    total_lines = 4 + 1 + 1 + 1 + quote_lines + 1 + 1 + 1  # prompt + separator + header + sep + quote + sep + url + blank
    h = PADDING + LINE_H * total_lines + PADDING
    img = Image.new("RGB", (WIDTH, h), BG)
    draw = ImageDraw.Draw(img)
    y = PADDING

    # Prompt context
    y = draw_terminal_frame(draw, y, "$ claude", GREEN)
    y = draw_terminal_frame(draw, y, "", FG)
    y = draw_terminal_frame(draw, y, "> Refactor the auth module to use JWT tokens", CYAN)
    y = draw_terminal_frame(draw, y, "", FG)

    # Frinkiac box
    bar = "═" * 55
    thin = "─" * 55
    y = draw_terminal_frame(draw, y, f"  {bar}", YELLOW)
    y = draw_terminal_frame(draw, y, f"  \U0001f369 FRINKIAC \u2014 {ep}", ORANGE)
    y = draw_terminal_frame(draw, y, f"  {thin}", YELLOW)
    for line in quote:
        y = draw_terminal_frame(draw, y, f"  \u2502 {line}", FG)
    y = draw_terminal_frame(draw, y, f"  {bar}", YELLOW)
    y = draw_terminal_frame(draw, y, f"  \U0001f517 {demo['url']}", DIM)

    return img


def make_gif():
    """Generate the animated demo GIF."""
    frames = []
    durations = []

    # Frame 1: prompt (hold 1.5s)
    frames.append(render_prompt_frame())
    durations.append(1500)

    # Frames 2-4: thinking spinner
    spinners = ["\u28fb Thinking...", "\u28fd Thinking...", "\u28fe Thinking..."]
    for s in spinners:
        frames.append(render_thinking_frame(s))
        durations.append(400)

    # Frame 5+: First quote appears (typing effect)
    demo = DEMOS[0]
    for i in range(1, len(demo["quote"]) + 1):
        frames.append(render_frinkiac_frame(demo, typing_lines=i))
        durations.append(600)

    # Hold the full quote
    frames.append(render_frinkiac_frame(demo))
    durations.append(3000)

    # Second quote (quick flash)
    frames.append(render_thinking_frame("\u28fb Thinking..."))
    durations.append(500)

    demo2 = DEMOS[1]
    frames.append(render_frinkiac_frame(demo2))
    durations.append(2500)

    # Third quote
    frames.append(render_thinking_frame("\u28fe Thinking..."))
    durations.append(500)

    demo3 = DEMOS[2]
    for i in range(1, len(demo3["quote"]) + 1):
        frames.append(render_frinkiac_frame(demo3, typing_lines=i))
        durations.append(500)

    frames.append(render_frinkiac_frame(demo3))
    durations.append(3000)

    # Normalize frame sizes (pad to max height)
    max_h = max(f.height for f in frames)
    normalized = []
    for f in frames:
        if f.height < max_h:
            new = Image.new("RGB", (WIDTH, max_h), BG)
            new.paste(f, (0, 0))
            normalized.append(new)
        else:
            normalized.append(f)

    # Save
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    normalized[0].save(
        OUTPUT,
        save_all=True,
        append_images=normalized[1:],
        duration=durations,
        loop=0,
        optimize=True,
    )
    print(f"Saved demo GIF to {OUTPUT} ({os.path.getsize(OUTPUT)} bytes)")


FONT = get_font(FONT_SIZE)
make_gif()

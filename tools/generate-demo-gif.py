#!/usr/bin/env python3
"""Generate an animated GIF demo of the Frinkiac thinking hook."""

import io
import os
import urllib.request
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
MAGENTA = (245, 194, 231) # magenta for mode labels

LINE_H = 22
PADDING = 20
FONT_SIZE = 16
ASCII_COLS = 70  # width of ASCII art in characters

# ── Simpsons quotes for the demo ────────────────────────────────────────────

DEMOS = [
    {
        "episode": "S05E18",
        "timestamp": "433715",
        "quote": [
            "Kids, you tried your best,",
            "and you failed miserably.",
            "The lesson is, never try.",
        ],
        "url": "https://frinkiac.com/img/S05E18/433715.jpg",
    },
    {
        "episode": "S10E19",
        "timestamp": "1234566",
        "quote": [
            "Everything's comin' up Milhouse!",
        ],
        "url": "https://frinkiac.com/img/S10E19/1234566.jpg",
    },
    {
        "episode": "S08E18",
        "timestamp": "1307739",
        "quote": [
            "To alcohol--",
            "The cause of and solution to",
            "all of life's problems.",
        ],
        "url": "https://frinkiac.com/img/S08E18/1307739.jpg",
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


# ── Fetch a Frinkiac screenshot and convert to ASCII block art ───────────────

# ASCII art chars from dark to light
ASCII_CHARS = " .:-=+*#%@"


def fetch_screenshot(url):
    """Download a Frinkiac screenshot and return a PIL Image."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "frinkiac-demo/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return Image.open(io.BytesIO(resp.read()))
    except Exception as e:
        print(f"  Warning: Could not fetch {url}: {e}")
        return None


def screenshot_to_pil_thumbnail(img, target_w, target_h):
    """Resize a Frinkiac screenshot to fit in target pixel dimensions, preserving aspect."""
    img = img.convert("RGB")
    img.thumbnail((target_w, target_h), Image.LANCZOS)
    return img


def image_to_ascii_art(img, cols=ASCII_COLS):
    """Convert an image to ASCII art strings (monochrome)."""
    img = img.convert("L")  # grayscale
    rows = int(cols * img.height / img.width / 2)
    img = img.resize((cols, rows))
    lines = []
    for y_pos in range(rows):
        line = []
        for x_pos in range(cols):
            brightness = img.getpixel((x_pos, y_pos))
            idx = brightness * (len(ASCII_CHARS) - 1) // 255
            line.append(ASCII_CHARS[idx])
        lines.append("".join(line))
    return lines


# ── Frame renderers ──────────────────────────────────────────────────────────

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


def render_frinkiac_text_frame(demo, typing_lines=None):
    """Render a Frinkiac quote frame (text-only fallback with Homer face)."""
    ep = demo["episode"]
    quote = demo["quote"]
    if typing_lines is not None:
        quote = quote[:typing_lines]

    # Homer face layout: 7 lines for the face art, plus quote lines beside it
    homer_lines = [
        "  \u2502",
        "  \u2502    \u256d\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u256e",
        "  \u2502    \u2502 (o  o) \u2502",
        "  \u2502    \u2502  \\__/  \u2502",
        "  \u2502    \u2570\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u256f",
        "  \u2502",
    ]

    total_lines = 4 + 1 + 1 + 1 + len(homer_lines) + 1 + 1 + 1
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
    bar = "\u2550" * 55
    thin = "\u2500" * 55
    y = draw_terminal_frame(draw, y, f"  {bar}", YELLOW)
    y = draw_terminal_frame(draw, y, f"  \U0001f369 FRINKIAC \u2014 {ep}", ORANGE)
    y = draw_terminal_frame(draw, y, f"  {thin}", YELLOW)

    # Homer face with quote beside it
    for i, homer_line in enumerate(homer_lines):
        if i == 2 and len(quote) > 0:
            # First quote line next to face
            combined = f'{homer_line}   "{quote[0]}'
            y = draw_terminal_frame(draw, y, combined, FG)
        elif i == 3 and len(quote) > 1:
            combined = f"{homer_line}    {quote[1]}"
            y = draw_terminal_frame(draw, y, combined, FG)
        elif i == 4 and len(quote) > 2:
            combined = f"{homer_line}    {quote[2]}"
            y = draw_terminal_frame(draw, y, combined, FG)
        else:
            y = draw_terminal_frame(draw, y, homer_line, YELLOW)

    y = draw_terminal_frame(draw, y, f"  {bar}", YELLOW)
    y = draw_terminal_frame(draw, y, f"  \U0001f517 {demo['url']}", DIM)

    return img


def render_screenshot_frame(demo, screenshot, mode_label="chafa"):
    """Render a frame with the actual Frinkiac screenshot embedded (simulates chafa/image renderer)."""
    ep = demo["episode"]
    quote = demo["quote"]

    # Calculate image area: leave room for prompt (4 lines), mode label, separator, caption, url
    header_lines = 5  # prompt (4) + mode label (1)
    footer_lines = 1 + len(quote) + 1  # separator + quote + url
    header_h = PADDING + LINE_H * header_lines
    footer_h = LINE_H * footer_lines + PADDING

    # Scale screenshot to fit within the frame width
    img_area_w = WIDTH - PADDING * 2 - 40  # some margin
    img_area_h = 280  # max height for the screenshot
    thumb = screenshot_to_pil_thumbnail(screenshot.copy(), img_area_w, img_area_h)

    total_h = header_h + thumb.height + 10 + footer_h
    frame = Image.new("RGB", (WIDTH, total_h), BG)
    draw = ImageDraw.Draw(frame)
    y = PADDING

    # Prompt context
    y = draw_terminal_frame(draw, y, "$ claude", GREEN)
    y = draw_terminal_frame(draw, y, "", FG)
    y = draw_terminal_frame(draw, y, "> Refactor the auth module to use JWT tokens", CYAN)
    y = draw_terminal_frame(draw, y, "", FG)

    # Mode label
    y = draw_terminal_frame(draw, y, f"  [{mode_label}] {ep}", MAGENTA)

    # Paste the actual screenshot
    img_x = PADDING + 20
    frame.paste(thumb, (img_x, y))
    y += thumb.height + 10

    # Separator + caption
    thin = "\u2500" * 55
    y = draw_terminal_frame(draw, y, f"  {thin}", YELLOW)
    for line in quote:
        y = draw_terminal_frame(draw, y, f"  {line}", FG)
    y = draw_terminal_frame(draw, y, f"  \U0001f517 {demo['url']}", DIM)

    return frame


def render_ascii_art_frame(demo, ascii_lines):
    """Render a frame showing jp2a-style ASCII art of a scene."""
    ep = demo["episode"]
    quote = demo["quote"]

    total_lines = 4 + 1 + len(ascii_lines) + 1 + len(quote) + 1 + 1
    h = PADDING + LINE_H * total_lines + PADDING
    img = Image.new("RGB", (WIDTH, h), BG)
    draw = ImageDraw.Draw(img)
    y = PADDING

    # Prompt context
    y = draw_terminal_frame(draw, y, "$ claude", GREEN)
    y = draw_terminal_frame(draw, y, "", FG)
    y = draw_terminal_frame(draw, y, "> Refactor the auth module to use JWT tokens", CYAN)
    y = draw_terminal_frame(draw, y, "", FG)

    # Mode label
    y = draw_terminal_frame(draw, y, f"  [jp2a \u2014 ASCII art] {ep}", MAGENTA)

    # ASCII art lines
    for line in ascii_lines:
        y = draw_terminal_frame(draw, y, f"  {line}", FG)

    # Separator + caption
    thin = "\u2500" * 55
    y = draw_terminal_frame(draw, y, f"  {thin}", YELLOW)
    for line in quote:
        y = draw_terminal_frame(draw, y, f"  {line}", FG)
    y = draw_terminal_frame(draw, y, f"  \U0001f517 {demo['url']}", DIM)

    return img


def make_gif():
    """Generate the animated demo GIF."""
    frames = []
    durations = []

    # ── Pre-fetch screenshots for the visual demos ───────────────────────────
    print("Fetching Frinkiac screenshots...")
    screenshots = {}
    for demo in DEMOS:
        print(f"  Fetching {demo['episode']}...")
        screenshots[demo["episode"]] = fetch_screenshot(demo["url"])

    # ── Scene 1: Full screenshot (simulates chafa / image renderer) ─────────

    # Frame 1: prompt (hold 1.5s)
    frames.append(render_prompt_frame())
    durations.append(1500)

    # Thinking spinner
    for s in ["\u28fb Thinking...", "\u28fe Thinking..."]:
        frames.append(render_thinking_frame(s))
        durations.append(500)

    demo1 = DEMOS[0]
    ss1 = screenshots.get(demo1["episode"])
    if ss1:
        frames.append(render_screenshot_frame(demo1, ss1, mode_label="chafa"))
        durations.append(4000)
    else:
        frames.append(render_frinkiac_text_frame(demo1))
        durations.append(4000)

    # ── Scene 2: Another screenshot (different scene) ──────────────────────

    frames.append(render_thinking_frame("\u28fb Thinking..."))
    durations.append(600)

    demo2 = DEMOS[1]
    ss2 = screenshots.get(demo2["episode"])
    if ss2:
        frames.append(render_screenshot_frame(demo2, ss2, mode_label="chafa"))
        durations.append(3500)
    else:
        frames.append(render_frinkiac_text_frame(demo2))
        durations.append(3500)

    # ── Scene 3: Text-only fallback (Homer face) ─────────────────────────────

    frames.append(render_thinking_frame("\u28fe Thinking..."))
    durations.append(600)

    demo3 = DEMOS[2]
    # Show the Homer face text fallback with typing effect
    for i in range(1, len(demo3["quote"]) + 1):
        frames.append(render_frinkiac_text_frame(demo3, typing_lines=i))
        durations.append(500)
    frames.append(render_frinkiac_text_frame(demo3))
    durations.append(3500)

    # ── Normalize and save ──────────────────────────────────────────────────

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

from PIL import Image, ImageDraw, ImageFont
import numpy as np
import os
import textwrap
import math

WIDTH, HEIGHT = 1280, 720
FPS = 24

# ── Premium Color Palette ──────────────────────────────────────────────────────
BG_DARK       = (8, 10, 22)
BG_CARD       = (18, 22, 42)
BG_CARD_LIGHT = (28, 34, 62)
ACCENT_BLUE   = (99, 102, 241)    # Indigo-500
ACCENT_PURPLE = (139, 92, 246)    # Violet-500
ACCENT_CYAN   = (34, 211, 238)    # Cyan-400
WHITE         = (255, 255, 255)
OFF_WHITE     = (224, 231, 255)   # Indigo-100
MUTED_TEXT    = (148, 163, 184)   # Slate-400
ANSWER_GREEN  = (52, 211, 153)    # Emerald-400
ANSWER_BG     = (6, 78, 59)       # Emerald-900
WRONG_TEXT    = (100, 116, 139)   # Slate-500
WRONG_BG     = (30, 41, 59)       # Slate-800
TIMER_COLORS  = [(52, 211, 153), (251, 191, 36), (239, 68, 68)]
GOLD          = (251, 191, 36)

OPT_BADGE_COLORS = {
    "A": ((99, 102, 241), (79, 70, 229)),     # Indigo gradient
    "B": ((16, 185, 129), (5, 150, 105)),      # Emerald gradient
    "C": ((245, 158, 11), (217, 119, 6)),      # Amber gradient
    "D": ((244, 63, 94),  (225, 29, 72)),      # Rose gradient
}

OPT_BG_COLORS = {
    "A": (25, 28, 56),
    "B": (18, 35, 32),
    "C": (32, 28, 18),
    "D": (32, 22, 26),
}


# ── Font Helpers ───────────────────────────────────────────────────────────────

def get_font(size):
    """Load a bold font."""
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except: continue
    return ImageFont.load_default()

def get_font_reg(size):
    """Load a regular weight font."""
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except: continue
    return ImageFont.load_default()

def draw_text_centered(draw, text, font, y, color=WHITE, width=WIDTH):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    draw.text(((width - tw) // 2, y), text, font=font, fill=color)


# ── Helper Drawing Utilities ───────────────────────────────────────────────────

def _blend(c1, c2, t):
    """Blend two RGB tuples by factor t (0→c1, 1→c2)."""
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

def _draw_gradient_rect(draw, bbox, c_top, c_bottom, radius=0):
    """Draw a vertical-gradient rounded rectangle (approximated with horizontal lines)."""
    x1, y1, x2, y2 = bbox
    h = y2 - y1
    # Fill with lines for gradient effect
    for row in range(h):
        t = row / max(h - 1, 1)
        color = _blend(c_top, c_bottom, t)
        draw.line([(x1 + radius, y1 + row), (x2 - radius, y1 + row)], fill=color)
    # Draw rounded corners using the rectangle (overlay)
    if radius > 0:
        draw.rounded_rectangle(bbox, radius=radius, outline=None, fill=None)

def _draw_decorative_circles(draw):
    """Draw subtle decorative circles on the background."""
    circles = [
        (100, 580, 180, (20, 25, 55, 40)),
        (1150, 120, 140, (25, 18, 50, 30)),
        (640, 650, 100, (18, 22, 48, 25)),
    ]
    for cx, cy, r, color_alpha in circles:
        c = color_alpha[:3]
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=c)

def _draw_glow_rect(draw, bbox, glow_color, radius=14, glow_size=4):
    """Draw a subtle glow/shadow behind a rectangle."""
    x1, y1, x2, y2 = bbox
    for i in range(glow_size, 0, -1):
        alpha_t = i / glow_size
        c = _blend(glow_color, BG_DARK, alpha_t * 0.5)
        draw.rounded_rectangle(
            [x1 - i, y1 - i, x2 + i, y2 + i],
            radius=radius + i, fill=c
        )

def _draw_option_badge(draw, x, y, letter, color, size=42):
    """Draw a circular letter badge for an option."""
    r = size // 2
    # Outer circle
    draw.ellipse([x, y, x + size, y + size], fill=color)
    # Inner letter
    font_badge = get_font(22)
    bbox = draw.textbbox((0, 0), letter, font=font_badge)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text((x + (size - tw) // 2, y + (size - th) // 2 - 1), letter, font=font_badge, fill=WHITE)


# ── Background & Header ───────────────────────────────────────────────────────

def make_base(topic):
    """Draw premium background with decorations and header."""
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_DARK)
    draw = ImageDraw.Draw(img)

    # Decorative background circles
    _draw_decorative_circles(draw)

    # Top gradient accent bar
    bar_h = 56
    for row in range(bar_h):
        t = row / bar_h
        c = _blend(ACCENT_BLUE, ACCENT_PURPLE, t * 0.6)
        draw.line([(22, 12 + row), (WIDTH - 22, 12 + row)], fill=c)
    draw.rounded_rectangle([22, 12, WIDTH - 22, 12 + bar_h], radius=14, outline=None, fill=None)
    # Clip corners by redrawing BG at corners
    for corner_x, corner_y in [(22, 12), (WIDTH - 36, 12), (22, bar_h - 2), (WIDTH - 36, bar_h - 2)]:
        pass  # PIL rounded_rectangle handles this

    # Re-draw the bar with proper rounding
    draw.rounded_rectangle([22, 12, WIDTH - 22, 12 + bar_h], radius=14, fill=None, outline=None)

    # Header text
    font_h = get_font(21)
    header_text = f"🧠  GK LIVE QUIZ   ·   {topic}"
    draw_text_centered(draw, header_text, font_h, 26, WHITE)

    # Subtle separator line under header
    draw.line([(60, 72), (WIDTH - 60, 72)], fill=(35, 42, 70), width=1)

    # Bottom bar with gradient
    for row in range(36):
        t = row / 36
        c = _blend((15, 20, 40), (10, 14, 30), t)
        draw.line([(0, HEIGHT - 36 + row), (WIDTH, HEIGHT - 36 + row)], fill=c)

    font_b = get_font_reg(15)
    draw_text_centered(draw, "💬  Comment your answer!   ·   👍  Like & Subscribe!",
                       font_b, HEIGHT - 28, MUTED_TEXT)

    return img, draw


# ── Question Frame ─────────────────────────────────────────────────────────────

def make_question_frame(qdata):
    """Premium frame showing question + options with badges."""
    topic = qdata.get("topic", "General Knowledge")
    img, draw = make_base(topic)

    # ── Question Card ──
    q_box = [40, 82, WIDTH - 40, 250]
    _draw_glow_rect(draw, q_box, ACCENT_BLUE, radius=16, glow_size=5)
    draw.rounded_rectangle(q_box, radius=16, fill=BG_CARD)
    # Inner top accent line
    draw.rounded_rectangle([42, 84, WIDTH - 42, 90], radius=4, fill=ACCENT_BLUE)

    # Question number tag
    font_tag = get_font_reg(13)
    draw.rounded_rectangle([56, 100, 148, 120], radius=8, fill=(40, 48, 82))
    draw.text((64, 103), "QUESTION", font=font_tag, fill=ACCENT_CYAN)

    # Question text
    font_q = get_font(25)
    wrapped = textwrap.wrap(qdata["question"], width=58)
    q_start_y = 132
    for i, line in enumerate(wrapped[:4]):
        bbox = draw.textbbox((0, 0), line, font=font_q)
        tw = bbox[2] - bbox[0]
        draw.text(((WIDTH - tw) // 2, q_start_y + i * 34), line, font=font_q, fill=OFF_WHITE)

    # ── Options Grid (2×2) ──
    font_o = get_font(19)
    font_o_reg = get_font_reg(18)
    opt_w = (WIDTH - 100) // 2        # Width of each option card
    opt_h = 82                          # Height of each option card
    grid_top = 268
    gap_x = 20
    gap_y = 16

    for idx, (key, val) in enumerate(qdata["options"].items()):
        col = idx % 2
        row = idx // 2
        ox = 40 + col * (opt_w + gap_x)
        oy = grid_top + row * (opt_h + gap_y)

        badge_color = OPT_BADGE_COLORS.get(key, ((120, 120, 120), (90, 90, 90)))
        bg_color = OPT_BG_COLORS.get(key, (30, 35, 60))

        # Option card background
        card_rect = [ox, oy, ox + opt_w, oy + opt_h]
        draw.rounded_rectangle(card_rect, radius=12, fill=bg_color)
        # Left accent stripe
        draw.rounded_rectangle([ox, oy, ox + 5, oy + opt_h], radius=2, fill=badge_color[0])

        # Letter badge
        badge_x = ox + 16
        badge_y = oy + (opt_h - 42) // 2
        _draw_option_badge(draw, badge_x, badge_y, key, badge_color[0])

        # Option text
        text_x = badge_x + 54
        text_y_center = oy + opt_h // 2
        wrapped_o = textwrap.wrap(val, width=28)
        total_text_h = len(wrapped_o[:2]) * 26
        text_start = text_y_center - total_text_h // 2
        for li, line in enumerate(wrapped_o[:2]):
            draw.text((text_x, text_start + li * 26), line, font=font_o_reg, fill=OFF_WHITE)

    return np.array(img)


# ── Countdown Frame ────────────────────────────────────────────────────────────

def make_countdown_frame(qdata, seconds_left, total=5):
    """Frame with animated countdown ring overlay."""
    img_arr = make_question_frame(qdata).copy()
    img = Image.fromarray(img_arr)
    draw = ImageDraw.Draw(img)

    # Timer position — top-right area
    cx, cy, r = WIDTH - 82, 120, 48

    # Outer glow
    pct = seconds_left / total
    color = TIMER_COLORS[0] if pct > 0.6 else TIMER_COLORS[1] if pct > 0.3 else TIMER_COLORS[2]
    glow_c = _blend(color, BG_DARK, 0.7)
    draw.ellipse([cx - r - 8, cy - r - 8, cx + r + 8, cy + r + 8], fill=glow_c)

    # Dark circle background
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(14, 18, 36))

    # Progress arc using line segments
    segments = 48
    active = int(pct * segments)
    ring_w = 5
    for i in range(segments):
        angle = math.radians(-90 + (i / segments) * 360)
        inner_r = r - ring_w - 3
        outer_r = r - 3
        x1 = cx + inner_r * math.cos(angle)
        y1 = cy + inner_r * math.sin(angle)
        x2 = cx + outer_r * math.cos(angle)
        y2 = cy + outer_r * math.sin(angle)
        seg_color = color if i < active else (30, 38, 60)
        draw.line([x1, y1, x2, y2], fill=seg_color, width=4)

    # Timer number
    font_t = get_font(32)
    num = str(seconds_left)
    bbox = draw.textbbox((0, 0), num, font=font_t)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text((cx - tw // 2, cy - th // 2 - 1), num, font=font_t, fill=color)

    # "seconds" label below the number
    font_sec = get_font_reg(10)
    draw_text_centered(draw, "SEC", font_sec, cy + 16, MUTED_TEXT, width=WIDTH)
    # Adjust: we need it centered on cx, not full width
    # Re-draw directly
    bbox2 = draw.textbbox((0, 0), "SEC", font=font_sec)
    tw2 = bbox2[2] - bbox2[0]
    # overwrite
    draw.rectangle([cx - 20, cy + 16, cx + 20, cy + 28], fill=(14, 18, 36))
    draw.text((cx - tw2 // 2, cy + 17), "SEC", font=font_sec, fill=MUTED_TEXT)

    return np.array(img)


# ── Answer Reveal Frame ────────────────────────────────────────────────────────

def make_answer_frame(qdata):
    """Premium answer reveal with glowing correct option and explanation."""
    topic = qdata.get("topic", "General Knowledge")
    img, draw = make_base(topic)

    # ── Question Card (compact) ──
    q_box = [40, 82, WIDTH - 40, 218]
    draw.rounded_rectangle(q_box, radius=16, fill=BG_CARD)
    draw.rounded_rectangle([42, 84, WIDTH - 42, 89], radius=4, fill=ACCENT_PURPLE)

    # "ANSWER REVEAL" tag
    font_tag = get_font_reg(13)
    draw.rounded_rectangle([56, 97, 175, 117], radius=8, fill=(50, 28, 60))
    draw.text((63, 100), "ANSWER REVEAL", font=font_tag, fill=GOLD)

    # Question text (slightly muted)
    font_q = get_font(22)
    wrapped = textwrap.wrap(qdata["question"], width=62)
    for i, line in enumerate(wrapped[:3]):
        bbox = draw.textbbox((0, 0), line, font=font_q)
        tw = bbox[2] - bbox[0]
        draw.text(((WIDTH - tw) // 2, 125 + i * 30), line, font=font_q, fill=MUTED_TEXT)

    # ── Options Grid with answer highlighted ──
    font_o = get_font(19)
    font_o_reg = get_font_reg(18)
    answer = qdata["answer"]
    opt_w = (WIDTH - 100) // 2
    opt_h = 76
    grid_top = 232
    gap_x = 20
    gap_y = 14

    for idx, (key, val) in enumerate(qdata["options"].items()):
        col = idx % 2
        row = idx // 2
        ox = 40 + col * (opt_w + gap_x)
        oy = grid_top + row * (opt_h + gap_y)

        is_correct = (key == answer)
        card_rect = [ox, oy, ox + opt_w, oy + opt_h]

        if is_correct:
            # Glow behind correct answer
            _draw_glow_rect(draw, card_rect, ANSWER_GREEN, radius=12, glow_size=6)
            bg = (12, 60, 42)
            stripe_color = ANSWER_GREEN
            text_color = WHITE
            badge_color = ANSWER_GREEN
        else:
            bg = WRONG_BG
            stripe_color = (50, 60, 80)
            text_color = WRONG_TEXT
            badge_color = (60, 70, 90)

        # Card
        draw.rounded_rectangle(card_rect, radius=12, fill=bg)
        # Left stripe
        draw.rounded_rectangle([ox, oy, ox + 5, oy + opt_h], radius=2, fill=stripe_color)

        # Badge
        badge_x = ox + 16
        badge_y = oy + (opt_h - 42) // 2
        _draw_option_badge(draw, badge_x, badge_y, key, badge_color)

        # Checkmark for correct answer
        if is_correct:
            check_font = get_font(18)
            draw.text((ox + opt_w - 40, oy + 8), "✓", font=check_font, fill=ANSWER_GREEN)

        # Option text
        text_x = badge_x + 54
        text_y_center = oy + opt_h // 2
        wrapped_o = textwrap.wrap(val, width=28)
        total_text_h = len(wrapped_o[:2]) * 24
        text_start = text_y_center - total_text_h // 2
        for li, line in enumerate(wrapped_o[:2]):
            draw.text((text_x, text_start + li * 24), line,
                      font=font_o_reg if not is_correct else font_o,
                      fill=text_color)

    # ── Explanation Banner ──
    banner_y = HEIGHT - 145
    banner_box = [40, banner_y, WIDTH - 40, HEIGHT - 44]
    _draw_glow_rect(draw, banner_box, ANSWER_GREEN, radius=14, glow_size=4)
    draw.rounded_rectangle(banner_box, radius=14, fill=ANSWER_BG)
    # Top accent line on banner
    draw.rounded_rectangle([42, banner_y + 2, WIDTH - 42, banner_y + 6], radius=2, fill=ANSWER_GREEN)

    # "CORRECT ANSWER" label
    font_label = get_font(18)
    answer_val = qdata["options"].get(answer, "")
    ans_display = f"✅  Correct Answer:  {answer}. {answer_val}"
    draw_text_centered(draw, ans_display, font_label, banner_y + 16, ANSWER_GREEN)

    # Explanation text
    font_exp = get_font_reg(16)
    exp = qdata.get("explanation", "")
    wrapped_exp = textwrap.wrap(exp, width=82)
    for i, line in enumerate(wrapped_exp[:3]):
        draw_text_centered(draw, line, font_exp, banner_y + 44 + i * 22, (167, 243, 208))

    return np.array(img)


# ── Transition Frame ───────────────────────────────────────────────────────────

def make_transition_frame(t, total=1.0):
    """Animated transition with spinning ring and pulsing text."""
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_DARK)
    draw = ImageDraw.Draw(img)

    # Decorative background
    _draw_decorative_circles(draw)

    # Spinning ring
    cx, cy = WIDTH // 2, HEIGHT // 2 - 40
    outer_r, inner_r = 110, 80
    segments = 72
    for i in range(segments):
        frac = i / segments
        angle = math.radians(frac * 360 + t * 360)
        # Smooth hue rotation
        hue = (frac + t) % 1.0
        r2 = int(99 + 140 * abs(math.sin(math.pi * hue)))
        g2 = int(92 + 120 * abs(math.sin(math.pi * (hue + 0.33))))
        b2 = int(241 - 180 * abs(math.sin(math.pi * (hue + 0.66))))
        x1 = cx + outer_r * math.cos(angle)
        y1 = cy + outer_r * math.sin(angle)
        x2 = cx + inner_r * math.cos(angle)
        y2 = cy + inner_r * math.sin(angle)
        draw.line([x1, y1, x2, y2], fill=(r2, g2, b2), width=5)

    # Center filled circle
    draw.ellipse([cx - 65, cy - 65, cx + 65, cy + 65], fill=BG_DARK)

    # "GK" text in center
    font_gk = get_font(40)
    draw_text_centered(draw, "GK", font_gk, cy - 24, ACCENT_CYAN)

    # Pulsing "Get Ready" text
    alpha = abs(math.sin(math.pi * t * 2))
    brightness = int(120 + 135 * alpha)
    font_msg = get_font(26)
    draw_text_centered(draw, "Get Ready for Next Question!",
                       font_msg, HEIGHT // 2 + 100, (brightness, brightness, 240))

    # Dots animation
    dots = "·  " * (int(t * 12) % 4 + 1)
    font_dots = get_font(20)
    draw_text_centered(draw, dots.strip(), font_dots, HEIGHT // 2 + 140, MUTED_TEXT)

    # Bottom bar
    font_b = get_font_reg(15)
    draw_text_centered(draw, "💬  Comment your answer!   ·   👍  Like & Subscribe!",
                       font_b, HEIGHT - 28, (100, 110, 160))

    return np.array(img)


# ── Frame Generator ────────────────────────────────────────────────────────────

def generate_question_frames(qdata,
                              question_secs=12,
                              countdown_secs=5,
                              answer_secs=5,
                              transition_secs=2):
    """
    Generator yielding raw byte frames for one complete question cycle.
    Ultra low memory footprint to prevent container crashes.
    """
    # 1. Question phase
    qf_bytes = make_question_frame(qdata).tobytes()
    for _ in range(question_secs * FPS):
        yield qf_bytes

    # 2. Countdown phase
    for s in range(countdown_secs, 0, -1):
        cf_bytes = make_countdown_frame(qdata, s, total=countdown_secs).tobytes()
        for _ in range(FPS):
            yield cf_bytes

    # 3. Answer phase
    af_bytes = make_answer_frame(qdata).tobytes()
    for _ in range(answer_secs * FPS):
        yield af_bytes

    # 4. Transition animation
    transition_frames = transition_secs * FPS
    for i in range(transition_frames):
        t = i / transition_frames
        yield make_transition_frame(t).tobytes()

from PIL import Image, ImageDraw, ImageFont
import numpy as np
import os
import textwrap
import math

WIDTH, HEIGHT = 1080, 1920
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

def _draw_decorative_circles(draw):
    """Draw subtle decorative circles on the vertical background."""
    circles = [
        (150, 400, 260, (20, 25, 55, 40)),
        (930, 950, 300, (25, 18, 50, 30)),
        (540, 1600, 220, (18, 22, 48, 25)),
    ]
    for cx, cy, r, color_alpha in circles:
        c = color_alpha[:3]
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=c)

def _draw_glow_rect(draw, bbox, glow_color, radius=16, glow_size=6):
    """Draw a subtle glow/shadow behind a rectangle."""
    x1, y1, x2, y2 = bbox
    for i in range(glow_size, 0, -1):
        alpha_t = i / glow_size
        c = _blend(glow_color, BG_DARK, alpha_t * 0.5)
        draw.rounded_rectangle(
            [x1 - i, y1 - i, x2 + i, y2 + i],
            radius=radius + i, fill=c
        )

def _draw_option_badge(draw, x, y, letter, color, size=56):
    """Draw a circular letter badge for an option."""
    r = size // 2
    draw.ellipse([x, y, x + size, y + size], fill=color)
    font_badge = get_font(28)
    bbox = draw.textbbox((0, 0), letter, font=font_badge)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text((x + (size - tw) // 2, y + (size - th) // 2 - 2), letter, font=font_badge, fill=WHITE)


# ── Background & Header ───────────────────────────────────────────────────────

def make_base(topic):
    """Draw premium background with decorations and header."""
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_DARK)
    draw = ImageDraw.Draw(img)

    _draw_decorative_circles(draw)

    # Top gradient accent bar
    bar_h = 76
    for row in range(bar_h):
        t = row / bar_h
        c = _blend(ACCENT_BLUE, ACCENT_PURPLE, t * 0.6)
        draw.line([(30, 30 + row), (WIDTH - 30, 30 + row)], fill=c)
    draw.rounded_rectangle([30, 30, WIDTH - 30, 30 + bar_h], radius=18, fill=None, outline=None)

    # Header text
    font_h = get_font(28)
    header_text = f"🧠  GK LIVE SHORTS   ·   {topic}"
    draw_text_centered(draw, header_text, font_h, 50, WHITE)

    # Separator line under header
    draw.line([(80, 124), (WIDTH - 80, 124)], fill=(35, 42, 70), width=2)

    # Bottom bar with gradient
    for row in range(54):
        t = row / 54
        c = _blend((15, 20, 40), (10, 14, 30), t)
        draw.line([(0, HEIGHT - 54 + row), (WIDTH, HEIGHT - 54 + row)], fill=c)

    font_b = get_font_reg(22)
    draw_text_centered(draw, "💬  Comment your answer!   ·   👍  Like & Subscribe!",
                       font_b, HEIGHT - 40, MUTED_TEXT)

    return img, draw


# ── Question Frame ─────────────────────────────────────────────────────────────

def make_question_frame(qdata):
    """Premium frame showing question + vertical options stack with badges."""
    topic = qdata.get("topic", "General Knowledge")
    img, draw = make_base(topic)

    # ── Question Card ──
    q_box = [50, 146, WIDTH - 50, 480]
    _draw_glow_rect(draw, q_box, ACCENT_BLUE, radius=20, glow_size=7)
    draw.rounded_rectangle(q_box, radius=20, fill=BG_CARD)
    draw.rounded_rectangle([52, 148, WIDTH - 52, 156], radius=6, fill=ACCENT_BLUE)

    # Question tag
    font_tag = get_font_reg(18)
    draw.rounded_rectangle([80, 172, 210, 202], radius=10, fill=(40, 48, 82))
    draw.text((94, 176), "QUESTION", font=font_tag, fill=ACCENT_CYAN)

    # Question text (dynamic sizing)
    q_text_str = qdata["question"]
    if len(q_text_str) > 150:
        font_q_size = 28
        wrap_w = 42
        line_h = 38
        q_start_y = 220
    elif len(q_text_str) > 90:
        font_q_size = 32
        wrap_w = 36
        line_h = 44
        q_start_y = 225
    else:
        font_q_size = 38
        wrap_w = 30
        line_h = 50
        q_start_y = 235

    font_q = get_font(font_q_size)
    wrapped = textwrap.wrap(q_text_str, width=wrap_w)
    for i, line in enumerate(wrapped[:5]):
        bbox = draw.textbbox((0, 0), line, font=font_q)
        tw = bbox[2] - bbox[0]
        draw.text(((WIDTH - tw) // 2, q_start_y + i * line_h), line, font=font_q, fill=OFF_WHITE)

    # ── Options Vertical Stack (1 Column x 4 Rows) ──
    font_o = get_font(26)
    font_o_reg = get_font_reg(24)
    opt_w = WIDTH - 100               # 980px wide
    opt_h = 136                         # Height of each vertical card
    grid_top = 520
    gap_y = 24

    for idx, (key, val) in enumerate(qdata["options"].items()):
        ox = 50
        oy = grid_top + idx * (opt_h + gap_y)

        badge_color = OPT_BADGE_COLORS.get(key, ((120, 120, 120), (90, 90, 90)))
        bg_color = OPT_BG_COLORS.get(key, (30, 35, 60))

        card_rect = [ox, oy, ox + opt_w, oy + opt_h]
        draw.rounded_rectangle(card_rect, radius=16, fill=bg_color)
        draw.rounded_rectangle([ox, oy, ox + 8, oy + opt_h], radius=4, fill=badge_color[0])

        badge_x = ox + 24
        badge_y = oy + (opt_h - 56) // 2
        _draw_option_badge(draw, badge_x, badge_y, key, badge_color[0], size=56)

        text_x = badge_x + 76
        text_y_center = oy + opt_h // 2
        wrapped_o = textwrap.wrap(val, width=38)
        total_text_h = len(wrapped_o[:2]) * 34
        text_start = text_y_center - total_text_h // 2
        for li, line in enumerate(wrapped_o[:2]):
            draw.text((text_x, text_start + li * 34), line, font=font_o_reg, fill=OFF_WHITE)

    return np.array(img)


# ── Countdown Frame ────────────────────────────────────────────────────────────

def make_countdown_frame(qdata, seconds_left, total=5):
    """Frame with animated countdown ring overlay."""
    img_arr = make_question_frame(qdata).copy()
    img = Image.fromarray(img_arr)
    draw = ImageDraw.Draw(img)

    # Timer position — centered top right of question card
    cx, cy, r = WIDTH - 110, 200, 60

    pct = seconds_left / total
    color = TIMER_COLORS[0] if pct > 0.6 else TIMER_COLORS[1] if pct > 0.3 else TIMER_COLORS[2]
    glow_c = _blend(color, BG_DARK, 0.7)
    draw.ellipse([cx - r - 10, cy - r - 10, cx + r + 10, cy + r + 10], fill=glow_c)
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(14, 18, 36))

    segments = 48
    active = int(pct * segments)
    ring_w = 6
    for i in range(segments):
        angle = math.radians(-90 + (i / segments) * 360)
        inner_r = r - ring_w - 4
        outer_r = r - 4
        x1 = cx + inner_r * math.cos(angle)
        y1 = cy + inner_r * math.sin(angle)
        x2 = cx + outer_r * math.cos(angle)
        y2 = cy + outer_r * math.sin(angle)
        seg_color = color if i < active else (30, 38, 60)
        draw.line([x1, y1, x2, y2], fill=seg_color, width=5)

    font_t = get_font(42)
    num = str(seconds_left)
    bbox = draw.textbbox((0, 0), num, font=font_t)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text((cx - tw // 2, cy - th // 2 - 2), num, font=font_t, fill=color)

    font_sec = get_font_reg(12)
    bbox2 = draw.textbbox((0, 0), "SEC", font=font_sec)
    tw2 = bbox2[2] - bbox2[0]
    draw.rectangle([cx - 25, cy + 22, cx + 25, cy + 38], fill=(14, 18, 36))
    draw.text((cx - tw2 // 2, cy + 23), "SEC", font=font_sec, fill=MUTED_TEXT)

    return np.array(img)


# ── Answer Reveal Frame ────────────────────────────────────────────────────────

def make_answer_frame(qdata):
    """Premium answer reveal with glowing correct option and explanation."""
    topic = qdata.get("topic", "General Knowledge")
    img, draw = make_base(topic)

    # ── Question Card (compact vertical) ──
    q_box = [50, 146, WIDTH - 50, 440]
    draw.rounded_rectangle(q_box, radius=20, fill=BG_CARD)
    draw.rounded_rectangle([52, 148, WIDTH - 52, 155], radius=6, fill=ACCENT_PURPLE)

    font_tag = get_font_reg(18)
    draw.rounded_rectangle([80, 170, 260, 200], radius=10, fill=(50, 28, 60))
    draw.text((92, 174), "ANSWER REVEAL", font=font_tag, fill=GOLD)

    font_q = get_font(30)
    wrapped = textwrap.wrap(qdata["question"], width=38)
    for i, line in enumerate(wrapped[:4]):
        bbox = draw.textbbox((0, 0), line, font=font_q)
        tw = bbox[2] - bbox[0]
        draw.text(((WIDTH - tw) // 2, 215 + i * 42), line, font=font_q, fill=MUTED_TEXT)

    # ── Options Grid with answer highlighted ──
    font_o = get_font(26)
    font_o_reg = get_font_reg(24)
    answer = qdata["answer"]
    opt_w = WIDTH - 100
    opt_h = 130
    grid_top = 475
    gap_y = 20

    for idx, (key, val) in enumerate(qdata["options"].items()):
        ox = 50
        oy = grid_top + idx * (opt_h + gap_y)

        is_correct = (key == answer)
        card_rect = [ox, oy, ox + opt_w, oy + opt_h]

        if is_correct:
            _draw_glow_rect(draw, card_rect, ANSWER_GREEN, radius=16, glow_size=8)
            bg = (12, 60, 42)
            stripe_color = ANSWER_GREEN
            text_color = WHITE
            badge_color = ANSWER_GREEN
        else:
            bg = WRONG_BG
            stripe_color = (50, 60, 80)
            text_color = WRONG_TEXT
            badge_color = (60, 70, 90)

        draw.rounded_rectangle(card_rect, radius=16, fill=bg)
        draw.rounded_rectangle([ox, oy, ox + 8, oy + opt_h], radius=4, fill=stripe_color)

        badge_x = ox + 24
        badge_y = oy + (opt_h - 56) // 2
        _draw_option_badge(draw, badge_x, badge_y, key, badge_color, size=56)

        if is_correct:
            check_font = get_font(32)
            draw.text((ox + opt_w - 60, oy + 16), "✓", font=check_font, fill=ANSWER_GREEN)

        text_x = badge_x + 76
        text_y_center = oy + opt_h // 2
        wrapped_o = textwrap.wrap(val, width=38)
        total_text_h = len(wrapped_o[:2]) * 32
        text_start = text_y_center - total_text_h // 2
        for li, line in enumerate(wrapped_o[:2]):
            draw.text((text_x, text_start + li * 32), line,
                      font=font_o if is_correct else font_o_reg,
                      fill=text_color)

    # ── Explanation Banner ──
    banner_y = 1100
    banner_box = [50, banner_y, WIDTH - 50, HEIGHT - 80]
    _draw_glow_rect(draw, banner_box, ANSWER_GREEN, radius=18, glow_size=6)
    draw.rounded_rectangle(banner_box, radius=18, fill=ANSWER_BG)
    draw.rounded_rectangle([52, banner_y + 3, WIDTH - 52, banner_y + 9], radius=3, fill=ANSWER_GREEN)

    font_label = get_font(26)
    answer_val = qdata["options"].get(answer, "")
    ans_display = f"✅  Correct Answer:  {answer}. {answer_val}"
    if len(ans_display) > 50:
        ans_display = ans_display[:47] + "..."
    draw_text_centered(draw, ans_display, font_label, banner_y + 26, ANSWER_GREEN)

    font_exp = get_font_reg(22)
    exp = qdata.get("explanation", "")
    wrapped_exp = textwrap.wrap(exp, width=46)
    for i, line in enumerate(wrapped_exp[:6]):
        draw_text_centered(draw, line, font_exp, banner_y + 80 + i * 36, (167, 243, 208))

    return np.array(img)


# ── Transition Frame ───────────────────────────────────────────────────────────

def make_transition_frame(t, total=1.0):
    """Animated transition with spinning ring and pulsing text."""
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_DARK)
    draw = ImageDraw.Draw(img)

    _draw_decorative_circles(draw)

    cx, cy = WIDTH // 2, HEIGHT // 2 - 100
    outer_r, inner_r = 160, 120
    segments = 72
    for i in range(segments):
        frac = i / segments
        angle = math.radians(frac * 360 + t * 360)
        hue = (frac + t) % 1.0
        r2 = int(99 + 140 * abs(math.sin(math.pi * hue)))
        g2 = int(92 + 120 * abs(math.sin(math.pi * (hue + 0.33))))
        b2 = int(241 - 180 * abs(math.sin(math.pi * (hue + 0.66))))
        x1 = cx + outer_r * math.cos(angle)
        y1 = cy + outer_r * math.sin(angle)
        x2 = cx + inner_r * math.cos(angle)
        y2 = cy + inner_r * math.sin(angle)
        draw.line([x1, y1, x2, y2], fill=(r2, g2, b2), width=7)

    draw.ellipse([cx - 95, cy - 95, cx + 95, cy + 95], fill=BG_DARK)

    font_gk = get_font(60)
    draw_text_centered(draw, "GK", font_gk, cy - 36, ACCENT_CYAN)

    alpha = abs(math.sin(math.pi * t * 2))
    brightness = int(120 + 135 * alpha)
    font_msg = get_font(36)
    draw_text_centered(draw, "Get Ready for Next Question!",
                       font_msg, HEIGHT // 2 + 120, (brightness, brightness, 240))

    dots = "·  " * (int(t * 12) % 4 + 1)
    font_dots = get_font(30)
    draw_text_centered(draw, dots.strip(), font_dots, HEIGHT // 2 + 180, MUTED_TEXT)

    font_b = get_font_reg(22)
    draw_text_centered(draw, "💬  Comment your answer!   ·   👍  Like & Subscribe!",
                       font_b, HEIGHT - 40, (100, 110, 160))

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
    qf_bytes = make_question_frame(qdata).tobytes()
    for _ in range(question_secs * FPS):
        yield qf_bytes

    for s in range(countdown_secs, 0, -1):
        cf_bytes = make_countdown_frame(qdata, s, total=countdown_secs).tobytes()
        for _ in range(FPS):
            yield cf_bytes

    af_bytes = make_answer_frame(qdata).tobytes()
    for _ in range(answer_secs * FPS):
        yield af_bytes

    transition_frames = transition_secs * FPS
    for i in range(transition_frames):
        t = i / transition_frames
        yield make_transition_frame(t).tobytes()

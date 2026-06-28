from PIL import Image, ImageDraw, ImageFont
import numpy as np
import os
import textwrap
import math

WIDTH, HEIGHT = 1280, 720
FPS = 24

BG_COLOR      = (10, 15, 30)
ACCENT_COLOR  = (99, 102, 241)
WHITE         = (255, 255, 255)
ANSWER_COLOR  = (52, 211, 153)
TIMER_COLORS  = [(52,211,153), (251,191,36), (239,68,68)]
OPT_COLORS    = {
    "A": (79, 70, 229),
    "B": (16, 185, 129),
    "C": (245, 158, 11),
    "D": (239, 68, 68),
}

def get_font(size):
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

def make_base(topic):
    """Draw background + header."""
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Gradient-like top bar
    draw.rounded_rectangle([20, 10, WIDTH-20, 60], radius=14, fill=ACCENT_COLOR)
    font_h = get_font(22)
    draw_text_centered(draw, f"🧠 GK LIVE QUIZ  |  {topic}", font_h, 22)

    # Bottom bar
    draw.rectangle([0, HEIGHT-40, WIDTH, HEIGHT], fill=(20, 28, 50))
    font_b = get_font_reg(16)
    draw_text_centered(draw, "💬 Comment your answer below!  👍 Like & Subscribe!", font_b, HEIGHT-30, (150,160,200))

    return img, draw

def make_question_frame(qdata):
    """Frame showing question + options."""
    topic = qdata.get("topic", "General Knowledge")
    img, draw = make_base(topic)

    # Question box
    draw.rounded_rectangle([30, 75, WIDTH-30, 240], radius=14, fill=(25, 35, 65))
    font_q = get_font(26)
    wrapped = textwrap.wrap(qdata["question"], width=60)
    for i, line in enumerate(wrapped[:4]):
        bbox = draw.textbbox((0,0), line, font=font_q)
        tw = bbox[2]-bbox[0]
        draw.text(((WIDTH-tw)//2, 90 + i*38), line, font=font_q, fill=WHITE)

    # Options
    font_o = get_font(21)
    for idx, (key, val) in enumerate(qdata["options"].items()):
        col = idx % 2
        row = idx // 2
        ox = 35 + col * (WIDTH//2)
        oy = 255 + row * 105
        draw.rounded_rectangle([ox, oy, ox + WIDTH//2 - 55, oy + 88],
                               radius=12, fill=OPT_COLORS.get(key, (80,80,80)))
        opt_text = f"{key}.  {val}"
        wrapped_o = textwrap.wrap(opt_text, width=33)
        for li, line in enumerate(wrapped_o[:2]):
            draw.text((ox+16, oy+16+li*28), line, font=font_o, fill=WHITE)

    return np.array(img)

def make_countdown_frame(qdata, seconds_left, total=5):
    """Frame with countdown timer overlaid."""
    img_arr = make_question_frame(qdata).copy()
    img = Image.fromarray(img_arr)
    draw = ImageDraw.Draw(img)

    # Timer circle background
    cx, cy, r = WIDTH-80, 80, 55
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(20, 28, 50))

    # Colored arc (approximate with wedge)
    pct = seconds_left / total
    color = TIMER_COLORS[0] if pct > 0.6 else TIMER_COLORS[1] if pct > 0.3 else TIMER_COLORS[2]

    # Draw arc segments
    segments = 36
    for i in range(int(pct * segments)):
        angle = -90 + (i / segments) * 360
        angle_rad = math.radians(angle)
        x1 = cx + (r-6) * math.cos(angle_rad)
        y1 = cy + (r-6) * math.sin(angle_rad)
        x2 = cx + r * math.cos(angle_rad)
        y2 = cy + r * math.sin(angle_rad)
        draw.line([x1, y1, x2, y2], fill=color, width=5)

    # Timer number
    font_t = get_font(36)
    num = str(seconds_left)
    bbox = draw.textbbox((0,0), num, font=font_t)
    tw = bbox[2]-bbox[0]
    th = bbox[3]-bbox[1]
    draw.text((cx - tw//2, cy - th//2), num, font=font_t, fill=color)

    return np.array(img)

def make_answer_frame(qdata):
    """Frame revealing the answer."""
    topic = qdata.get("topic", "General Knowledge")
    img, draw = make_base(topic)

    # Question box (smaller)
    draw.rounded_rectangle([30, 75, WIDTH-30, 195], radius=14, fill=(25, 35, 65))
    font_q = get_font(22)
    wrapped = textwrap.wrap(qdata["question"], width=68)
    for i, line in enumerate(wrapped[:3]):
        bbox = draw.textbbox((0,0), line, font=font_q)
        tw = bbox[2]-bbox[0]
        draw.text(((WIDTH-tw)//2, 88 + i*34), line, font=font_q, fill=(180,190,220))

    # Options with answer highlighted
    font_o = get_font(21)
    answer = qdata["answer"]
    for idx, (key, val) in enumerate(qdata["options"].items()):
        col = idx % 2
        row = idx // 2
        ox = 35 + col * (WIDTH//2)
        oy = 208 + row * 98

        if key == answer:
            fill = ANSWER_COLOR
            text_c = (0, 0, 0)
            # Glow effect
            draw.rounded_rectangle([ox-3, oy-3, ox + WIDTH//2 - 52, oy + 84],
                                   radius=14, fill=(30, 150, 100))
        else:
            fill = (40, 50, 80)
            text_c = (120, 130, 150)

        draw.rounded_rectangle([ox, oy, ox + WIDTH//2 - 55, oy + 80],
                               radius=12, fill=fill)
        opt_text = f"{key}.  {val}"
        wrapped_o = textwrap.wrap(opt_text, width=33)
        for li, line in enumerate(wrapped_o[:2]):
            draw.text((ox+16, oy+14+li*26), line, font=font_o, fill=text_c)

    # Correct answer banner
    draw.rounded_rectangle([30, HEIGHT-135, WIDTH-30, HEIGHT-48],
                           radius=12, fill=(6, 60, 45))
    font_e = get_font(20)
    draw_text_centered(draw, f"✅  Correct Answer: {answer}", font_e, HEIGHT-128, ANSWER_COLOR)
    font_exp = get_font_reg(17)
    exp = qdata.get("explanation", "")
    wrapped_exp = textwrap.wrap(exp, width=85)
    if wrapped_exp:
        draw_text_centered(draw, wrapped_exp[0], font_exp, HEIGHT-100, (167,243,208))

    return np.array(img)

def make_transition_frame(t, total=1.0):
    """
    Animated transition: spinning ring + 'Next Question...' text.
    t = 0.0 .. 1.0
    """
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Spinning ring
    cx, cy = WIDTH//2, HEIGHT//2 - 40
    outer_r, inner_r = 120, 85
    segments = 60
    for i in range(segments):
        frac = i / segments
        angle = math.radians(frac * 360 + t * 360)
        # Color rotates
        hue = (frac + t) % 1.0
        r2 = int(99 + 156 * abs(math.sin(math.pi * hue)))
        g2 = int(102 + 109 * abs(math.sin(math.pi * (hue + 0.33))))
        b2 = int(241 - 200 * abs(math.sin(math.pi * (hue + 0.66))))
        x1 = cx + outer_r * math.cos(angle)
        y1 = cy + outer_r * math.sin(angle)
        x2 = cx + inner_r * math.cos(angle)
        y2 = cy + inner_r * math.sin(angle)
        draw.line([x1,y1,x2,y2], fill=(r2, g2, b2), width=6)

    # Center circle
    draw.ellipse([cx-70, cy-70, cx+70, cy+70], fill=BG_COLOR)

    # GK text in center
    font_big = get_font(38)
    draw_text_centered(draw, "GK", font_big, cy-22, ACCENT_COLOR)

    # "Next Question..." text
    alpha = abs(math.sin(math.pi * t * 2))
    gray = int(180 * alpha)
    font_msg = get_font(28)
    draw_text_centered(draw, "Get Ready for Next Question!", font_msg, HEIGHT//2 + 100, (gray, gray, 200))

    font_b = get_font_reg(16)
    draw_text_centered(draw, "💬 Comment your answer below!  👍 Like & Subscribe!",
                      font_b, HEIGHT-30, (100,110,160))

    return np.array(img)

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

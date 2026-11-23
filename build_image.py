#!/usr/bin/env python3
"""Build entry.png: one image summing up world news for Monday 23 Nov 2026.

Deterministic: same fonts, same layout, no timestamps -> identical bytes
on every run. Stdlib + Pillow only. Run: python3 build_image.py
"""
import hashlib
import os
from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")

# ---- palette ----
NAVY = (15, 37, 64)
NAVY2 = (18, 46, 80)
INK = (24, 28, 36)
MUTED = (84, 92, 104)
PAPER = (250, 249, 246)
CARD = (255, 255, 255)
LINE = (214, 218, 224)
AMBER = (245, 176, 65)
RED = (198, 54, 44)
BLUE = (41, 98, 168)
GREEN = (39, 130, 84)
TEAL = (23, 120, 122)
GOLD = (176, 132, 24)

FONT_DIR = "/usr/share/fonts/truetype/dejavu"


def font(name, size):
    path = os.path.join(FONT_DIR, name)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"font missing: {path}")
    return ImageFont.truetype(path, size)


F_TITLE = font("DejaVuSans-Bold.ttf", 40)
F_DATE = font("DejaVuSans-Bold.ttf", 21)
F_DATESUB = font("DejaVuSans.ttf", 13)
F_TAG = font("DejaVuSans-Bold.ttf", 12)
F_HEAD = font("DejaVuSans-Bold.ttf", 22)
F_SUB = font("DejaVuSans.ttf", 14)
F_SECT = font("DejaVuSans-Bold.ttf", 17)
F_MORE_B = font("DejaVuSans-Bold.ttf", 14)
F_MORE = font("DejaVuSans.ttf", 14)
F_WIRE_T = font("DejaVuSans-Bold.ttf", 15)
F_WIRE = font("DejaVuSans.ttf", 13)
F_CHECK = font("DejaVuSans-Bold.ttf", 16)
F_SRC = font("DejaVuSans.ttf", 12)
F_FOOT = font("DejaVuSans.ttf", 11)


def wrap(text, fnt, max_w):
    """Greedy word wrap; returns list of lines, each fitting max_w."""
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if fnt.getlength(trial) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


NO_SPACE_BEFORE = ";,.:!?%)]"


def _join_words(words):
    out = ""
    for w in words:
        if out and w[0] not in NO_SPACE_BEFORE:
            out += " "
        out += w
    return out


def wrap_mixed(bold, rest, max_w):
    """Greedy wrap of bold+rest where bold words are measured in the bold
    font and rest words in the regular font. Returns list of lines."""
    bwords = bold.split()
    rwords = rest.split()
    # (word, is_bold) stream; rest may start with punctuation attached to
    # its first word, which is fine -- it is measured regular.
    stream = [(w, True) for w in bwords] + [(w, False) for w in rwords]
    lines, cur, cur_w = [], [], 0.0
    space_b = F_MORE_B.getlength(" ")
    space_r = F_MORE.getlength(" ")
    for word, is_b in stream:
        wlen = (F_MORE_B if is_b else F_MORE).getlength(word)
        if not cur:
            add = wlen
        elif word[0] in NO_SPACE_BEFORE:
            add = wlen
        else:
            add = (space_b if is_b else space_r) + wlen
        if cur and cur_w + add > max_w:
            lines.append(_join_words([w for w, _ in cur]))
            cur, cur_w = [(word, is_b)], wlen
        else:
            cur.append((word, is_b))
            cur_w += add
    if cur:
        lines.append(_join_words([w for w, _ in cur]))
    return lines, stream


def draw_mixed_line(d, x, y, line, bold_left):
    """Draw one wrapped line; the first bold_left chars are bold."""
    n_bold = max(0, min(bold_left, len(line)))
    if n_bold:
        d.text((x, y), line[:n_bold], font=F_MORE_B, fill=INK)
        x += F_MORE_B.getlength(line[:n_bold])
    if n_bold < len(line):
        d.text((x, y), line[n_bold:], font=F_MORE, fill=INK)
    return bold_left - n_bold


def draw_wrapped(d, x, y, lines, fnt, fill, lh):
    for ln in lines:
        d.text((x, y), ln, font=fnt, fill=fill)
        y += lh
    return y


def rounded(d, box, r, fill=None, outline=None, width=1):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


# ---- content (all verified from AP / Reuters / BBC / AFP / CFR, 23 Nov 2026) ----
PANELS = [
    {
        "tag": "DIPLOMACY", "accent": BLUE,
        "head": "Ukraine talks in Abu Dhabi end with no breakthrough",
        "sub": "US-mediated talks stall on guarantees; Trump meets Putin in Anchorage tomorrow.",
        "icon": "globe",
    },
    {
        "tag": "UKRAINE WAR", "accent": RED,
        "head": "Kyiv toll climbs as rescuers dig through rubble",
        "sub": "At least 15 dead; a boy, 7, was pulled alive after 14 hours under the rubble.",
        "icon": "rescue",
    },
    {
        "tag": "MARKETS", "accent": GREEN,
        "head": "Stocks steady after AI sell-off hits Wall Street",
        "sub": "US futures climb after the Nasdaq's worst week since March 2020; Asia mixed.",
        "icon": "chart",
    },
    {
        "tag": "AFRICA", "accent": TEAL,
        "head": "Kenya and DR Congo restore full diplomatic ties",
        "sub": "Ruto and Tshisekedi agree to restore ties after tensions over the DR Congo war.",
        "icon": "rings",
    },
]

MORE = [
    ("Democrats clinch 258 House seats", " \u2014 largest majority since 1992 (AP)."),
    ("COP31 ends with no climate deal", " after the longest talks in UN history."),
    ("Ukrainian sea drones hit a Russian warship", " at Benghazi; it capsized, officials say."),
    ("Trump meets Putin in Anchorage tomorrow", "; warns of \u201csevere consequences\u201d if no deal."),
    ("Kushner: Trump open to a NATO-style guarantee", " for Ukraine, if invasion risk falls."),
    ("Indonesia candy factory fire kills 24", "; about 30 still unaccounted for."),
    ("Tanker attacks in the Strait of Hormuz", " hit a new high since the war began."),
    ("Liverpool thrash Man Utd 4-0", " in Pochettino\u2019s first match in charge."),
    ("Alcaraz beats Zverev", " to win his first ATP Finals title."),
    ("49ers rout Vikings 35-10 in Mexico City", "; Purdy throws three TDs."),
    ("BepiColombo enters Mercury orbit", " \u2014 only the second mission ever to do so."),
    ("Shuri Castle\u2019s main hall restored", ", seven years after fire destroyed it."),
    ("South Korea\u2019s education minister resigns", " over an exam cheating scandal."),
    ("Mexico makes more arrests", " after a drug kingpin\u2019s capture."),
    ("Modi offers flood-hit Nepal", " a $1.6bn aid package."),
    ("Iran vows \u201call available means\u201d", " to counter a US blockade."),
    ("Zelensky calls for four-way talks", " with Russia \u201cas soon as possible\u201d."),
    ("Tyson Fury reveals schizophrenia diagnosis", " in a Netflix documentary."),
]

WIRE = [
    ("02:36 UTC", "Russian ships hit by Ukrainian drones off Libya coast"),
    ("05:33 UTC", "Dymer death toll rises to 11 as rescuers keep digging"),
    ("09:00 UTC", "US-brokered Ukraine talks in Abu Dhabi end without a deal"),
    ("13:00 UTC", "Mexico makes more arrests after drug kingpin\u2019s capture"),
]

SOURCES = ("Sources: Associated Press \u00b7 Reuters \u00b7 BBC \u00b7 AFP \u00b7 CFR Daily News "
           "Brief \u00b7 Al Jazeera \u00b7 Xinhua \u2014 all items verified from reports published 23 Nov 2026.")


def draw_icon(d, kind, x, y, s, color):
    """Small drawn illustration inside a s x s box at (x, y)."""
    if kind == "globe":
        cx, cy, r = x + s // 2, y + s // 2, s // 2 - 6
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=4)
        d.ellipse([cx - r // 2, cy - r, cx + r // 2, cy + r], outline=color, width=3)
        d.line([cx - r, cy, cx + r, cy], fill=color, width=3)
        d.arc([cx - r, cy - r // 2, cx + r, cy + r // 2], 200, 340, fill=color, width=3)
        d.arc([cx - r, cy - r // 2, cx + r, cy + r // 2], 20, 160, fill=color, width=3)
    elif kind == "rescue":
        # building with a crack + a small cross badge
        bx, by = x + 10, y + 8
        d.rectangle([bx, by, bx + 52, by + 62], outline=color, width=4)
        for wy in (by + 12, by + 28, by + 44):
            for wx in (bx + 9, bx + 25, bx + 41):
                d.rectangle([wx, wy, wx + 7, wy + 7], fill=color)
        d.line([(bx + 26, by), (bx + 20, by + 22), (bx + 30, by + 38),
                (bx + 22, by + 62)], fill=RED, width=3)
        cx, cy, r = x + s - 20, y + s - 20, 15
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=RED)
        d.rectangle([cx - 3, cy - 9, cx + 3, cy + 9], fill=(255, 255, 255))
        d.rectangle([cx - 9, cy - 3, cx + 9, cy + 3], fill=(255, 255, 255))
    elif kind == "chart":
        bars = [22, 36, 30, 48]
        bx, by = x + 12, y + s - 14
        for i, bh in enumerate(bars):
            x0 = bx + i * 18
            d.rectangle([x0, by - bh, x0 + 11, by], fill=color)
        d.line([(x + 8, y + 22), (x + 30, y + 34), (x + 48, y + 20),
                (x + s - 10, y + 8)], fill=color, width=4)
        d.polygon([(x + s - 10, y + 8), (x + s - 22, y + 8), (x + s - 10, y + 20)],
                  fill=color)
    elif kind == "rings":
        cx, cy, r = x + s // 2, y + s // 2 - 4, 22
        d.ellipse([cx - r - 14, cy - r, cx - r + 14, cy + r], outline=color, width=5)
        d.ellipse([cx + r - 14, cy - r, cx + r + 14, cy + r], outline=AMBER, width=5)
        d.line([(x + 14, y + s - 10), (x + 24, y + s - 20)], fill=GREEN, width=4)
        d.line([(x + 24, y + s - 20), (x + 40, y + s - 4)], fill=GREEN, width=4)


def build():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # ---------- header ----------
    d.rectangle([0, 0, W, 86], fill=NAVY)
    d.rectangle([0, 86, W, 90], fill=AMBER)
    d.text((16, 14), "THE WORLD IN ONE IMAGE", font=F_TITLE, fill=(255, 255, 255))
    d.text((16, 60), "23 November 2026  \u00b7  World news, summed up  \u00b7  make.fun bounty",
           font=F_DATESUB, fill=(196, 208, 224))
    dt = "MONDAY"
    d.text((W - 16 - F_DATE.getlength(dt), 12), dt, font=F_DATE, fill=AMBER)
    d.text((W - 16 - F_DATE.getlength("23 NOVEMBER 2026"), 40), "23 NOVEMBER 2026",
           font=F_DATE, fill=(255, 255, 255))

    # ---------- 4 main panels (2 x 2) ----------
    px, py, pw, ph, gap = 16, 102, 488, 186, 12
    for i, p in enumerate(PANELS):
        x = px + (i % 2) * (pw + gap)
        y = py + (i // 2) * (ph + gap)
        d.rounded_rectangle([x, y, x + pw, y + ph], radius=10, fill=CARD,
                            outline=LINE, width=1)
        d.rounded_rectangle([x, y, x + pw, y + 6], radius=3, fill=p["accent"])
        d.rectangle([x, y + 3, x + pw, y + 6], fill=p["accent"])
        # tag chip
        tag = p["tag"]
        tw = F_TAG.getlength(tag)
        ty = y + 16
        d.rounded_rectangle([x + 14, ty, x + 14 + tw + 16, ty + 22], radius=11,
                            fill=p["accent"])
        d.text((x + 22, ty + 4), tag, font=F_TAG, fill=(255, 255, 255))
        # icon box (right)
        ix, iy, isz = x + pw - 14 - 96, y + 48, 96
        d.rounded_rectangle([ix, iy, ix + isz, iy + isz], radius=12,
                            fill=(238, 242, 246))
        draw_icon(d, p["icon"], ix + 8, iy + 8, isz - 16, p["accent"])
        # headline + sub (left column)
        tx = x + 14
        tw_text = pw - 28 - 96 - 10
        head_lines = wrap(p["head"], F_HEAD, tw_text)
        assert len(head_lines) <= 2, f"panel {i} headline too long: {head_lines}"
        for ln in head_lines:
            assert F_HEAD.getlength(ln) <= tw_text
        hy = ty + 34
        hy = draw_wrapped(d, tx, hy, head_lines, F_HEAD, INK, 27)
        sub_lines = wrap(p["sub"], F_SUB, tw_text)
        assert len(sub_lines) <= 2, f"panel {i} sub too long: {sub_lines}"
        for ln in sub_lines:
            assert F_SUB.getlength(ln) <= tw_text
        draw_wrapped(d, tx, hy + 6, sub_lines, F_SUB, MUTED, 19)

    # ---------- More from 23 November ----------
    my = py + 2 * ph + gap + 12  # 498
    d.text((16, my), "MORE FROM 23 NOVEMBER", font=F_SECT, fill=INK)
    d.line([(16, my + 26), (W - 16, my + 26)], fill=LINE, width=2)
    col_w = 488
    row_h = 35
    iy0 = my + 36
    for idx, (bold, rest) in enumerate(MORE):
        col = idx // 9
        row = idx % 9
        x = 16 + col * (col_w + 12)
        y = iy0 + row * row_h
        # wrap with mixed fonts: bold lead measured bold, rest measured regular
        lines, _stream = wrap_mixed(bold, rest, col_w - 18)
        assert len(lines) <= 2, f"more item {idx} too long: {lines}"
        _bl = len(bold)
        for _ln in lines:
            _n = max(0, min(_bl, len(_ln)))
            _w = F_MORE_B.getlength(_ln[:_n]) + F_MORE.getlength(_ln[_n:])
            assert _w <= col_w - 18, f"more item {idx} overflows: {_ln} ({_w:.1f})"
            _bl -= _n
        # draw line 1: bullet + mixed text, then line 2 if any
        d.text((x, y), "\u2022", font=F_MORE_B, fill=RED)
        lx = x + 14
        bold_left = len(bold)
        bold_left = draw_mixed_line(d, lx, y, lines[0], bold_left)
        if len(lines) == 2:
            draw_mixed_line(d, lx, y + 18, lines[1], bold_left)
    more_bottom = iy0 + 9 * row_h  # 498+36+333 = 867

    # ---------- UTC wire strip ----------
    wy = more_bottom + 6  # 873
    wh = 70
    d.rounded_rectangle([16, wy, W - 16, wy + wh], radius=8, fill=NAVY2)
    d.text((28, wy + 6), "UTC WIRE", font=F_TAG, fill=AMBER)
    col_w = (W - 32 - 24) // 4
    for i, (t, txt) in enumerate(WIRE):
        x = 28 + i * col_w
        d.text((x, wy + 22), t, font=F_WIRE_T, fill=AMBER)
        lines = wrap(txt, F_WIRE, col_w - 12)
        assert len(lines) <= 2, f"wire {i} too long: {lines}"
        draw_wrapped(d, x, wy + 42, lines, F_WIRE, (235, 238, 242), 14)
    wire_bottom = wy + wh  # 939

    # ---------- footer: date check + sources ----------
    fy = wire_bottom + 10  # 949
    check = "DATE CHECK: Monday, 23 November 2026"
    d.text(((W - F_CHECK.getlength(check)) // 2, fy), check, font=F_CHECK, fill=RED)
    fy += 26
    src_lines = wrap(SOURCES, F_SRC, 860)
    assert len(src_lines) <= 2, f"sources too long: {src_lines}"
    for ln in src_lines:
        d.text(((W - F_SRC.getlength(ln)) // 2, fy), ln, font=F_SRC, fill=MUTED)
        fy += 16
    fy += 4
    foot = "Built by an AI agent for make.fun \u00b7 entry.png generated deterministically with Python + Pillow"
    d.text(((W - F_FOOT.getlength(foot)) // 2, fy), foot, font=F_FOOT, fill=MUTED)
    assert fy + 14 <= H - 4, f"footer overflows: {fy}"

    img.save(OUT, format="PNG", optimize=True)
    size = os.path.getsize(OUT)
    assert img.size == (1024, 1024)
    assert size <= 1024 * 1024, f"PNG too big: {size}"
    digest = hashlib.sha256(open(OUT, "rb").read()).hexdigest()
    print(f"entry.png  {img.size}  {size} bytes  sha256={digest}")
    return digest


if __name__ == "__main__":
    build()

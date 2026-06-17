#!/usr/bin/env python3
"""Render the GitHub social-preview (OG) card for vrp-ir.

Deterministic, no network. Outputs a 1280x640 PNG (GitHub's recommended
social-preview size), rendered at 2x and downscaled for crisp text.
"""
from __future__ import annotations

import os
from PIL import Image, ImageDraw, ImageFont

S = 2  # supersampling factor
W, H = 1280 * S, 640 * S

# palette
BG = (11, 14, 20)
PANEL = (17, 22, 31)
BORDER = (45, 54, 67)
WHITE = (230, 237, 243)
MUTED = (139, 148, 158)
GREEN = (63, 185, 80)
RED = (248, 81, 73)
AMBER = (210, 153, 34)
TEAL = (45, 212, 191)

FONT_DIR = "/usr/share/fonts/truetype"
def sans(sz, bold=False):
    p = f"{FONT_DIR}/dejavu/DejaVuSans{'-Bold' if bold else ''}.ttf"
    return ImageFont.truetype(p, sz * S)
def mono(sz, bold=False):
    p = f"{FONT_DIR}/dejavu/DejaVuSansMono{'-Bold' if bold else ''}.ttf"
    return ImageFont.truetype(p, sz * S)

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)

# left accent bar
d.rectangle([0, 0, 10 * S, H], fill=TEAL)

PAD = 64 * S

# wordmark
d.text((PAD, 56 * S), "vrp-ir", font=mono(58, bold=True), fill=WHITE)
d.text((PAD + 360 * S, 84 * S), "Apache-2.0  ·  pip install vrp-ir",
       font=sans(18), fill=MUTED)

# tagline
d.text((PAD, 142 * S),
       "Source-traceable IR for Huawei VRP/USG configs",
       font=sans(30, bold=True), fill=WHITE)

# differentiator hook
d.text((PAD, 192 * S),
       "Batfish marks Huawei VRP unsupported.  vrp-ir parses it —",
       font=sans(22), fill=MUTED)
d.text((PAD, 224 * S),
       "every field carries its file:line, every finding cites the line.",
       font=sans(22), fill=MUTED)

# terminal panel
px0, py0, px1, py1 = PAD, 288 * S, W - PAD, 552 * S
d.rounded_rectangle([px0, py0, px1, py1], radius=14 * S, fill=PANEL,
                    outline=BORDER, width=2 * S)
# window dots
for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
    d.ellipse([px0 + (28 + i * 26) * S, py0 + 20 * S,
               px0 + (28 + i * 26) * S + 14 * S, py0 + 20 * S + 14 * S], fill=c)

mf = mono(18)
mb = mono(18, bold=True)
tx = px0 + 30 * S
ty = py0 + 56 * S
lh = 30 * S

def line(parts, y):
    x = tx
    for text, color, font in parts:
        d.text((x, y), text, font=font, fill=color)
        x += d.textlength(text, font=font)

line([("$ ", GREEN, mb), ("vrp-ir audit edge-fw.cfg --strict", WHITE, mf)], ty)
line([("FAIL  ", RED, mb),
      ("FW-DEFAULT-DENY ", WHITE, mb),
      ("[CRITICAL]", RED, mf)], ty + int(lh * 1.5))
line([("      evidence  ", MUTED, mf),
      ("edge-fw.cfg:14", AMBER, mb),
      ("  default action permit", MUTED, mf)], ty + int(lh * 2.5))
line([("FAIL  ", RED, mb),
      ("FW-PERMIT-SCOPE ", WHITE, mb),
      ("[HIGH]   ", RED, mf),
      ("rule 'any-to-any' not narrowed", MUTED, mf)], ty + int(lh * 4.0))
line([("$ ", GREEN, mb), ("echo $?  ", WHITE, mf),
      ("# 1  -> drop into CI as an acceptance gate", MUTED, mf)],
     ty + int(lh * 5.5))

# footer tag
d.text((PAD, 576 * S), "open core of AegisTwin", font=sans(18, bold=True), fill=TEAL)

img = img.resize((1280, 640), Image.LANCZOS)
_out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "og-card.png")
img.save(_out)
print("wrote", _out, img.size)

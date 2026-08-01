#!/usr/bin/env python3
"""Generate the product photos used by ``seed.py``.

The seeded catalogue ships with its own artwork so a fresh checkout has real
images without needing S3, network access, or binary blobs in git. Every photo
is a flat-vector SVG drawn from the palette of the storefront design system.

Run from ``packages/api``::

    python scripts/generate_product_images.py

Output goes to ``app/static/products/<slug>-<n>.svg`` and is deterministic, so
regenerating produces a byte-identical tree.
"""
import hashlib
import os
from typing import Callable, Dict, List

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app", "static", "products")

SIZE = 800

# ── Colourways ─────────────────────────────────────────────────────────────
# Backgrounds stay in the cream/sage family of the design system; the product
# body colours carry the variation between shots.
PALETTES: List[Dict[str, str]] = [
    {"bg1": "#eeebe3", "bg2": "#d9ded8", "body": "#2f3a35", "accent": "#ca0013", "light": "#f7f5f0", "dark": "#171e19"},
    {"bg1": "#e6ece9", "bg2": "#c9d5d1", "body": "#3d4a52", "accent": "#e0a458", "light": "#f4f7f5", "dark": "#171e19"},
    {"bg1": "#f2ece6", "bg2": "#ddd0c3", "body": "#8c5a3c", "accent": "#2f3a35", "light": "#faf6f2", "dark": "#171e19"},
    {"bg1": "#e9e6ef", "bg2": "#cdc7dc", "body": "#4b4266", "accent": "#ca0013", "light": "#f6f4fa", "dark": "#171e19"},
    {"bg1": "#eaf0ec", "bg2": "#c8d8cd", "body": "#2c5545", "accent": "#e0a458", "light": "#f5f9f6", "dark": "#171e19"},
    {"bg1": "#f3ebe9", "bg2": "#e0c8c5", "body": "#7a3b3b", "accent": "#2f3a35", "light": "#fbf5f4", "dark": "#171e19"},
]


def palette_for(slug: str, index: int) -> Dict[str, str]:
    """Pick a stable palette per (product, shot) so output never churns."""
    seed = int(hashlib.sha256(slug.encode()).hexdigest(), 16)
    return PALETTES[(seed + index) % len(PALETTES)]


# ── Drawing helpers ────────────────────────────────────────────────────────

def _chrome(p: Dict[str, str], index: int) -> str:
    """Background wash, vignette and floor shadow shared by every shot."""
    return f"""  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0.4" y2="1">
      <stop offset="0%" stop-color="{p['bg1']}"/>
      <stop offset="100%" stop-color="{p['bg2']}"/>
    </linearGradient>
    <radialGradient id="glow" cx="50%" cy="42%" r="62%">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.55"/>
      <stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="floor" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="{p['dark']}" stop-opacity="0.20"/>
      <stop offset="100%" stop-color="{p['dark']}" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="{SIZE}" height="{SIZE}" fill="url(#bg)"/>
  <rect width="{SIZE}" height="{SIZE}" fill="url(#glow)"/>
  <circle cx="{620 if index % 2 else 180}" cy="{170 if index % 2 else 640}" r="130" fill="#ffffff" opacity="0.18"/>
  <ellipse cx="400" cy="648" rx="215" ry="42" fill="url(#floor)"/>"""


# ── Product silhouettes ────────────────────────────────────────────────────
# Each function draws one product family, centred on a 800x800 canvas with the
# subject roughly inside x/y 200-600.

def laptop(p: Dict[str, str]) -> str:
    return f"""  <g>
    <path d="M245 250 h310 a18 18 0 0 1 18 18 v218 h-346 v-218 a18 18 0 0 1 18 -18 z" fill="{p['body']}"/>
    <rect x="262" y="268" width="276" height="184" rx="8" fill="{p['light']}"/>
    <rect x="284" y="296" width="150" height="14" rx="7" fill="{p['accent']}" opacity="0.85"/>
    <rect x="284" y="326" width="210" height="10" rx="5" fill="{p['body']}" opacity="0.25"/>
    <rect x="284" y="350" width="180" height="10" rx="5" fill="{p['body']}" opacity="0.25"/>
    <rect x="284" y="374" width="120" height="10" rx="5" fill="{p['body']}" opacity="0.25"/>
    <path d="M196 486 h408 l30 46 a10 10 0 0 1 -9 15 h-450 a10 10 0 0 1 -9 -15 z" fill="{p['body']}"/>
    <rect x="352" y="500" width="96" height="10" rx="5" fill="{p['light']}" opacity="0.5"/>
  </g>"""


def headphones(p: Dict[str, str]) -> str:
    return f"""  <g>
    <path d="M262 442 v-58 a138 138 0 0 1 276 0 v58" fill="none" stroke="{p['body']}" stroke-width="34" stroke-linecap="round"/>
    <path d="M286 400 a114 114 0 0 1 228 0" fill="none" stroke="{p['light']}" stroke-width="10" opacity="0.45"/>
    <rect x="226" y="418" width="82" height="140" rx="34" fill="{p['body']}"/>
    <rect x="492" y="418" width="82" height="140" rx="34" fill="{p['body']}"/>
    <rect x="244" y="438" width="46" height="100" rx="23" fill="{p['accent']}" opacity="0.9"/>
    <rect x="510" y="438" width="46" height="100" rx="23" fill="{p['accent']}" opacity="0.9"/>
    <circle cx="267" cy="488" r="12" fill="{p['light']}" opacity="0.7"/>
    <circle cx="533" cy="488" r="12" fill="{p['light']}" opacity="0.7"/>
  </g>"""


def watch(p: Dict[str, str]) -> str:
    return f"""  <g>
    <rect x="352" y="188" width="96" height="150" rx="26" fill="{p['body']}" opacity="0.85"/>
    <rect x="352" y="462" width="96" height="150" rx="26" fill="{p['body']}" opacity="0.85"/>
    <rect x="304" y="292" width="192" height="216" rx="52" fill="{p['body']}"/>
    <rect x="324" y="312" width="152" height="176" rx="38" fill="{p['dark']}"/>
    <circle cx="400" cy="400" r="52" fill="none" stroke="{p['accent']}" stroke-width="10" opacity="0.9"/>
    <path d="M400 372 v30 l22 14" fill="none" stroke="{p['light']}" stroke-width="8" stroke-linecap="round"/>
    <rect x="496" y="366" width="16" height="42" rx="8" fill="{p['accent']}"/>
  </g>"""


def camera(p: Dict[str, str]) -> str:
    return f"""  <g>
    <rect x="318" y="238" width="120" height="42" rx="14" fill="{p['body']}" opacity="0.75"/>
    <rect x="226" y="272" width="348" height="248" rx="40" fill="{p['body']}"/>
    <circle cx="400" cy="396" r="94" fill="{p['dark']}"/>
    <circle cx="400" cy="396" r="66" fill="none" stroke="{p['accent']}" stroke-width="8" opacity="0.9"/>
    <circle cx="400" cy="396" r="40" fill="{p['light']}" opacity="0.18"/>
    <circle cx="374" cy="372" r="15" fill="{p['light']}" opacity="0.45"/>
    <circle cx="520" cy="318" r="16" fill="{p['accent']}"/>
    <rect x="252" y="306" width="60" height="14" rx="7" fill="{p['light']}" opacity="0.4"/>
  </g>"""


def tshirt(p: Dict[str, str]) -> str:
    return f"""  <g>
    <path d="M320 236 l-108 62 l52 96 l46 -26 v218 a16 16 0 0 0 16 16 h148 a16 16 0 0 0 16 -16 v-218 l46 26 l52 -96 l-108 -62 z" fill="{p['body']}"/>
    <path d="M320 236 a80 42 0 0 0 160 0" fill="none" stroke="{p['light']}" stroke-width="12" opacity="0.55"/>
    <rect x="356" y="392" width="88" height="88" rx="14" fill="{p['accent']}" opacity="0.85"/>
    <path d="M264 394 l40 -22" stroke="{p['light']}" stroke-width="8" opacity="0.3" stroke-linecap="round"/>
  </g>"""


def jeans(p: Dict[str, str]) -> str:
    return f"""  <g>
    <path d="M292 216 h216 l18 96 l-16 300 h-92 l-26 -228 l-26 228 h-92 l-16 -300 z" fill="{p['body']}"/>
    <rect x="292" y="216" width="216" height="42" rx="8" fill="{p['dark']}" opacity="0.35"/>
    <path d="M400 258 v122" stroke="{p['light']}" stroke-width="6" opacity="0.35"/>
    <path d="M318 292 h44 v40 h-44 z" fill="{p['light']}" opacity="0.18"/>
    <rect x="440" y="292" width="52" height="44" rx="8" fill="{p['accent']}" opacity="0.7"/>
  </g>"""


def sweater(p: Dict[str, str]) -> str:
    return f"""  <g>
    <g transform="rotate(32 294 292)">
      <rect x="254" y="272" width="80" height="252" rx="26" fill="{p['body']}"/>
      <rect x="254" y="490" width="80" height="34" rx="16" fill="{p['dark']}" opacity="0.35"/>
    </g>
    <g transform="rotate(-32 506 292)">
      <rect x="466" y="272" width="80" height="252" rx="26" fill="{p['body']}"/>
      <rect x="466" y="490" width="80" height="34" rx="16" fill="{p['dark']}" opacity="0.35"/>
    </g>
    <path d="M306 268 h188 a26 26 0 0 1 26 26 v300 a20 20 0 0 1 -20 20 h-200 a20 20 0 0 1 -20 -20 v-300 a26 26 0 0 1 26 -26 z" fill="{p['body']}"/>
    <path d="M348 268 a52 28 0 0 0 104 0" fill="none" stroke="{p['light']}" stroke-width="16" opacity="0.55"/>
    <rect x="286" y="566" width="228" height="48" rx="16" fill="{p['dark']}" opacity="0.28"/>
    <path d="M348 356 l52 62 l52 -62 M348 448 l52 62 l52 -62" fill="none" stroke="{p['accent']}" stroke-width="11" opacity="0.85" stroke-linecap="round"/>
  </g>"""


def sneaker(p: Dict[str, str]) -> str:
    return f"""  <g>
    <path d="M212 470 c0 -32 34 -40 66 -58 l70 -104 a20 20 0 0 1 30 -4 l52 46 l86 44 c56 28 78 46 78 80 v22 h-382 z" fill="{p['body']}"/>
    <path d="M206 492 h388 a18 18 0 0 1 18 18 v14 a18 18 0 0 1 -18 18 h-388 a18 18 0 0 1 -18 -18 v-14 a18 18 0 0 1 18 -18 z" fill="{p['light']}"/>
    <path d="M336 342 l38 34 M366 320 l40 36 M396 300 l42 38" stroke="{p['accent']}" stroke-width="11" stroke-linecap="round"/>
    <circle cx="512" cy="440" r="16" fill="{p['light']}" opacity="0.55"/>
  </g>"""


def espresso(p: Dict[str, str]) -> str:
    return f"""  <g>
    <rect x="240" y="196" width="320" height="180" rx="30" fill="{p['body']}"/>
    <rect x="240" y="520" width="320" height="86" rx="26" fill="{p['body']}"/>
    <rect x="256" y="376" width="72" height="144" fill="{p['body']}" opacity="0.9"/>
    <rect x="286" y="236" width="140" height="76" rx="14" fill="{p['dark']}"/>
    <circle cx="502" cy="274" r="26" fill="{p['accent']}"/>
    <rect x="392" y="376" width="80" height="26" rx="8" fill="{p['dark']}" opacity="0.8"/>
    <rect x="420" y="402" width="24" height="34" fill="{p['dark']}" opacity="0.6"/>
    <path d="M396 462 h96 l-14 58 h-68 z" fill="{p['light']}"/>
    <rect x="396" y="452" width="96" height="14" rx="7" fill="{p['light']}"/>
  </g>"""


def pourover(p: Dict[str, str]) -> str:
    return f"""  <g>
    <path d="M282 246 h236 l-66 112 h-104 z" fill="{p['light']}"/>
    <path d="M348 358 h104" stroke="{p['body']}" stroke-width="8" opacity="0.35"/>
    <rect x="272" y="228" width="256" height="26" rx="13" fill="{p['accent']}"/>
    <path d="M300 358 h200 a32 32 0 0 1 32 32 v106 a104 104 0 0 1 -104 104 h-56 a104 104 0 0 1 -104 -104 v-106 a32 32 0 0 1 32 -32 z" fill="{p['light']}" opacity="0.95"/>
    <path d="M268 486 h264 v10 a104 104 0 0 1 -104 104 h-56 a104 104 0 0 1 -104 -104 z" fill="{p['body']}"/>
    <path d="M532 396 h28 a48 48 0 0 1 0 96 h-28" fill="none" stroke="{p['light']}" stroke-width="20"/>
    <rect x="296" y="392" width="18" height="70" rx="9" fill="{p['light']}" opacity="0.6"/>
  </g>"""


def skillet(p: Dict[str, str]) -> str:
    return f"""  <g>
    <rect x="470" y="272" width="230" height="46" rx="23" fill="{p['body']}" transform="rotate(-24 470 272)"/>
    <circle cx="376" cy="452" r="176" fill="{p['body']}"/>
    <circle cx="376" cy="452" r="140" fill="{p['dark']}" opacity="0.55"/>
    <circle cx="376" cy="452" r="140" fill="none" stroke="{p['light']}" stroke-width="4" opacity="0.25"/>
    <circle cx="330" cy="404" r="34" fill="{p['light']}" opacity="0.12"/>
    <circle cx="640" cy="222" r="17" fill="none" stroke="{p['accent']}" stroke-width="10"/>
  </g>"""


def blanket(p: Dict[str, str]) -> str:
    return f"""  <g>
    <rect x="196" y="330" width="408" height="96" rx="24" fill="{p['body']}" opacity="0.65"/>
    <rect x="212" y="404" width="376" height="102" rx="24" fill="{p['body']}" opacity="0.85"/>
    <rect x="228" y="484" width="344" height="110" rx="26" fill="{p['body']}"/>
    <path d="M252 520 h296 M252 552 h296" stroke="{p['light']}" stroke-width="7" opacity="0.35"/>
    <path d="M244 594 v34 M292 594 v34 M340 594 v34 M388 594 v34 M436 594 v34 M484 594 v34 M532 594 v34" stroke="{p['accent']}" stroke-width="7" stroke-linecap="round" opacity="0.75"/>
  </g>"""


def book(p: Dict[str, str]) -> str:
    return f"""  <g>
    <rect x="268" y="176" width="272" height="452" rx="14" fill="{p['dark']}" opacity="0.18"/>
    <rect x="258" y="164" width="272" height="452" rx="14" fill="{p['body']}"/>
    <rect x="258" y="164" width="42" height="452" rx="14" fill="{p['dark']}" opacity="0.35"/>
    <rect x="530" y="180" width="16" height="420" rx="6" fill="{p['light']}"/>
    <rect x="336" y="248" width="150" height="18" rx="9" fill="{p['accent']}"/>
    <rect x="336" y="292" width="112" height="12" rx="6" fill="{p['light']}" opacity="0.7"/>
    <rect x="336" y="480" width="80" height="10" rx="5" fill="{p['light']}" opacity="0.5"/>
    <circle cx="412" cy="386" r="52" fill="none" stroke="{p['light']}" stroke-width="8" opacity="0.6"/>
  </g>"""


def backpack(p: Dict[str, str]) -> str:
    return f"""  <g>
    <path d="M300 250 a100 100 0 0 1 200 0 v40 h-40 v-40 a60 60 0 0 0 -120 0 v40 h-40 z" fill="{p['body']}" opacity="0.6"/>
    <rect x="240" y="256" width="320" height="352" rx="72" fill="{p['body']}"/>
    <rect x="272" y="396" width="256" height="140" rx="42" fill="{p['dark']}" opacity="0.28"/>
    <rect x="240" y="330" width="320" height="26" fill="{p['accent']}" opacity="0.85"/>
    <rect x="368" y="452" width="64" height="26" rx="13" fill="{p['light']}" opacity="0.75"/>
    <path d="M292 300 h72 M436 300 h72" stroke="{p['light']}" stroke-width="9" opacity="0.4" stroke-linecap="round"/>
  </g>"""


def yogamat(p: Dict[str, str]) -> str:
    return f"""  <g>
    <ellipse cx="556" cy="401" rx="44" ry="118" fill="{p['body']}"/>
    <rect x="300" y="283" width="256" height="236" fill="{p['body']}"/>
    <rect x="404" y="273" width="48" height="256" rx="8" fill="{p['accent']}" opacity="0.85"/>
    <ellipse cx="300" cy="401" rx="44" ry="118" fill="{p['light']}" opacity="0.95"/>
    <ellipse cx="300" cy="401" rx="30" ry="80" fill="none" stroke="{p['body']}" stroke-width="7" opacity="0.55"/>
    <ellipse cx="300" cy="401" rx="17" ry="45" fill="none" stroke="{p['body']}" stroke-width="7" opacity="0.45"/>
    <circle cx="300" cy="401" r="9" fill="{p['body']}" opacity="0.4"/>
    <rect x="404" y="273" width="48" height="12" rx="6" fill="{p['dark']}" opacity="0.3"/>
  </g>"""


def bottle(p: Dict[str, str]) -> str:
    return f"""  <g>
    <rect x="352" y="164" width="96" height="58" rx="16" fill="{p['dark']}" opacity="0.8"/>
    <rect x="344" y="212" width="112" height="34" rx="12" fill="{p['accent']}"/>
    <path d="M330 246 h140 a48 48 0 0 1 48 48 v266 a56 56 0 0 1 -56 56 h-124 a56 56 0 0 1 -56 -56 v-266 a48 48 0 0 1 48 -48 z" fill="{p['body']}"/>
    <rect x="282" y="366" width="236" height="120" fill="{p['light']}" opacity="0.9"/>
    <rect x="316" y="404" width="168" height="16" rx="8" fill="{p['accent']}" opacity="0.85"/>
    <rect x="316" y="436" width="112" height="12" rx="6" fill="{p['body']}" opacity="0.45"/>
    <rect x="306" y="270" width="18" height="72" rx="9" fill="{p['light']}" opacity="0.35"/>
  </g>"""


def poles(p: Dict[str, str]) -> str:
    return f"""  <g>
    <g transform="rotate(-9 400 400)">
      <rect x="316" y="188" width="26" height="120" rx="13" fill="{p['dark']}"/>
      <rect x="320" y="300" width="18" height="270" fill="{p['body']}"/>
      <rect x="316" y="286" width="26" height="18" rx="6" fill="{p['accent']}"/>
      <path d="M300 528 h58" stroke="{p['accent']}" stroke-width="12" stroke-linecap="round"/>
      <path d="M329 570 l-10 40 h20 z" fill="{p['dark']}"/>
    </g>
    <g transform="rotate(9 400 400)">
      <rect x="458" y="188" width="26" height="120" rx="13" fill="{p['dark']}"/>
      <rect x="462" y="300" width="18" height="270" fill="{p['body']}"/>
      <rect x="458" y="286" width="26" height="18" rx="6" fill="{p['accent']}"/>
      <path d="M442 528 h58" stroke="{p['accent']}" stroke-width="12" stroke-linecap="round"/>
      <path d="M471 570 l-10 40 h20 z" fill="{p['dark']}"/>
    </g>
  </g>"""


def dropper(p: Dict[str, str]) -> str:
    return f"""  <g>
    <rect x="368" y="146" width="64" height="86" rx="14" fill="{p['dark']}"/>
    <rect x="352" y="222" width="96" height="30" rx="10" fill="{p['accent']}"/>
    <path d="M330 252 h140 a34 34 0 0 1 34 34 v264 a52 52 0 0 1 -52 52 h-104 a52 52 0 0 1 -52 -52 v-264 a34 34 0 0 1 34 -34 z" fill="{p['body']}" opacity="0.9"/>
    <rect x="330" y="352" width="140" height="150" rx="12" fill="{p['light']}" opacity="0.92"/>
    <rect x="356" y="388" width="88" height="14" rx="7" fill="{p['accent']}"/>
    <rect x="356" y="418" width="66" height="10" rx="5" fill="{p['body']}" opacity="0.45"/>
    <rect x="356" y="444" width="76" height="10" rx="5" fill="{p['body']}" opacity="0.3"/>
  </g>"""


def mister(p: Dict[str, str]) -> str:
    return f"""  <g>
    <path d="M356 156 h74 a16 16 0 0 1 16 16 v22 h-90 z" fill="{p['dark']}"/>
    <path d="M446 168 h44 a12 12 0 0 1 12 12 v18" fill="none" stroke="{p['dark']}" stroke-width="14" stroke-linecap="round"/>
    <rect x="352" y="194" width="96" height="46" rx="10" fill="{p['accent']}" opacity="0.9"/>
    <path d="M336 240 h128 a40 40 0 0 1 40 40 v250 a58 58 0 0 1 -58 58 h-92 a58 58 0 0 1 -58 -58 v-250 a40 40 0 0 1 40 -40 z" fill="{p['body']}" opacity="0.88"/>
    <rect x="296" y="356" width="208" height="132" rx="10" fill="{p['light']}" opacity="0.9"/>
    <rect x="326" y="396" width="120" height="14" rx="7" fill="{p['accent']}"/>
    <rect x="326" y="428" width="88" height="10" rx="5" fill="{p['body']}" opacity="0.4"/>
    <circle cx="546" cy="196" r="7" fill="{p['accent']}" opacity="0.8"/>
    <circle cx="576" cy="176" r="5" fill="{p['accent']}" opacity="0.6"/>
    <circle cx="566" cy="222" r="4" fill="{p['accent']}" opacity="0.5"/>
  </g>"""


def jar(p: Dict[str, str]) -> str:
    return f"""  <g>
    <rect x="262" y="238" width="276" height="86" rx="26" fill="{p['dark']}"/>
    <rect x="286" y="252" width="228" height="20" rx="10" fill="{p['light']}" opacity="0.28"/>
    <path d="M282 324 h236 a34 34 0 0 1 34 34 v146 a90 90 0 0 1 -90 90 h-124 a90 90 0 0 1 -90 -90 v-146 a34 34 0 0 1 34 -34 z" fill="{p['body']}"/>
    <rect x="266" y="398" width="268" height="118" rx="12" fill="{p['light']}" opacity="0.9"/>
    <rect x="304" y="430" width="140" height="16" rx="8" fill="{p['accent']}"/>
    <rect x="304" y="464" width="96" height="12" rx="6" fill="{p['body']}" opacity="0.4"/>
  </g>"""


def lamp(p: Dict[str, str]) -> str:
    return f"""  <g>
    <ellipse cx="300" cy="606" rx="118" ry="28" fill="{p['body']}"/>
    <rect x="286" y="352" width="28" height="248" rx="14" fill="{p['body']}"/>
    <path d="M300 360 l176 -74" fill="none" stroke="{p['body']}" stroke-width="26" stroke-linecap="round"/>
    <circle cx="300" cy="360" r="20" fill="{p['dark']}" opacity="0.55"/>
    <g transform="rotate(28 500 300)">
      <path d="M456 254 h88 l40 96 h-168 z" fill="{p['body']}"/>
      <ellipse cx="500" cy="350" rx="84" ry="16" fill="{p['accent']}" opacity="0.9"/>
    </g>
    <ellipse cx="548" cy="432" rx="122" ry="62" fill="{p['accent']}" opacity="0.14"/>
  </g>"""


def brushes(p: Dict[str, str]) -> str:
    return f"""  <g>
    <g transform="rotate(-12 340 400)">
      <rect x="312" y="196" width="46" height="150" rx="20" fill="{p['dark']}" opacity="0.85"/>
      <rect x="314" y="336" width="42" height="34" fill="{p['accent']}"/>
      <rect x="318" y="366" width="34" height="240" rx="17" fill="{p['body']}"/>
    </g>
    <g transform="rotate(6 460 400)">
      <ellipse cx="470" cy="252" rx="40" ry="60" fill="{p['dark']}" opacity="0.7"/>
      <rect x="450" y="304" width="40" height="30" fill="{p['accent']}"/>
      <rect x="454" y="330" width="32" height="272" rx="16" fill="{p['body']}"/>
    </g>
    <path d="M244 640 h312" stroke="{p['dark']}" stroke-width="8" opacity="0.12" stroke-linecap="round"/>
  </g>"""


SHAPES: Dict[str, Callable[[Dict[str, str]], str]] = {
    "laptop": laptop,
    "headphones": headphones,
    "watch": watch,
    "camera": camera,
    "tshirt": tshirt,
    "jeans": jeans,
    "sweater": sweater,
    "sneaker": sneaker,
    "espresso": espresso,
    "pourover": pourover,
    "skillet": skillet,
    "blanket": blanket,
    "book": book,
    "backpack": backpack,
    "yogamat": yogamat,
    "bottle": bottle,
    "poles": poles,
    "dropper": dropper,
    "mister": mister,
    "jar": jar,
    "brushes": brushes,
    "lamp": lamp,
}

# ── Catalogue → artwork mapping ────────────────────────────────────────────
# (slug, shape, number of shots). Kept in sync with PRODUCTS in seed.py.
CATALOGUE: List[tuple] = [
    ("probook-laptop-15", "laptop", 3),
    ("soundmax-wireless-headphones", "headphones", 3),
    ("pulse-smartwatch-series-5", "watch", 2),
    ("lumen-4k-action-camera", "camera", 2),
    ("classic-cotton-tshirt", "tshirt", 3),
    ("slim-fit-jeans", "jeans", 2),
    ("alpine-wool-sweater", "sweater", 2),
    ("everyday-canvas-sneakers", "sneaker", 3),
    ("barista-pro-espresso-machine", "espresso", 3),
    ("ceramic-pour-over-set", "pourover", 2),
    ("cast-iron-skillet-12", "skillet", 2),
    ("linen-throw-blanket", "blanket", 2),
    ("the-lost-horizon", "book", 2),
    ("atlas-of-quiet-places", "book", 2),
    ("the-pragmatic-kitchen", "book", 2),
    ("foundations-of-modern-design", "book", 2),
    ("trailhead-45l-backpack", "backpack", 3),
    ("grip-pro-yoga-mat", "yogamat", 2),
    ("summit-insulated-bottle-1l", "bottle", 2),
    ("carbon-trekking-poles", "poles", 2),
    ("botanical-face-serum", "dropper", 3),
    ("rosewater-hydrating-mist", "mister", 2),
    ("clay-purifying-mask", "jar", 2),
    ("bamboo-bristle-brush-set", "brushes", 2),
    ("aurora-desk-lamp", "lamp", 2),
]


def render(slug: str, shape: str, index: int) -> str:
    p = palette_for(slug, index)
    # Alternate shots are framed slightly differently so a gallery feels like
    # more than one photograph of the same object.
    scale = [1.0, 0.88, 1.06][index % 3]
    rotate = [0, -6, 5][index % 3]
    inner = SHAPES[shape](p)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SIZE} {SIZE}" width="{SIZE}" height="{SIZE}" role="img">\n'
        f"{_chrome(p, index)}\n"
        f'  <g transform="translate(400 400) rotate({rotate}) scale({scale}) translate(-400 -400)">\n'
        f"{inner}\n"
        f"  </g>\n"
        f"</svg>\n"
    )


def main() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    written = 0
    for slug, shape, shots in CATALOGUE:
        for i in range(shots):
            path = os.path.join(OUTPUT_DIR, f"{slug}-{i + 1}.svg")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(render(slug, shape, i))
            written += 1
    print(f"Wrote {written} product images to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera os banners SVG animados do README (tema ASCII / vermelho).

- Hero, Sobre, Contato, Stacks, Stats e Footer
- Icones reais das tecnologias (Simple Icons, embutidos no SVG)
- Estatisticas do GitHub via github-readme-stats / streak-stats
  (com fallback para scripts/stats.json)

Uso: python scripts/build_banners.py
"""
from __future__ import annotations

import datetime as dt
import html
import json
import random
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
SCRIPTS = ROOT / "scripts"
ASSETS.mkdir(exist_ok=True)

ICONS = json.loads((SCRIPTS / "icons.json").read_text(encoding="utf-8"))

# ---------------------------------------------------------------------------
# Fonte ASCII 5x5
# ---------------------------------------------------------------------------
FONT = {
    " ": ["     "] * 5,
    "A": [" ### ", "#   #", "#####", "#   #", "#   #"],
    "B": ["#### ", "#   #", "#### ", "#   #", "#### "],
    "C": [" ####", "#    ", "#    ", "#    ", " ####"],
    "D": ["#### ", "#   #", "#   #", "#   #", "#### "],
    "E": ["#####", "#    ", "#### ", "#    ", "#####"],
    "F": ["#####", "#    ", "#### ", "#    ", "#    "],
    "G": [" ####", "#    ", "#  ##", "#   #", " ####"],
    "H": ["#   #", "#   #", "#####", "#   #", "#   #"],
    "I": ["#####", "  #  ", "  #  ", "  #  ", "#####"],
    "J": ["  ###", "   # ", "   # ", "#  # ", " ##  "],
    "K": ["#   #", "#  # ", "###  ", "#  # ", "#   #"],
    "L": ["#    ", "#    ", "#    ", "#    ", "#####"],
    "M": ["#   #", "## ##", "# # #", "#   #", "#   #"],
    "N": ["#   #", "##  #", "# # #", "#  ##", "#   #"],
    "O": [" ### ", "#   #", "#   #", "#   #", " ### "],
    "P": ["#### ", "#   #", "#### ", "#    ", "#    "],
    "Q": [" ### ", "#   #", "# # #", "#  # ", " ## #"],
    "R": ["#### ", "#   #", "#### ", "#  # ", "#   #"],
    "S": [" ####", "#    ", " ### ", "    #", "#### "],
    "T": ["#####", "  #  ", "  #  ", "  #  ", "  #  "],
    "U": ["#   #", "#   #", "#   #", "#   #", " ### "],
    "V": ["#   #", "#   #", "#   #", " # # ", "  #  "],
    "W": ["#   #", "#   #", "# # #", "## ##", "#   #"],
    "X": ["#   #", " # # ", "  #  ", " # # ", "#   #"],
    "Y": ["#   #", " # # ", "  #  ", "  #  ", "  #  "],
    "Z": ["#####", "   # ", "  #  ", " #   ", "#####"],
}
MONO = "'Cascadia Code',Consolas,'Courier New',monospace"


def art(text: str) -> list[str]:
    rows = [""] * 5
    for i, ch in enumerate(text.upper()):
        glyph = FONT.get(ch, FONT[" "])
        for r in range(5):
            rows[r] += (" " if i else "") + glyph[r]
    return rows


def esc(text: str) -> str:
    return html.escape(text, quote=False)


# ---------------------------------------------------------------------------
# CSS / defs / camadas comuns
# ---------------------------------------------------------------------------
COMMON_CSS = """
    @keyframes liquidA {
      0%, 100% { transform: translate(-2px, -7px); opacity: .32; }
      50%      { transform: translate(2px, 7px); opacity: .88; }
    }
    @keyframes liquidB {
      0%, 100% { transform: translate(3px, -11px); opacity: .26; }
      50%      { transform: translate(-3px, 11px); opacity: .72; }
    }
    @keyframes liquidC {
      0%, 100% { transform: translate(-3px, -5px); opacity: .5; }
      50%      { transform: translate(3px, 5px); opacity: 1; }
    }
    @keyframes jitterA {
      0%, 88%, 100% { transform: translate(0, 0); }
      89% { transform: translate(-4px, 2px); }
      90% { transform: translate(3px, -2px); }
      91% { transform: translate(-2px, 1px); }
      92% { transform: translate(0, 0); }
    }
    @keyframes jitterB {
      0%, 84%, 100% { transform: translate(0, 0); }
      85% { transform: translate(4px, -2px); }
      86% { transform: translate(-3px, 2px); }
      87% { transform: translate(2px, 1px); }
      88% { transform: translate(0, 0); }
    }
    @keyframes floaty {
      0%, 100% { transform: translateY(0); }
      50% { transform: translateY(-4px); }
    }
    @keyframes pulse {
      0%, 100% { opacity: .18; }
      50% { opacity: .55; }
    }
    @keyframes blink {
      0%, 49% { opacity: 1; }
      50%, 100% { opacity: 0; }
    }
    @keyframes flicker {
      0%, 96%, 100% { opacity: .85; }
      97% { opacity: .25; }
      98% { opacity: 1; }
      99% { opacity: .45; }
    }
    @media (prefers-reduced-motion: reduce) {
      * { animation: none !important; }
    }
"""


def defs(H: int, extra: str = "", W: int = 1200) -> str:
    return f'''<defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#070001"/>
      <stop offset="0.55" stop-color="#0d0004"/>
      <stop offset="1" stop-color="#160007"/>
    </linearGradient>
    <radialGradient id="glow" cx="0.5" cy="0.18" r="0.78">
      <stop offset="0" stop-color="#ff0033" stop-opacity="0.20"/>
      <stop offset="0.55" stop-color="#8b0016" stop-opacity="0.08"/>
      <stop offset="1" stop-color="#000000" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="titleGrad" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#ff4d6d"/>
      <stop offset="0.35" stop-color="#ff0033"/>
      <stop offset="0.65" stop-color="#ff3355"/>
      <stop offset="1" stop-color="#b3001b"/>
    </linearGradient>
    <linearGradient id="barGrad" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#b3001b"/>
      <stop offset="0.55" stop-color="#ff0033"/>
      <stop offset="1" stop-color="#ff6680"/>
    </linearGradient>
    <linearGradient id="sweep" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#ff0033" stop-opacity="0"/>
      <stop offset="0.5" stop-color="#ff4d6d" stop-opacity="0.55"/>
      <stop offset="1" stop-color="#ff0033" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="scanY" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#ff0033" stop-opacity="0"/>
      <stop offset="0.5" stop-color="#ff4d6d" stop-opacity="0.20"/>
      <stop offset="1" stop-color="#ff0033" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="tile" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#1b0009"/>
      <stop offset="1" stop-color="#0a0003"/>
    </linearGradient>
    <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
      <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#ff0033" stroke-width="0.6" opacity="0.05"/>
    </pattern>
    <pattern id="scan" width="1" height="4" patternUnits="userSpaceOnUse">
      <rect width="1" height="1" fill="#ff0033" opacity="0.055"/>
    </pattern>
    <clipPath id="frame"><rect x="0" y="0" width="{W}" height="{H}"/></clipPath>
    <style><![CDATA[
{COMMON_CSS}
    ]]></style>
    {extra}
  </defs>'''


def liquid(W: int, H: int, seed: int, lo: float = 0.10, hi: float = 0.28) -> str:
    """Campo ASCII liquido cobrindo toda a tela: malha de caracteres em onda 2D."""
    random.seed(seed)
    out: list[str] = []

    # malha dimensionada para preencher o banner inteiro
    cell_w = max(36.0, ((W * H) / 560 * 1.4) ** 0.5)
    cell_h = cell_w * 0.62
    font = max(13, round(cell_w * 0.38))
    cols = int(W / cell_w) + 2
    rows = int(H / cell_h) + 2
    chars = "~≈~-_.=+~<>|~"
    palette = ["#6b0012", "#8b0016", "#a8001d", "#c40024", "#ff2d55"]

    # onda diagonal coerente: fase cresce com x e y, entao as cristas viajam
    period = 9.0
    lam_x = W / 2.3
    lam_y = H / 1.7

    for r in range(rows):
        for c in range(cols):
            x = c * cell_w
            y = r * cell_h + cell_h * 0.78
            seq = "".join(random.choice(chars) for _ in range(5))
            phase = ((x / lam_x) + (y / lam_y)) * period + random.uniform(-0.3, 0.3)
            delay = -((phase % period))
            kind = (c * 7 + r * 5) % 13
            patch = (r // 6 + c // 8) % 4 == 0
            if kind == 0:
                cls, fill, fop = "liquidC", "#ff4d6d", round(random.uniform(0.3, 0.6), 2)
            elif patch:
                cls, fill, fop = "liquidB", "#8b0016", round(random.uniform(0.14, 0.4), 2)
            else:
                cls, fill, fop = (
                    "liquidA",
                    random.choice(palette),
                    round(random.uniform(max(0.08, lo * 1.1), max(0.16, hi * 1.6)), 2),
                )
            out.append(
                f'<g style="animation: {cls} {period}s ease-in-out infinite; animation-delay: {delay:.2f}s;">'
                f'<text x="{x:.1f}" y="{y:.1f}" font-family="{MONO}" font-size="{font}" fill="{fill}" '
                f'fill-opacity="{fop}" textLength="{cell_w + 0.5:.1f}" lengthAdjust="spacingAndGlyphs" '
                f'xml:space="preserve">{esc(seq)}</text></g>'
            )

    # --- espuma: gotas soltas cintilando ---
    for _ in range(max(3, int(W / 90))):
        out.append(
            f'<text x="{random.uniform(20, W - 20):.1f}" y="{random.uniform(16, H - 16):.1f}" '
            f'font-family="{MONO}" font-size="{random.choice([9, 10, 11])}" fill="#ff8fa3" '
            f'fill-opacity="{round(random.uniform(0.16, 0.42), 2)}" xml:space="preserve" '
            f'style="animation: floaty {round(random.uniform(4, 9), 1)}s ease-in-out infinite; '
            f'animation-delay: -{round(random.uniform(0, 8), 1)}s;">'
            f'{esc(random.choice(["·", "+", ".", ":", "≈"]))}</text>'
        )

    return f'<g clip-path="url(#frame)">{"".join(out)}</g>'


def backdrop(W: int, H: int, seed: int, lo: float = 0.10, hi: float = 0.28) -> str:
    return f'''
  <rect width="{W}" height="{H}" fill="url(#bg)"/>
  <rect width="{W}" height="{H}" fill="url(#glow)"/>
  <rect width="{W}" height="{H}" fill="url(#grid)"/>
  {liquid(W, H, seed, lo, hi)}
'''


def scanlines(W: int, H: int) -> str:
    return f'<rect width="{W}" height="{H}" fill="url(#scan)" pointer-events="none"/>'


def sweep(W: int, H: int, dur: int = 8) -> str:
    return (
        f'<rect x="-260" y="0" width="260" height="{H}" fill="url(#sweep)" opacity="0.11">'
        f'<animate attributeName="x" values="-260;{W + 60}" dur="{dur}s" repeatCount="indefinite"/>'
        f"</rect>"
    )


def scan_bar(W: int, H: int, dur: int = 8) -> str:
    return (
        f'<rect x="0" y="-110" width="{W}" height="110" fill="url(#scanY)" opacity="0.16">'
        f'<animate attributeName="y" values="-110;{H}" dur="{dur}s" repeatCount="indefinite"/>'
        f"</rect>"
    )


def corners(W: int, H: int, lt: str, rt: str, lb: str, rb: str) -> str:
    return f'''<g font-family="{MONO}" font-size="13" fill="#ff2d55" opacity="0.82">
    <text x="22" y="30" xml:space="preserve">+--[ {esc(lt)} ]</text>
    <text x="{W - 22}" y="30" text-anchor="end" xml:space="preserve">[ {esc(rt)} ]--+</text>
    <text x="22" y="{H - 14}" xml:space="preserve">+--[ {esc(lb)} ]</text>
    <text x="{W - 22}" y="{H - 14}" text-anchor="end" xml:space="preserve">[ {esc(rb)} ]--+</text>
  </g>'''


def ascii_group(
    text: str,
    W: int,
    size: int,
    lh: int,
    top: int,
    main_fill: str = "url(#titleGrad)",
    weight: int = 700,
) -> str:
    rows = art(text)

    def layer(fill: str, opacity: str, anim: str) -> str:
        body = "".join(
            f'<text x="{W / 2:.1f}" y="{top + i * lh}" text-anchor="middle" '
            f'xml:space="preserve">{esc(row)}</text>'
            for i, row in enumerate(rows)
        )
        return f'<g fill="{fill}" opacity="{opacity}" style="animation: {anim};">{body}</g>'

    return (
        f'<g font-family="{MONO}" font-size="{size}" font-weight="{weight}" letter-spacing="0">'
        f'{layer("#6b0012", "0.55", "jitterA 6s steps(1) infinite")}'
        f'{layer("#ff6680", "0.20", "jitterB 8s steps(1) infinite")}'
        f'{layer(main_fill, "1", "jitterA 9s steps(1) infinite")}'
        f"</g>"
    )


def icon_paths(key: str, fill: str = "#ffffff") -> str:
    paths = "".join(f'<path d="{d}"/>' for d in ICONS[key]["paths"])
    return f'<g fill="{fill}">{paths}</g>'


def icon_at(key: str, x: float, y: float, size: float, fill: str = "#ffffff") -> str:
    s = size / 24.0
    return f'<g transform="translate({x:.2f},{y:.2f}) scale({s:.5f})">{icon_paths(key, fill)}</g>'


def typing_mask(mid: str, x: float, y: float, width: float, begin: float, dur: float = 0.5) -> str:
    return (
        f'<mask id="{mid}" maskUnits="userSpaceOnUse" x="0" y="0" width="1400" height="1200">'
        f'<rect x="{x}" y="{y}" width="0" height="26" fill="#ffffff">'
        f'<animate attributeName="width" from="0" to="{width}" begin="{begin:.2f}s" '
        f'dur="{dur:.2f}s" fill="freeze"/></rect></mask>'
    )


def svg_doc(W: int, H: int, title: str, desc: str, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t d">
  <title id="t">{esc(title)}</title>
  <desc id="d">{esc(desc)}</desc>
  {body}
</svg>'''


def write(name: str, content: str) -> None:
    (ASSETS / name).write_text(content, encoding="utf-8", newline="\n")
    print(f"  {name:28} {len(content):>7} bytes")


# ---------------------------------------------------------------------------
# 1. HERO
# ---------------------------------------------------------------------------
def banner_hero() -> str:
    W, H = 1200, 560
    title = ascii_group("JACYANE", W, 26, 29, 118)
    handle = "@Izzieee"
    handle_layers = f'''
  <g font-family="{MONO}" font-size="40" font-weight="700" letter-spacing="1">
    <text x="603" y="296" text-anchor="middle" fill="#6b0012" opacity=".55"
          style="animation: jitterA 5s steps(1) infinite;">{handle}</text>
    <text x="597" y="294" text-anchor="middle" fill="#ff6680" opacity=".22"
          style="animation: jitterB 7s steps(1) infinite;">{handle}</text>
    <text x="600" y="295" text-anchor="middle" fill="url(#titleGrad)">{handle}</text>
  </g>
  <rect x="724" y="272" width="10" height="28" fill="#ff2d55" opacity="0">
    <animate attributeName="opacity" values="0;1;0;1;0" dur="1.1s" repeatCount="indefinite"/>
  </rect>'''

    chips = [
        "ENG. DE SOFTWARE",
        "SISTEMAS P/ INTERNET",
        "CIBERSEGURANÇA",
    ]
    chip_w = [len(c) * 7.6 + 30 for c in chips]
    total = sum(chip_w) + 14 * (len(chips) - 1)
    cx = (W - total) / 2
    chip_svg = []
    for c, cw in zip(chips, chip_w):
        chip_svg.append(
            f'<g><rect x="{cx:.1f}" y="382" width="{cw:.1f}" height="38" rx="7" '
            f'fill="#12000a" stroke="#6b0012" stroke-width="1"/>'
            f'<text x="{cx + cw / 2:.1f}" y="406" text-anchor="middle" font-family="{MONO}" '
            f'font-size="12.5" letter-spacing="1.4" fill="#ffb3c0">{esc(c)}</text></g>'
        )
        cx += cw + 14

    mask = typing_mask("heroType", 250, 468, 700, 2.1, 1.1)
    body = f'''
  {defs(H, mask)}
  {backdrop(W, H, 17, 0.10, 0.30)}
  <ellipse cx="600" cy="160" rx="430" ry="140" fill="#080002" opacity="0.55"/>
  {corners(W, H, "ASCII.BANNER v2.0", "SYS.ONLINE", "EOF", "0xIZZIE")}
  {title}

  <rect x="438" y="246" width="324" height="66" rx="10" fill="#100008" opacity=".92" stroke="#8b0016" stroke-width="1.5"/>
  {handle_layers}

  <text x="600" y="350" text-anchor="middle" font-family="{MONO}" font-size="15"
        letter-spacing="2.6" fill="#ff8fa3" xml:space="preserve">// SOFTWARE ENGINEERING · CYBERSECURITY &amp; NETWORKS //</text>

  {''.join(chip_svg)}

  <g mask="url(#heroType)" font-family="{MONO}" font-size="14" fill="#ffb3c0" text-anchor="middle">
    <text x="600" y="486" xml:space="preserve">$ echo "aprendendo · construindo · compartilhando"</text>
  </g>
  <rect x="824" y="472" width="9" height="18" fill="#ff2d55" opacity="0">
    <animate attributeName="opacity" values="0;1;0;1;0" dur="1.1s" begin="3.4s" repeatCount="indefinite"/>
  </rect>

  {sweep(W, H, 8)}
  {scanlines(W, H)}
  <rect x="0" y="0" width="{W}" height="2" fill="#ff0033" opacity="0.35"
        style="animation: flicker 6s steps(1) infinite;"/>
'''
    return svg_doc(
        W,
        H,
        "Jacyane Martins — @Izzieee",
        "Banner ASCII animado com o nome Jacyane, o usuario @Izzieee, engenharia de software, ciberseguranca e redes.",
        body,
    )


# ---------------------------------------------------------------------------
# 2. SOBRE
# ---------------------------------------------------------------------------
def banner_sobre() -> str:
    W, H = 1200, 590
    title = ascii_group("SOBRE MIM", W, 22, 26, 80)
    lines = [
        "Engenharia de Software — ULBRA",
        "Sistemas para Internet — IFTO",
        "Aprendendo linguagens de programação e desenvolvimento web",
        "Estudos, artigos e projetos de extensão",
        "Carreira em cibersegurança ou redes",
    ]
    masks, texts = [], []
    for i, line in enumerate(lines):
        mid = f"sbm{i}"
        y = 312 + i * 34
        masks.append(typing_mask(mid, 100, y - 20, 1010, 1.25 + i * 0.48, 0.42))
        texts.append(
            f'<text x="108" y="{y}" font-family="{MONO}" font-size="18" mask="url(#{mid})" xml:space="preserve">'
            f'<tspan fill="#ff2d55" font-weight="700">[+]</tspan>'
            f'<tspan fill="#ffb3c0"> {esc(line)}</tspan></text>'
        )

    body = f'''
  {defs(H, "".join(masks))}
  {backdrop(W, H, 29, 0.09, 0.24)}
  {corners(W, H, "SEC.01", "SOBRE", "HISTORY", "05 LINHAS")}
  {title}

  <text x="600" y="218" text-anchor="middle" font-family="{MONO}" font-size="13"
        letter-spacing="2.4" fill="#ff8fa3" xml:space="preserve">// whoami --verbose</text>

  <g>
    <rect x="70" y="246" width="1060" height="310" rx="9" fill="#0a0003" opacity="0.93" stroke="#8b0016" stroke-width="1.5"/>
    <rect x="70" y="246" width="1060" height="30" rx="9" fill="#1a0008"/>
    <rect x="70" y="262" width="1060" height="14" fill="#1a0008"/>
    <line x1="70" y1="276" x2="1130" y2="276" stroke="#8b0016" stroke-width="1"/>
    <g fill="#ff2d55">
      <rect x="88" y="257" width="8" height="8" rx="1"/>
      <rect x="104" y="257" width="8" height="8" rx="1" opacity=".55"/>
      <rect x="120" y="257" width="8" height="8" rx="1" opacity=".3"/>
    </g>
    <text x="142" y="267" font-family="{MONO}" font-size="12" fill="#ff8fa3" opacity=".9"
          xml:space="preserve">izzie@ascii:~$ cat sobre.log</text>
    <text x="1100" y="267" text-anchor="end" font-family="{MONO}" font-size="11" fill="#8b0016"
          xml:space="preserve">zsh · utf-8</text>
    {''.join(texts)}

    <text x="100" y="512" font-family="{MONO}" font-size="12" fill="#ff8fa3"
          xml:space="preserve">// em construção_</text>
    <rect x="100" y="522" width="1000" height="10" rx="4" fill="#150007" stroke="#6b0012" stroke-width="1"/>
    <rect x="100" y="522" width="220" height="10" rx="4" fill="url(#barGrad)" opacity=".9">
      <animate attributeName="x" values="100;880;100" dur="5s" repeatCount="indefinite"/>
    </rect>
  </g>

  {sweep(W, H, 9)}
  {scanlines(W, H)}
  <rect x="0" y="0" width="{W}" height="2" fill="#ff0033" opacity="0.35"
        style="animation: flicker 7s steps(1) infinite;"/>
'''
    return svg_doc(
        W,
        H,
        "Sobre mim",
        "Banner animado com formacao em Engenharia de Software na ULBRA, Sistemas para Internet no IFTO, estudos, projetos de extensao e interesse em ciberseguranca e redes.",
        body,
    )


# ---------------------------------------------------------------------------
# 3. CONTATO (cabecalho + cards)
# ---------------------------------------------------------------------------
def banner_contato() -> str:
    W, H = 1200, 230
    title = ascii_group("CONTATO", W, 26, 29, 50)
    body = f'''
  {defs(H)}
  {backdrop(W, H, 41, 0.08, 0.22)}
  {corners(W, H, "SEC.02", "CONTATO", "OPEN", "04 CANAIS")}
  {title}
  <text x="600" y="200" text-anchor="middle" font-family="{MONO}" font-size="14"
        letter-spacing="2.2" fill="#ff8fa3" xml:space="preserve">// instagram · discord · gmail · linkedin</text>
  {sweep(W, H, 7)}
  {scanlines(W, H)}
'''
    return svg_doc(
        W,
        H,
        "Contato",
        "Banner ASCII animado da secao de contato com Instagram, Discord, Gmail e LinkedIn.",
        body,
    )


def contact_card(key: str, label: str, handle: str, sub: str, index: str) -> str:
    W, H = 240, 240
    handle_lines = [handle] if not sub else [handle, sub]
    hy = 168 if len(handle_lines) == 1 else 160
    handles = "".join(
        f'<text x="120" y="{hy + i * 17}" text-anchor="middle" font-family="{MONO}" '
        f'font-size="12.5" fill="#ffb3c0">{esc(h)}</text>'
        for i, h in enumerate(handle_lines)
    )
    dash_y = 196 if len(handle_lines) == 1 else 190
    prompt_y = 220
    body = f'''
  {defs(H)}
  {backdrop(W, H, 60 + int(index), 0.05, 0.16)}
  <rect x="6" y="6" width="228" height="228" rx="12" fill="#0c0003" opacity=".94" stroke="#6b0012" stroke-width="1.4"/>
  <rect x="6" y="6" width="228" height="228" rx="12" fill="none" stroke="#ff0033" stroke-width="1.2"
        opacity=".2" style="animation: pulse 3.4s ease-in-out infinite; animation-delay: -{int(index) * 0.45}s;"/>
  <g font-family="{MONO}" font-size="9.5" fill="#ff2d55" opacity=".8">
    <text x="18" y="24" xml:space="preserve">+--[ SOCIAL ]</text>
    <text x="222" y="24" text-anchor="end" xml:space="preserve">[ {index} ]--+</text>
  </g>
  <rect x="84" y="38" width="72" height="72" rx="15" fill="url(#tile)" stroke="#8b0016" stroke-width="1.3"/>
  <rect x="84" y="38" width="72" height="72" rx="15" fill="none" stroke="#ff0033" stroke-width="1"
        opacity=".25" style="animation: pulse 3s ease-in-out infinite; animation-delay: -{int(index) * 0.5}s;"/>
  <g style="animation: floaty 4.2s ease-in-out infinite; animation-delay: -{int(index) * 0.6}s;">
    {icon_at(key, 100, 54, 40, "#ffffff")}
  </g>
  <text x="120" y="142" text-anchor="middle" font-family="{MONO}" font-size="16" font-weight="700"
        letter-spacing="2" fill="url(#titleGrad)">{esc(label)}</text>
  {handles}
  <line x1="24" y1="{dash_y}" x2="216" y2="{dash_y}" stroke="#6b0012" stroke-dasharray="4 6" opacity=".7"/>
  <text x="24" y="{prompt_y}" font-family="{MONO}" font-size="9.5" letter-spacing="1.2"
        fill="#ff8fa3" xml:space="preserve">&gt; abrir perfil</text>
  <rect x="198" y="{prompt_y - 9}" width="8" height="11" fill="#ff2d55" opacity="0">
    <animate attributeName="opacity" values="0;1;0;1;0" dur="1.2s" begin="{0.8 + int(index) * 0.2}s" repeatCount="indefinite"/>
  </rect>
  {scanlines(W, H)}
'''
    return svg_doc(W, H, f"{label} — {handle}", f"Card animado de contato: {label}, {handle}.", body)


# ---------------------------------------------------------------------------
# 4. STACKS
# ---------------------------------------------------------------------------
STACK_ROWS = [
    (
        "LINGUAGENS & WEB",
        [
            ("css", "CSS"),
            ("html5", "HTML"),
            ("javascript", "JS"),
            ("typescript", "TS"),
            ("java", "Java"),
            ("python", "Python"),
            ("haskell", "Haskell"),
            ("markdown", "Markdown"),
            ("powershell", "PowerShell"),
        ],
    ),
    (
        "FRAMEWORKS & RUNTIME",
        [
            ("vue", "Vue.js"),
            ("node", "Node.js"),
            ("vite", "Vite"),
            ("npm", "NPM"),
        ],
    ),
    (
        "BANCOS DE DADOS",
        [
            ("sqlserver", "SQL Server"),
            ("mysql", "MySQL"),
            ("sqlite", "SQLite"),
        ],
    ),
    (
        "DEVOPS & FERRAMENTAS",
        [
            ("git", "Git"),
            ("github", "GitHub"),
            ("gitlab", "GitLab"),
            ("actions", "Actions"),
            ("docker", "Docker"),
            ("netlify", "Netlify"),
            ("terminal", "Terminal"),
        ],
    ),
    (
        "PRODUTIVIDADE & DESIGN",
        [
            ("canva", "Canva"),
            ("figma", "Figma"),
            ("notion", "Notion"),
            ("prettier", "Prettier"),
            ("sonarqube", "SonarQube"),
        ],
    ),
]


def banner_stacks() -> str:
    W, H = 1200, 1040
    title = ascii_group("STACKS", W, 28, 31, 80)
    rows_svg = []
    for r, (label, items) in enumerate(STACK_ROWS):
        top = 285 + r * 142
        spacing = 105
        total = (len(items) - 1) * spacing
        start = (W - total) / 2
        rows_svg.append(
            f'<text x="70" y="{top + 18}" font-family="{MONO}" font-size="13" letter-spacing="2" '
            f'fill="#ff2d55" xml:space="preserve">▸ {esc(label)}</text>'
            f'<text x="1130" y="{top + 18}" text-anchor="end" font-family="{MONO}" font-size="12" '
            f'fill="#8b0016" xml:space="preserve">[ {len(items):02d} ]</text>'
            f'<line x1="70" y1="{top + 25}" x2="1130" y2="{top + 25}" stroke="#6b0012" '
            f'stroke-dasharray="4 7" opacity=".55"/>'
        )
        for i, (key, name) in enumerate(items):
            cx = start + i * spacing
            delay = -((i * 0.37 + r * 0.21) % 4)
            rows_svg.append(
                f'<g transform="translate({cx:.2f},{top + 38})">'
                f'<rect x="-31" y="0" width="62" height="62" rx="11" fill="url(#tile)" stroke="#6b0012" stroke-width="1.2"/>'
                f'<rect x="-31" y="0" width="62" height="62" rx="11" fill="none" stroke="#ff0033" stroke-width="1" '
                f'opacity=".18" style="animation: pulse 3.6s ease-in-out infinite; animation-delay: {delay:.2f}s;"/>'
                f'<g style="animation: floaty 4.4s ease-in-out infinite; animation-delay: {delay:.2f}s;">'
                f'{icon_at(key, -21, 10, 42, "#ffffff")}'
                f"</g></g>"
                f'<text x="{cx:.2f}" y="{top + 120}" text-anchor="middle" font-family="{MONO}" '
                f'font-size="14.5" fill="#ffb3c0">{esc(name)}</text>'
            )

    body = f'''
  {defs(H)}
  {backdrop(W, H, 73, 0.07, 0.20)}
  {corners(W, H, "SEC.03", "STACKS", "28 ITEMS", "TOOLKIT")}
  {title}
  <text x="600" y="242" text-anchor="middle" font-family="{MONO}" font-size="13"
        letter-spacing="2.2" fill="#ff8fa3" xml:space="preserve">// linguagens · frameworks · dados · devops · design</text>
  {''.join(rows_svg)}
  {scan_bar(W, H, 8)}
  {sweep(W, H, 11)}
  {scanlines(W, H)}
  <rect x="0" y="0" width="{W}" height="2" fill="#ff0033" opacity="0.35"
        style="animation: flicker 8s steps(1) infinite;"/>
'''
    return svg_doc(
        W,
        H,
        "Stacks e tecnologias",
        "Banner animado com 28 tecnologias: CSS, HTML, JavaScript, TypeScript, Java, Python, Haskell, Markdown, PowerShell, Vue, Node, Vite, NPM, SQL Server, MySQL, SQLite, Git, GitHub, GitLab, GitHub Actions, Docker, Netlify, Windows Terminal, Canva, Figma, Notion, Prettier e SonarQube.",
        body,
    )


# ---------------------------------------------------------------------------
# 5. STATS
# ---------------------------------------------------------------------------
FALLBACK = {
    "stars": "0",
    "commits": "145",
    "prs": "6",
    "issues": "6",
    "contributed": "1",
    "total_contributions": "168",
    "current_streak": "2",
    "longest_streak": "4",
    "langs": [
        ("HTML", 51.29),
        ("CSS", 16.38),
        ("JavaScript", 15.58),
        ("Vue", 10.82),
        ("Python", 3.43),
        ("TypeScript", 1.49),
        ("TSQL", 1.00),
        ("Haskell", 0.00),
    ],
    "synced": "05.11.2026",
}

STATS_URL = (
    "https://github-readme-stats.shion.dev/api?username=Izzieee&theme=dark"
    "&title_color=FF2D55&text_color=FFB3C0&icon_color=FF2D55&bg_color=0D0004"
    "&border_color=8B0016&hide_border=false&include_all_commits=true"
    "&count_private=false&rank_icon=github"
)
STREAK_URL = (
    "https://streak-stats.demolab.com/?user=Izzieee&theme=dark&background=0D0004"
    "&border=8B0016&stroke=FF2D55&ring=FF2D55&fire=FF2D55&currStreakNum=FFFFFF"
    "&currStreakLabel=FF2D55&sideNums=FFB3C0&sideLabels=FF2D55&dates=8B0016"
    "&hide_border=false"
)
LANGS_URL = (
    "https://github-readme-stats.shion.dev/api/top-langs/?username=Izzieee"
    "&theme=dark&title_color=FF2D55&text_color=FFB3C0&bg_color=0D0004"
    "&border_color=8B0016&include_all_commits=true&count_private=false"
    "&layout=compact&langs_count=8"
)


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read().decode("utf-8", "replace")


def svg_texts(svg: str) -> list[str]:
    chunks = re.findall(r"<text[^>]*>(.*?)</text>", svg, re.S)
    return [re.sub(r"<[^>]+>", "", html.unescape(c)).strip() for c in chunks]


def after(texts: list[str], label: str) -> str:
    for i, text in enumerate(texts):
        if label in text and i + 1 < len(texts):
            return texts[i + 1]
    return "0"


def get_stats() -> dict:
    prev = {}
    stats_file = SCRIPTS / "stats.json"
    if stats_file.exists():
        try:
            prev = json.loads(stats_file.read_text(encoding="utf-8"))
        except Exception:
            prev = {}
    data = dict(FALLBACK)
    try:
        st = svg_texts(fetch(STATS_URL))
        sk = svg_texts(fetch(STREAK_URL))
        lg = svg_texts(fetch(LANGS_URL))
        nums = [t for t in sk if re.fullmatch(r"[\d,]+", t)]
        langs = []
        for t in lg:
            m = re.match(r"(.+?)\s+([\d.]+)%$", t)
            if m:
                langs.append((m.group(1).strip(), float(m.group(2))))
        data.update(
            {
                "stars": after(st, "Total Stars Earned:"),
                "commits": after(st, "Total Commits:"),
                "prs": after(st, "Total PRs:"),
                "issues": after(st, "Total Issues:"),
                "contributed": after(st, "Contributed to (last year):"),
                "total_contributions": nums[0] if len(nums) > 0 else "0",
                "current_streak": nums[1] if len(nums) > 1 else "0",
                "longest_streak": nums[2] if len(nums) > 2 else "0",
                "langs": langs or FALLBACK["langs"],
                "synced": dt.date.today().strftime("%d.%m.%Y"),
            }
        )
        stats_file.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("  stats atualizados via rede")
    except Exception as exc:
        if prev:
            data.update(prev)
        print(f"  stats: usando fallback ({exc})")
    return data


LANG_ICON = {
    "HTML": "html5",
    "CSS": "css",
    "JavaScript": "javascript",
    "Vue": "vue",
    "Python": "python",
    "TypeScript": "typescript",
    "TSQL": "sqlserver",
    "Haskell": "haskell",
}


def banner_stats(data: dict) -> str:
    W, H = 1200, 660
    title = ascii_group("GITHUB STATS", W, 22, 25, 55)

    tiles = [
        ("STARS", data["stars"]),
        ("COMMITS", data["commits"]),
        ("PULL REQUESTS", data["prs"]),
        ("ISSUES", data["issues"]),
    ]
    tile_svg = []
    for i, (label, value) in enumerate(tiles):
        x = 70 + (i % 2) * 245
        y = 278 + (i // 2) * 135
        tile_svg.append(
            f'<rect x="{x}" y="{y}" width="225" height="120" rx="9" fill="url(#tile)" stroke="#6b0012" stroke-width="1.2"/>'
            f'<text x="{x + 112.5}" y="{y + 62}" text-anchor="middle" font-family="{MONO}" font-size="42" '
            f'font-weight="700" fill="url(#titleGrad)" style="animation: flicker 9s steps(1) infinite;">{esc(value)}</text>'
            f'<text x="{x + 112.5}" y="{y + 92}" text-anchor="middle" font-family="{MONO}" font-size="11" '
            f'letter-spacing="1.5" fill="#ff8fa3">{esc(label)}</text>'
        )

    langs = data["langs"][:8]
    rows_svg = []
    for i, (name, pct) in enumerate(langs):
        y = 288 + i * 31
        icon = LANG_ICON.get(name, "git")
        width = max(1.5, pct / 100 * 250)
        rows_svg.append(
            f'{icon_at(icon, 626, y - 13, 20, "#ffb3c0")}'
            f'<text x="660" y="{y + 2}" font-family="{MONO}" font-size="14" fill="#ffb3c0">{esc(name)}</text>'
            f'<rect x="790" y="{y - 6}" width="250" height="8" rx="4" fill="#150007" stroke="#3d000a" stroke-width=".8"/>'
            f'<rect x="790" y="{y - 6}" width="0" height="8" rx="4" fill="url(#barGrad)">'
            f'<animate attributeName="width" from="0" to="{width:.1f}" begin="{1.3 + i * 0.08:.2f}s" dur="0.9s" fill="freeze"/>'
            f"</rect>"
            f'<text x="1125" y="{y + 2}" text-anchor="end" font-family="{MONO}" font-size="12.5" '
            f'fill="#ff8fa3">{pct:.2f}%</text>'
        )

    body = f'''
  {defs(H)}
  {backdrop(W, H, 97, 0.07, 0.19)}
  {corners(W, H, "SEC.04", "GITHUB STATS", "SYNC " + data["synced"], "PUBLIC DATA")}
  {title}
  <text x="600" y="190" text-anchor="middle" font-family="{MONO}" font-size="13"
        letter-spacing="2.2" fill="#ff8fa3" xml:space="preserve">// snapshot dos dados públicos do @Izzieee</text>

  <g>
    <rect x="50" y="225" width="520" height="330" rx="10" fill="#0a0003" opacity=".9" stroke="#8b0016" stroke-width="1.3"/>
    <text x="70" y="256" font-family="{MONO}" font-size="13" letter-spacing="1.5" fill="#ff2d55"
          xml:space="preserve">▸ RESUMO</text>
    {''.join(tile_svg)}
  </g>

  <g>
    <rect x="610" y="225" width="540" height="330" rx="10" fill="#0a0003" opacity=".9" stroke="#8b0016" stroke-width="1.3"/>
    <text x="630" y="256" font-family="{MONO}" font-size="13" letter-spacing="1.5" fill="#ff2d55"
          xml:space="preserve">▸ TOP LINGUAGENS</text>
    {''.join(rows_svg)}
  </g>

  <rect x="50" y="575" width="1100" height="42" rx="7" fill="#12000a" stroke="#6b0012" stroke-width="1"/>
  <text x="600" y="601" text-anchor="middle" font-family="{MONO}" font-size="12.5" fill="#ffb3c0"
        xml:space="preserve">CONTRIBUIÇÕES <tspan fill="#ff2d55" font-weight="700">{esc(data["total_contributions"])}</tspan>
    · STREAK ATUAL <tspan fill="#ff2d55" font-weight="700">{esc(data["current_streak"])}</tspan>
    · MAIOR STREAK <tspan fill="#ff2d55" font-weight="700">{esc(data["longest_streak"])}</tspan>
    · CONTRIBUIU <tspan fill="#ff2d55" font-weight="700">{esc(data["contributed"])}</tspan> REPO</text>
  <text x="600" y="637" text-anchor="middle" font-family="{MONO}" font-size="10" fill="#8b0016"
        xml:space="preserve">// sync {esc(data["synced"])} · github-readme-stats / streak-stats</text>

  {sweep(W, H, 10)}
  {scanlines(W, H)}
  <rect x="0" y="0" width="{W}" height="2" fill="#ff0033" opacity="0.35"
        style="animation: flicker 6s steps(1) infinite;"/>
'''
    return svg_doc(
        W,
        H,
        "GitHub Stats de @Izzieee",
        "Banner animado com estrelas, commits, pull requests, issues, contribuicoes, streaks e linguagens mais usadas.",
        body,
    )


# ---------------------------------------------------------------------------
# 6. FOOTER
# ---------------------------------------------------------------------------
def banner_footer() -> str:
    W, H = 1200, 320
    title = ascii_group("OBRIGADO", W, 24, 25, 55)
    mask = typing_mask("byeType", 300, 207, 600, 1.2, 0.8)
    body = f'''
  {defs(H, mask)}
  {backdrop(W, H, 113, 0.07, 0.20)}
  {corners(W, H, "EOF", "@IZZIEE", "FIM", "OBRIGADA")}
  {title}

  <g mask="url(#byeType)" font-family="{MONO}" font-size="20" fill="#ffb3c0" text-anchor="middle">
    <text x="600" y="225" xml:space="preserve">obrigada pela visita_</text>
  </g>
  <rect x="738" y="210" width="10" height="19" fill="#ff2d55" opacity="0">
    <animate attributeName="opacity" values="0;1;0;1;0" dur="1.1s" begin="2.2s" repeatCount="indefinite"/>
  </rect>

  <text x="600" y="272" text-anchor="middle" font-family="{MONO}" font-size="14"
        letter-spacing="4" fill="#ff8fa3" xml:space="preserve">@Izzieee</text>
  {sweep(W, H, 7)}
  {scanlines(W, H)}
'''
    return svg_doc(
        W,
        H,
        "Obrigado pela visita",
        "Banner ASCII animado de despedida com o usuario @Izzieee.",
        body,
    )


# ---------------------------------------------------------------------------
def main() -> None:
    print("Gerando banners...")
    data = get_stats()
    write("banner.svg", banner_hero())
    write("banner-sobre.svg", banner_sobre())
    write("banner-contato.svg", banner_contato())
    write("contato-instagram.svg", contact_card("instagram", "INSTAGRAM", "@jacy_martins_", "", "01"))
    write("contato-discord.svg", contact_card("discord", "DISCORD", "discord.gg", "", "02"))
    write("contato-gmail.svg", contact_card("gmail", "GMAIL", "jacyanemartins011", "@gmail.com", "03"))
    write("contato-linkedin.svg", contact_card("linkedin", "LINKEDIN", "in/jacyane-martins", "", "04"))
    write("banner-stacks.svg", banner_stacks())
    write("banner-stats.svg", banner_stats(data))
    write("banner-footer.svg", banner_footer())
    print("Pronto.")


if __name__ == "__main__":
    main()

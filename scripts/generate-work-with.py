#!/usr/bin/env python3
import json
import os
import xml.sax.saxutils

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(REPO, "work-with.json")
OUT_PATH = os.path.join(REPO, "assets", "work-with.svg")

WIDTH = 848
PAD = 20
GAP = 16
CARD_PAD = 18
TITLE_FONT = 20
TITLE_H = 26
PILL_FONT = 13
PILL_H = 26
PILL_GAP = 8
CHAR_W = 7.0
CARD_BG = "#161b22"
CARD_BORDER = "#30363d"
PILL_BG = "#0d1117"
LIGHT_CARD_BG = "#ffffff"
LIGHT_CARD_BORDER = "#d0d7de"
LIGHT_PILL_BG = "#f6f8fa"
LIGHT_FACTOR = 0.62
FONT = "Arial, Helvetica, sans-serif"


def esc(text):
    return xml.sax.saxutils.escape(text)


def pill_width(item):
    return int(len(item) * CHAR_W) + 22


def darken(hex_color, factor):
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i : i + 2], 16) / 255 for i in (0, 2, 4))
    mx, mn = max(r, g, b), min(r, g, b)
    l = (mx + mn) / 2
    if mx == mn:
        h = s = 0.0
    else:
        d = mx - mn
        s = d / (2 - mx - mn) if l > 0.5 else d / (mx + mn)
        if mx == r:
            h = (g - b) / d + (6 if g < b else 0)
        elif mx == g:
            h = (b - r) / d + 2
        else:
            h = (r - g) / d + 4
        h /= 6
    l = min(1.0, max(0.0, l * factor))

    def hue_to_rgb(p, q, t):
        if t < 0:
            t += 1
        if t > 1:
            t -= 1
        if t < 1 / 6:
            return p + (q - p) * 6 * t
        if t < 1 / 2:
            return q
        if t < 2 / 3:
            return p + (q - p) * (2 / 3 - t) * 6
        return p

    if s == 0:
        r = g = b = l
    else:
        q = l * (1 + s) if l < 0.5 else l + s - l * s
        p = 2 * l - q
        r = hue_to_rgb(p, q, h + 1 / 3)
        g = hue_to_rgb(p, q, h)
        b = hue_to_rgb(p, q, h - 1 / 3)
    return "#{:02x}{:02x}{:02x}".format(*(int(round(c * 255)) for c in (r, g, b)))


def wrap(items, max_width):
    rows = []
    row = []
    row_w = 0
    for item in items:
        w = pill_width(item)
        if row and row_w + PILL_GAP + w > max_width:
            rows.append(row)
            row = [item]
            row_w = w
        else:
            row.append(item)
            row_w += w + (PILL_GAP if row_w else 0)
    if row:
        rows.append(row)
    return rows


def card_height(rows):
    content = TITLE_H + 10 + len(rows) * PILL_H + (len(rows) - 1) * PILL_GAP
    return content + 2 * CARD_PAD


def pill_tag(x, y, w, label):
    return (
        '<g>'
        f'<rect class="pill-bg" x="{x}" y="{y}" width="{w}" height="{PILL_H}" rx="13"/>'
        f'<text class="pill-label" x="{x + w // 2}" y="{y + 17}" font-size="{PILL_FONT}" '
        f'text-anchor="middle">{esc(label)}</text>'
        '</g>'
    )


def card_tag(x, y, w, height, index, category):
    rows = wrap(category["items"], w - 2 * CARD_PAD)
    parts = [
        f'<g class="card c{index}">',
        f'<rect class="card-bg" x="{x}" y="{y}" width="{w}" height="{height}" rx="12"/>',
        f'<rect class="bar" x="{x + CARD_PAD}" y="{y + CARD_PAD + 4}" width="4" height="18" rx="2"/>',
        f'<text class="title" x="{x + CARD_PAD + 14}" y="{y + CARD_PAD + 21}" font-size="{TITLE_FONT}" '
        f'font-weight="bold">{esc(category["title"])}</text>',
    ]
    pill_y = y + CARD_PAD + TITLE_H + 10
    pill_x = x + CARD_PAD
    for row in rows:
        for item in row:
            w_item = pill_width(item)
            parts.append(pill_tag(pill_x, pill_y, w_item, item))
            pill_x += w_item + PILL_GAP
        pill_x = x + CARD_PAD
        pill_y += PILL_H + PILL_GAP
    parts.append("</g>")
    return "".join(parts)


def style_block(categories):
    dark = [f'.c{i}{{--accent:{c["accent"]};--text:{c["text"]}}}' for i, c in enumerate(categories)]
    light = [
        f'.c{i}{{--accent:{darken(c["accent"], LIGHT_FACTOR)};'
        f'--text:{darken(c["accent"], LIGHT_FACTOR)}}}'
        for i, c in enumerate(categories)
    ]
    return (
        f'<style>'
        f'text{{font-family:{FONT}}}'
        f'.card{{--card-bg:{CARD_BG};--card-border:{CARD_BORDER};--pill-bg:{PILL_BG}}}'
        f'.card-bg{{fill:var(--card-bg);stroke:var(--card-border);stroke-width:1}}'
        f'.bar{{fill:var(--accent)}}'
        f'.title{{fill:var(--accent)}}'
        f'.pill-bg{{fill:var(--pill-bg);stroke:var(--accent);stroke-opacity:0.35;stroke-width:1}}'
        f'.pill-label{{fill:var(--text)}}'
        + "".join(dark)
        + '@media (prefers-color-scheme: light){'
        f'.card{{--card-bg:{LIGHT_CARD_BG};--card-border:{LIGHT_CARD_BORDER};--pill-bg:{LIGHT_PILL_BG}}}'
        + "".join(light)
        + '}'
        + '</style>'
    )


def main():
    with open(DATA_PATH, encoding="utf-8") as fh:
        data = json.load(fh)
    categories = data.get("categories") or []
    if len(categories) != 4:
        raise SystemExit(
            "work-with.json must contain exactly 4 categories to fill the 2x2 grid"
        )
    for category in categories:
        for key in ("title", "accent", "text", "items"):
            if key not in category or not category[key]:
                raise SystemExit(
                    f'category {category.get("title", "?")!r} is missing field {key!r}'
                )

    cw = (WIDTH - 2 * PAD - GAP) // 2
    wrapped = [wrap(cat["items"], cw - 2 * CARD_PAD) for cat in categories]
    uniform = max(card_height(rows) for rows in wrapped)
    total_height = 2 * PAD + uniform + GAP + uniform

    cards = []
    y = PAD
    for row in range(2):
        x = PAD
        for col in range(2):
            idx = row * 2 + col
            cards.append(card_tag(x, y, cw, uniform, idx, categories[idx]))
            x += cw + GAP
        y += uniform + GAP

    svg = (
        f'<svg viewBox="0 0 {WIDTH} {total_height}" width="{WIDTH}" height="{total_height}" '
        f'xmlns="http://www.w3.org/2000/svg">'
        + style_block(categories)
        + "".join(cards)
        + "</svg>"
    )

    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        fh.write(svg)
    print(f"wrote {OUT_PATH} ({WIDTH}x{total_height})")


if __name__ == "__main__":
    main()

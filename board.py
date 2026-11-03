"""HTML and SVG rendering for investigation boards."""

from collections import defaultdict
from math import ceil, sqrt

from constants import FILES, GLYPHS
from game import coords, square


def board_html(positions, murder, start=None, end=None, caption="", compact=False):
    size = 47 if compact else 62
    left, top = 28, 12
    w, h = left + size*8 + 10, top + size*8 + 34
    arrows = ""
    if start and end:
        x1, y1 = coords(start)
        x2, y2 = coords(end)
        ax, ay = left + (x1+.5)*size, top + (7-y1+.5)*size
        bx, by = left + (x2+.5)*size, top + (7-y2+.5)*size
        arrows = f'<line x1="{ax}" y1="{ay}" x2="{bx}" y2="{by}" stroke="#ffb74d" stroke-width="5" marker-end="url(#arrow)" opacity=".95" />'
    cells = []
    for y in range(7, -1, -1):
        for x in range(8):
            s = square(x, y)
            px, py = left + x*size, top + (7-y)*size
            fill = "#e9dfc8" if (x+y)%2 else "#66806c"
            cells.append(f'<rect x="{px}" y="{py}" width="{size}" height="{size}" fill="{fill}"/>')
            if s == murder:
                cells.append(f'<rect x="{px+3}" y="{py+3}" width="{size-6}" height="{size-6}" fill="#a7333b" opacity=".78" rx="5"/>')
                cells.append(f'<text x="{px+size/2}" y="{py+size*.67}" text-anchor="middle" font-size="{size*.5}" fill="white">✕</text>')
            if s == start:
                cells.append(f'<rect x="{px+3}" y="{py+3}" width="{size-6}" height="{size-6}" fill="none" stroke="#fbbf24" stroke-width="4" rx="4"/>')
            if s == end:
                cells.append(f'<rect x="{px+3}" y="{py+3}" width="{size-6}" height="{size-6}" fill="none" stroke="#40d6d0" stroke-width="4" rx="4"/>')
    for i in range(8):
        cells.append(f'<text x="{left+(i+.5)*size}" y="{top+8*size+19}" text-anchor="middle" fill="#e5e7eb" font-size="13">{FILES[i]}</text>')
        cells.append(f'<text x="14" y="{top+(i+.62)*size}" text-anchor="middle" fill="#e5e7eb" font-size="13">{8-i}</text>')
    grouped = defaultdict(list)
    for name, pos in positions.items():
        grouped[pos].append(name)
    for pos, names in grouped.items():
        x, y = coords(pos)
        columns = ceil(sqrt(len(names)))
        rows = ceil(len(names) / columns)
        cell_size = size / max(columns, rows)
        for index, name in enumerate(names):
            row, column = divmod(index, columns)
            row_count = min(columns, len(names) - row * columns)
            px = left + (x + .5)*size + (column - (row_count - 1)/2)*cell_size
            py = top + (7-y+.5)*size + (row - (rows - 1)/2)*cell_size
            is_white = name.startswith("White")
            fg = "#fffdf2" if is_white else "#171923"
            stroke = "#242424" if is_white else "#f4f1e9"
            cells.append(f'<text x="{px}" y="{py+cell_size*.31}" text-anchor="middle" font-size="{cell_size*.76}" font-family="DejaVu Sans,Arial Unicode MS,serif" fill="{fg}" stroke="{stroke}" stroke-width=".9" paint-order="stroke"><title>{name}</title>{GLYPHS[name]}</text>')
    svg = f'''<svg viewBox="0 0 {w} {h}" style="width:100%;max-width:{w}px;height:auto;display:block;margin:auto" xmlns="http://www.w3.org/2000/svg"><defs><marker id="arrow" markerWidth="5" markerHeight="5" refX="3" refY="2.5" orient="auto"><path d="M0,0 L5,2.5 L0,5 Z" fill="#ffb74d"/></marker></defs>{''.join(cells)}{arrows}</svg>'''
    return f'<div style="background:#1b2430;border-radius:12px;padding:10px;text-align:center"><div style="color:#f3f4f6;font-family:sans-serif;font-weight:600;margin:6px">{caption}</div>{svg}</div>'

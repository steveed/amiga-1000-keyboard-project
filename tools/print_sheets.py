"""Lay the board's 1:1 SVG out on printable pages.

Usage: print_sheets.py <board.svg> <out_dir>

Writes a single 11x17 (tabloid) sheet with the whole board, and a two-page
US Letter set with an overlap, crosshairs and a cut line for taping together.
Every page carries a 100 mm and a 1 in scale bar to check the print scale.
"""
import os
import re
import sys

import cairosvg
from pypdf import PdfWriter

SRC, OUT = sys.argv[1], sys.argv[2]

svg = open(SRC).read()
W = float(re.search(r'width="([\d.]+)mm"', svg).group(1))
H = float(re.search(r'height="([\d.]+)mm"', svg).group(1))
inner = svg[svg.index('>', svg.index('<svg')) + 1:svg.rindex('</svg>')]

FONT = 'font-family="Helvetica, Arial, sans-serif"'


def board(x, y, x0=0.0, x1=None):
    """The board, or the slice x0..x1 of it, with its top-left at page (x, y)."""
    x1 = W if x1 is None else x1
    return ('<svg x="%.3f" y="%.3f" width="%.3f" height="%.3f" viewBox="%.3f 0 %.3f %.3f">%s</svg>'
            % (x, y, x1 - x0, H, x0, x1 - x0, H, inner))


def text(x, y, s, size=3.5, anchor='start'):
    return '<text x="%.2f" y="%.2f" font-size="%.2f" %s text-anchor="%s">%s</text>' % (x, y, size, FONT, anchor, s)


def scale_bars(x, y):
    """A 100 mm bar with 10 mm ticks and a 1 in bar under it."""
    p = ['<g stroke="black" stroke-width="0.3" fill="none">',
         '<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f"/>' % (x, y, x + 100, y)]
    for i in range(11):
        h = 4 if i % 5 == 0 else 2.5
        p.append('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f"/>' % (x + 10 * i, y, x + 10 * i, y - h))
    p.append('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f"/>' % (x, y + 8, x + 25.4, y + 8))
    for i in (0, 1):
        p.append('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f"/>' % (x + 25.4 * i, y + 8, x + 25.4 * i, y + 4))
    p.append('</g>')
    p.append(text(x + 103, y + 1, '100 mm'))
    p.append(text(x + 28.4, y + 9, '1 in'))
    return ''.join(p)


def crosshair(x, y, r=4):
    return ('<g stroke="black" stroke-width="0.25" fill="none"><circle cx="%.2f" cy="%.2f" r="%.2f"/>'
            '<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f"/><line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f"/></g>'
            % (x, y, r / 2, x - r, y, x + r, y, x, y - r, x, y + r))


def page(w, h, body):
    return ('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            'width="%.2fmm" height="%.2fmm" viewBox="0 0 %.2f %.2f">'
            '<rect width="100%%" height="100%%" fill="white"/>%s</svg>' % (w, h, w, h, body))


def write_pdf(pages, name):
    out = PdfWriter()
    for i, p in enumerate(pages):
        tmp = os.path.join(OUT, '.page%d.pdf' % i)
        cairosvg.svg2pdf(bytestring=p.encode(), write_to=tmp)
        out.append(tmp)
        os.remove(tmp)
    path = os.path.join(OUT, name)
    with open(path, 'wb') as fh:
        out.write(fh)
    print('wrote', path)


TITLE = 'Amiga 1000 keyboard PCB, 1:1 (%.1f x %.1f mm). Print at 100%% / Actual size; check the 100 mm bar.' % (W, H)

# 11x17 landscape: the whole board on one sheet.
TW, TH = 431.8, 279.4
bx, by = (TW - W) / 2, 35
write_pdf([page(TW, TH, text(bx, 22, TITLE, 4.5) + board(bx, by) + scale_bars(bx, by + H + 25))],
          'amiga-1000-keyboard-print-tabloid.pdf')

# US Letter landscape: two tiles that overlap by OVL mm.
LW, LH = 279.4, 215.9
OVL = 21.0
SPLIT = W / 2
a0, a1 = 0.0, SPLIT + OVL / 2
b0, b1 = SPLIT - OVL / 2, W
marks = [(SPLIT - 5, yy) for yy in (12, H / 2, H - 12)] + [(SPLIT + 5, yy) for yy in (12, H / 2, H - 12)]
my = 35


def tile(x0, x1, ox, label, cut):
    body = [text(12, 18, TITLE, 3.6), text(12, 25, label, 4.5), board(ox, my, x0, x1)]
    body += [crosshair(ox + mx - x0, my + myy) for mx, myy in marks]
    if cut:
        cx = ox + SPLIT - x0
        body.append('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="black" stroke-width="0.3" '
                    'stroke-dasharray="3,2"/>' % (cx, my - 6, cx, my + H + 6))
        body.append(text(cx, my - 8, 'cut here, then overlay on sheet 2 lining up the crosshairs', 3.2, 'middle'))
    body.append(scale_bars(12, my + H + 13))
    return page(LW, LH, ''.join(body))


write_pdf([tile(a0, a1, 12, 'Sheet 1 of 2 (left)', True),
           tile(b0, b1, LW - 12 - (b1 - b0), 'Sheet 2 of 2 (right)', False)],
          'amiga-1000-keyboard-print-letter.pdf')

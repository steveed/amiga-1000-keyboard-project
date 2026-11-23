"""A manufacturing inquiry drawing for the A1000 Return keycap, as a PDF.

Usage: keycap_spec.py <a1000_keycaps.scad> <return-keycap.stl> <top.png> <under.png> <out.pdf>

The plan view and the figures come from the parameters in a1000_keycaps.scad, so they follow the
model; the two sections are cut from the rendered STL, so they show the part as printed.  Three US
Letter landscape sheets: an overview with the requirements, the plan with stem positions, and the
sections with the profile.
"""
import base64
import io
import math
import re
import struct
import sys

import cairosvg
from pypdf import PdfReader, PdfWriter

SCAD, STL, TOP_PNG, UNDER_PNG, OUT = sys.argv[1:6]

src = open(SCAD).read()


def param(name):
    m = re.search(r'^\s*%s\s*=\s*([^;]+);' % name, src, re.M)
    v = m.group(1).strip()
    if v.startswith('['):
        return [float(t) for t in v.strip('[]').split(',')]
    return float(v)


P = {n: param(n) for n in ('U', 'grid_left_top', 'grid_left_bottom', 'grid_right', 'grid_back', 'grid_mid',
                           'grid_front', 'stab', 'top_in_x', 'top_in_y', 'top_skew', 'dish_depth', 'gap',
                           'wall', 'top_t', 'stem_d', 'cross_l', 'cross_w', 'cross_depth', 'stem_drop')}
P['dummy'] = param('dummy')
cherry = re.search(r'^\s*cherry\s*=\s*\[(.*)\];', src, re.M).group(1)
cherry = [[float(a), float(b)] for a, b in re.findall(r'\[([\d.]+),\s*([\d.]+)\]', cherry)]
return_row = int(param('return_row'))
height, tilt = cherry[return_row - 1][0], cherry[return_row - 1][1] / 2

g = P['gap']
xl_top, xl_bot, xr = P['grid_left_top'] + g, P['grid_left_bottom'] + g, P['grid_right'] - g
yf, yb, ym = P['grid_front'] + g, P['grid_back'] - g, P['grid_mid'] - g
y_mid = (P['grid_front'] + P['grid_back']) / 2

# Skirt and top outlines, anticlockwise from the front left
skirt = [(xl_bot, yf), (xr, yf), (xr, yb), (xl_top, yb), (xl_top, ym), (xl_bot, ym)]
tx, ty, sk = P['top_in_x'], P['top_in_y'], P['top_skew']
top = [(xl_bot + tx, yf + ty + sk), (xr - tx, yf + ty + sk), (xr - tx, yb - ty + sk), (xl_top + tx, yb - ty + sk),
       (xl_top + tx, ym - ty + sk), (xl_bot + tx, ym - ty + sk)]
grid = [(P['grid_left_bottom'], P['grid_front']), (P['grid_right'], P['grid_front']),
        (P['grid_right'], P['grid_back']), (P['grid_left_top'], P['grid_back']),
        (P['grid_left_top'], P['grid_mid']), (P['grid_left_bottom'], P['grid_mid'])]
stems = [('S1', 'Switch (MX)', 0.0, 0.0), ('S2', 'Stabiliser, back', 0.0, P['stab']),
         ('S3', 'Stabiliser, front', 0.0, -P['stab']), ('S4', 'Dummy switch (MX, no spring)', *P['dummy'])]


def top_z(y):
    """Height of the top plane (before the dish) at y, from the skirt bottom."""
    return height - (y - y_mid) * math.sin(math.radians(tilt))


z_front, z_back = top_z(top[0][1]), top_z(top[2][1])
dish_x0, dish_x1 = xl_bot + tx, xr - tx
dish_w = dish_x1 - dish_x0
dish_r = (dish_w ** 2 / 4 + P['dish_depth'] ** 2) / (2 * P['dish_depth'])

# ---------------------------------------------------------------- STL

data = open(STL, 'rb').read()
n = struct.unpack('<I', data[80:84])[0]
tris = [struct.unpack('<12f', data[84 + 50 * i:84 + 50 * i + 48])[3:] for i in range(n)]
tris = [((t[0], t[1], t[2]), (t[3], t[4], t[5]), (t[6], t[7], t[8])) for t in tris]
bbox = [(min(v[a] for t in tris for v in t), max(v[a] for t in tris for v in t)) for a in range(3)]


def section(axis, c):
    """Closed loops where the plane coord[axis] = c cuts the mesh, as (u, z) points, u the other
    horizontal coordinate."""
    u = 1 - axis
    segs = []
    for t in tris:
        pts = []
        for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            da, db = a[axis] - c, b[axis] - c
            if (da < 0) != (db < 0):
                f = da / (da - db)
                pts.append((a[u] + f * (b[u] - a[u]), a[2] + f * (b[2] - a[2])))
        if len(pts) == 2:
            segs.append(pts)
    key = lambda p: (round(p[0], 4), round(p[1], 4))
    ends = {}
    for i, (a, b) in enumerate(segs):
        ends.setdefault(key(a), []).append(i)
        ends.setdefault(key(b), []).append(i)
    used, loops = set(), []
    for i in range(len(segs)):
        if i in used:
            continue
        used.add(i)
        loop = list(segs[i])
        while True:
            nxt = [j for j in ends[key(loop[-1])] if j not in used]
            if not nxt:
                break
            j = nxt[0]
            used.add(j)
            a, b = segs[j]
            loop.append(b if key(a) == key(loop[-1]) else a)
        loops.append(loop)
    return loops


# ---------------------------------------------------------------- drawing primitives

PW, PH = 279.4, 215.9
FONT = 'font-family="Helvetica, Arial, sans-serif"'
INK, FAINT, ACCENT = '#111', '#777', '#1f5fa8'


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def text(x, y, s, size=3.0, anchor='start', weight='normal', fill=INK, rot=0):
    r = ' transform="rotate(%.1f %.2f %.2f)"' % (rot, x, y) if rot else ''
    return ('<text x="%.2f" y="%.2f" font-size="%.2f" %s font-weight="%s" fill="%s" text-anchor="%s"%s>%s</text>'
            % (x, y, size, FONT, weight, fill, anchor, r, esc(s)))


def wrap(x, y, s, width, size=3.0, lead=1.4, **kw):
    """Text wrapped to `width` mm; returns (svg, y below the last line)."""
    per = int(width / (size * 0.5))
    out, line = [], ''
    for w in s.split():
        if line and len(line) + 1 + len(w) > per:
            out.append(line)
            line = w
        else:
            line = (line + ' ' + w).strip()
    out.append(line)
    svg = ''.join(text(x, y + i * size * lead, l, size, **kw) for i, l in enumerate(out))
    return svg, y + len(out) * size * lead


def line(x1, y1, x2, y2, w=0.25, color=INK, dash=None):
    d = ' stroke-dasharray="%s"' % dash if dash else ''
    return ('<line x1="%.3f" y1="%.3f" x2="%.3f" y2="%.3f" stroke="%s" stroke-width="%.2f"%s/>'
            % (x1, y1, x2, y2, color, w, d))


def poly(pts, w=0.35, color=INK, fill='none', dash=None, closed=True):
    d = ' stroke-dasharray="%s"' % dash if dash else ''
    tag = 'polygon' if closed else 'polyline'
    return ('<%s points="%s" stroke="%s" stroke-width="%.2f" fill="%s" stroke-linejoin="round"%s/>'
            % (tag, ' '.join('%.3f,%.3f' % p for p in pts), color, w, fill, d))


def arrow(x, y, dx, dy, size=1.6):
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    return poly([(x, y), (x - size * ux + 0.45 * size * uy, y - size * uy - 0.45 * size * ux),
                 (x - size * ux - 0.45 * size * uy, y - size * uy + 0.45 * size * ux)], w=0.01, fill=ACCENT,
                color=ACCENT)


def image(path, x, y, w, h):
    b = base64.b64encode(open(path, 'rb').read()).decode()
    return ('<image x="%.2f" y="%.2f" width="%.2f" height="%.2f" preserveAspectRatio="xMidYMid meet" '
            'xlink:href="data:image/png;base64,%s"/>' % (x, y, w, h, b))


class View:
    """Model (u, v) to page mm: u to the right, v up, at scale s, model origin at page (ox, oy)."""

    def __init__(self, ox, oy, s):
        self.ox, self.oy, self.s = ox, oy, s

    def p(self, u, v):
        return (self.ox + self.s * u, self.oy - self.s * v)

    def poly(self, pts, **kw):
        return poly([self.p(*q) for q in pts], **kw)

    def line(self, a, b, **kw):
        return line(*self.p(*a), *self.p(*b), **kw)

    def circle(self, u, v, d, w=0.25, color=INK, dash=None, fill='none'):
        x, y = self.p(u, v)
        dd = ' stroke-dasharray="%s"' % dash if dash else ''
        return ('<circle cx="%.3f" cy="%.3f" r="%.3f" stroke="%s" stroke-width="%.2f" fill="%s"%s/>'
                % (x, y, d / 2 * self.s, color, w, fill, dd))

    def centre(self, u, v, r=3.5):
        x, y = self.p(u, v)
        return (line(x - r, y, x + r, y, 0.15, FAINT, '2,0.6,0.4,0.6')
                + line(x, y - r, x, y + r, 0.15, FAINT, '2,0.6,0.4,0.6'))

    def dim(self, a, b, at, horiz, label=None, size=2.8):
        """A dimension between model points a and b, its line at model v (horiz) or u = `at`."""
        out = []
        if horiz:
            x1, ya = self.p(*a)
            x2, yb = self.p(*b)
            _, yd = self.p(0, at)
            for x, y in ((x1, ya), (x2, yb)):
                s = 1 if yd > y else -1
                out.append(line(x, y + s * 0.8, x, yd + s * 1.2, 0.15, ACCENT))
            out.append(line(x1, yd, x2, yd, 0.18, ACCENT))
            out += [arrow(x1, yd, x1 - x2, 0), arrow(x2, yd, x2 - x1, 0)]
            val = label or '%.2f' % abs(b[0] - a[0])
            out.append(text((x1 + x2) / 2, yd - 0.9, val, size, 'middle', fill=ACCENT))
        else:
            xa, y1 = self.p(*a)
            xb, y2 = self.p(*b)
            xd, _ = self.p(at, 0)
            for x, y in ((xa, y1), (xb, y2)):
                s = 1 if xd > x else -1
                out.append(line(x + s * 0.8, y, xd + s * 1.2, y, 0.15, ACCENT))
            out.append(line(xd, y1, xd, y2, 0.18, ACCENT))
            out += [arrow(xd, y1, 0, y1 - y2), arrow(xd, y2, 0, y2 - y1)]
            val = label or '%.2f' % abs(b[1] - a[1])
            out.append(text(xd - 0.9, (y1 + y2) / 2, val, size, 'middle', fill=ACCENT, rot=-90))
        return ''.join(out)


def title_block(sheet, title, scale):
    x0, y0, w, h = PW - 10 - 118, PH - 10 - 24, 118, 24
    rows = [('DRAWING', 'A1000-RET-01'), ('REV', 'A'), ('DATE', '2026-10-27'), ('UNITS', 'mm'),
            ('SCALE', scale), ('SHEET', '%d / 3' % sheet)]
    out = [poly([(x0, y0), (x0 + w, y0), (x0 + w, y0 + h), (x0, y0 + h)], w=0.4),
           line(x0, y0 + 10, x0 + w, y0 + 10, 0.25),
           text(x0 + 3, y0 + 4.6, 'AMIGA 1000 RETURN KEYCAP, CHERRY MX', 3.4, weight='bold'),
           text(x0 + 3, y0 + 8.3, title, 2.8, fill=FAINT)]
    for i, (k, v) in enumerate(rows):
        cx = x0 + (i % 3) * w / 3
        cy = y0 + 10 + (i // 3) * 7
        out.append(line(cx, y0 + 10, cx, y0 + h, 0.25) if i % 3 and i < 3 else '')
        out.append(text(cx + 2, cy + 2.8, k, 1.9, fill=FAINT))
        out.append(text(cx + 2, cy + 6.2, v, 2.9, weight='bold'))
    out.append(line(x0, y0 + 17, x0 + w, y0 + 17, 0.25))
    out.append(text(10, PH - 6, 'Datum: centre of the switch stem S1. Dimensions in mm. '
                    'Third-angle projection. Plan views look down on the top of the key.', 2.4, fill=FAINT))
    return ''.join(out)


def page(body):
    return ('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            'width="%.1fmm" height="%.1fmm" viewBox="0 0 %.1f %.1f">'
            '<rect width="100%%" height="100%%" fill="white"/>'
            '<rect x="5" y="5" width="%.1f" height="%.1f" fill="none" stroke="%s" stroke-width="0.5"/>%s</svg>'
            % (PW, PH, PW, PH, PW - 10, PH - 10, INK, body))


def heading(x, y, s):
    return text(x, y, s, 3.6, weight='bold') + line(x, y + 1.3, x + 4 + len(s) * 2.0, y + 1.3, 0.3, ACCENT)


# ---------------------------------------------------------------- sheet 1: overview

W_out, D_out = xr - xl_bot, yb - yf


def sheet1():
    b = [text(10, 17, 'Custom keycap: Amiga 1000 Return (inverted L), Cherry MX mount', 6, weight='bold'),
         text(10, 23.5, 'Request for quotation / feasibility. Prototype printed from the attached STL, '
              'fitted and tested on the board.', 3.2, fill=FAINT)]
    x, y = 10, 34
    b.append(heading(x, y, 'What it is'))
    s, y = wrap(x, y + 6.5, (
        'The Return key of a reproduction Amiga 1000 keyboard built on Cherry MX switches. It is an inverted-L '
        'key, a smaller version of the larger Amiga Return: 1.25U wide in the upper row, 2U wide in the lower '
        'row and 2U tall (the larger Amiga version is 1.5U over 2.25U, which runs into the neighbouring keys '
        'on this layout). It sits between ] and \' on the left and HELP and UP on the right.'), 128, 3.0)
    b.append(s)
    y += 4
    b.append(heading(x, y, 'Mounting (four stems, all on the cap)'))
    y += 6.5
    rows = [('S1', 'MX switch, the key\'s switch. Datum (0, 0).'),
            ('S2, S3', 'Cherry plate-mount 2U stabiliser, turned 90 degrees: stems 0, +/-%.3f '
                       '(%.3f apart) front to back.' % (P['stab'], 2 * P['stab'])),
            ('S4', 'MX housing with no spring (dummy) under the lower-left extension, '
                   'at (%.2f, %.2f). Supports the cap only.' % tuple(P['dummy'])),
            ('', 'All four are standard MX female cross stems.')]
    for k, v in rows:
        b.append(text(x, y, k, 3.0, weight='bold'))
        s, y = wrap(x + 15, y, v, 113, 3.0)
        b.append(s)
        y += 0.6
    y += 3.4
    b.append(heading(x, y, 'Profile'))
    s, y = wrap(x, y + 6.5, (
        'Your DCS profile at the home row, adjusted for this shape as you see fit. For reference, the '
        'prototype is Cherry profile (as GMK) at the home row (R3): %.2f mm from the skirt bottom to the '
        'middle of the top, the top tilted %.1f degrees front-to-back over the full 2U depth (the R3 angle '
        'of %.0f degrees spread over two rows), and a cylindrical dish %.2f mm deep running front to back '
        'across the full width of the lower row.'
        % (height, tilt, 2 * tilt, P['dish_depth'])), 128, 3.0)
    b.append(s)
    y += 4
    b.append(heading(x, y, 'Critical (please hold)'))
    y += 6.5
    for v in ('Skirt outline and the 0.45 mm clearance to the key grid (sheet 2).',
              'The four stem positions relative to S1 (sheet 2 table), +/-0.05 suggested.',
              'Height and sculpt to sit level with the home-row keys beside it.',
              'Stem fit: standard MX cross, firm on a Cherry MX switch and a Cherry stabiliser insert.'):
        b.append(text(x, y, '-', 3.0))
        s, y = wrap(x + 4, y, v, 124, 3.0)
        b.append(s)
    y += 3.4
    b.append(heading(x, y, 'Your standard (adjust freely)'))
    s, y = wrap(x, y + 6.5, (
        'Wall %.1f mm, top %.1f mm under the dish, stem bosses %.1f mm across, %.1f mm up from the skirt '
        'bottom: these suit the 3D print and may follow your tooling, as may draft, ribs, the cross '
        'tolerances (the print used %.2f x %.2f slots tuned for FDM) and edge radii.'
        % (P['wall'], P['top_t'], P['stem_d'], P['stem_drop'], P['cross_l'], P['cross_w'])), 128, 3.0)
    b.append(s)

    # Right column: renders and to-agree table
    rx = 148
    b.append(heading(rx, 34, 'Model (attached STL)'))
    b.append(image(TOP_PNG, rx, 37, 60, 45) + image(UNDER_PNG, rx + 62, 37, 60, 45))
    b.append(text(rx + 30, 84, 'Top', 2.6, 'middle', fill=FAINT) + text(rx + 92, 84, 'Underside', 2.6, 'middle',
                                                                        fill=FAINT))
    y = 95
    b.append(heading(rx, y, 'Overall'))
    y += 6.5
    for k, v in (('Footprint', '%.2f x %.2f (wide x deep), inverted L' % (W_out, D_out)),
                 ('Upper row', '%.2f wide (1.25U key grid)' % (xr - xl_top)),
                 ('Lower row', '%.2f wide (2U key grid)' % (xr - xl_bot)),
                 ('Height', '%.2f at the front edge, %.2f at the back' % (z_front, z_back)),
                 ('Mount', 'Cherry MX, 1 switch + 2U stab + 1 dummy')):
        b.append(text(rx, y, k, 3.0, weight='bold') + text(rx + 22, y, v, 3.0))
        y += 4.4
    b.append(title_block(1, 'Overview and requirements', '-'))
    return page(''.join(b))


# ---------------------------------------------------------------- sheet 2: plan

def sheet2():
    s = 3.0
    v = View(176, 100, s)
    b = [heading(10, 15, 'Plan view, from above (front of the keyboard at the bottom)')]
    b.append(v.poly(grid, w=0.2, color=FAINT, dash='0.8,0.8'))
    b.append(v.poly(skirt, w=0.5))
    b.append(v.poly(top, w=0.25, color=INK, dash='3,1.2'))
    # dish extent
    for name, _, x, y in stems:
        b.append(v.circle(x, y, P['stem_d'], w=0.25, dash='1.2,0.8'))
        b.append(v.centre(x, y, 2.6 * s))
        px, py = v.p(x, y)
        b.append(text(px + 9, py - 5.5, name, 3.0, weight='bold'))
    px, py = v.p((P['grid_left_bottom'] + P['grid_left_top']) / 2, 9.5)
    b.append(text(px, py, 'key ] here', 2.7, 'middle', fill=FAINT))
    px, py = v.p((P['grid_left_bottom'] + P['grid_left_top']) / 2, 6.5)
    b.append(text(px, py, '(\' to the left, HELP', 2.4, 'middle', fill=FAINT))
    px, py = v.p((P['grid_left_bottom'] + P['grid_left_top']) / 2, 4.2)
    b.append(text(px, py, 'and UP to the right)', 2.4, 'middle', fill=FAINT))
    # outline dimensions
    b.append(v.dim((xl_bot, yf), (xr, yf), yf - 8, True))
    b.append(v.dim((xl_top, yb), (xr, yb), yb + 5, True))
    b.append(v.dim((xl_bot, yb), (xl_top, yb), yb + 5, True))
    b.append(v.dim((xr, yf), (xr, yb), xr + 14, False))
    b.append(v.dim((xl_bot, yf), (xl_bot, ym), xl_bot - 5, False))
    b.append(v.dim((xl_top, ym), (xl_top, yb), xl_bot - 5, False))
    # stem dimensions from the datum
    b.append(v.dim((0, 0), (xr, 0), yb - 3, True, size=2.5))
    b.append(v.dim((xl_bot, P['dummy'][1]), (P['dummy'][0], P['dummy'][1]), yf - 3.5, True, size=2.5))
    b.append(v.dim((P['dummy'][0], P['dummy'][1]), (0, P['dummy'][1]), yf - 3.5, True, size=2.5))
    b.append(v.dim((xr, 0), (xr, P['stab']), xr + 5.5, False, size=2.5))
    b.append(v.dim((xr, -P['stab']), (xr, 0), xr + 5.5, False, size=2.5))
    b.append(v.dim((xr, P['dummy'][1]), (xr, 0), xr + 9.5, False, size=2.5))

    # legend
    lx, ly = 10, 26
    b.append(poly([(lx, ly), (lx + 10, ly)], w=0.5, closed=False) + text(lx + 13, ly + 1, 'Skirt (bottom edge)', 2.7))
    b.append(poly([(lx, ly + 5), (lx + 10, ly + 5)], w=0.25, dash='3,1.2', closed=False)
             + text(lx + 13, ly + 6, 'Top surface edge, before the dish', 2.7))
    b.append(poly([(lx, ly + 10), (lx + 10, ly + 10)], w=0.2, color=FAINT, dash='0.8,0.8', closed=False)
             + text(lx + 13, ly + 11, 'Key grid; skirt %.2f inside it all round' % g, 2.7))
    b.append(v.circle(0, 0, 0, w=0) + '<circle cx="%.2f" cy="%.2f" r="2" stroke="%s" stroke-width="0.25" '
             'fill="none" stroke-dasharray="1.2,0.8"/>' % (lx + 5, ly + 15, INK)
             + text(lx + 13, ly + 16, 'Stem boss underneath (hidden)', 2.7))

    # stem table
    tx0, sy = 10, 156
    b.append(heading(tx0, sy, 'Stem positions from S1'))
    cols = (0, 10, 27, 44)
    sy += 7
    for c, h in zip(cols, ('Stem', 'X', 'Y', 'Use')):
        b.append(text(tx0 + c, sy, h, 2.7, weight='bold', fill=FAINT))
    for (name, _, x, y), fn in zip(stems, ('switch', 'stab', 'stab', 'dummy')):
        sy += 4.6
        b.append(text(tx0 + cols[0], sy, name, 2.9, weight='bold') + text(tx0 + cols[1], sy, '%+.3f' % x, 2.9)
                 + text(tx0 + cols[2], sy, '%+.3f' % y, 2.9) + text(tx0 + cols[3], sy, fn, 2.9))
    s_, _ = wrap(tx0, sy + 5.5, '+X to the right, +Y towards the back of the keyboard.', 56, 2.5, fill=FAINT)
    b.append(s_)

    # outline table
    ox0 = 10
    oy0 = 60
    b.append(heading(ox0, oy0, 'Skirt corners from S1'))
    oy = oy0 + 7
    b.append(text(ox0, oy, 'X', 2.7, weight='bold', fill=FAINT) + text(ox0 + 20, oy, 'Y', 2.7, weight='bold',
                                                                       fill=FAINT))
    for x, y in skirt:
        oy += 4.4
        b.append(text(ox0, oy, '%+.3f' % x, 2.9) + text(ox0 + 20, oy, '%+.3f' % y, 2.9))
    oy += 9
    b.append(heading(ox0, oy, 'Top surface corners'))
    oy += 7
    for x, y in top:
        b.append(text(ox0, oy, '%+.3f' % x, 2.9) + text(ox0 + 20, oy, '%+.3f' % y, 2.9))
        oy += 4.4
    s_, _ = wrap(ox0, oy + 0.5, 'In plan, before the %.1f degree tilt. Top inset %.3f each side, %.3f front '
                 'and back, then moved %.1f back.' % (tilt, tx, ty, sk), 56, 2.5, fill=FAINT)
    b.append(s_)
    b.append(title_block(2, 'Plan, outline and stem positions', '3 : 1'))
    return page(''.join(b))


# ---------------------------------------------------------------- sheet 3: sections

def section_view(v, loops, hatch_id):
    out = []
    d = ' '.join('M ' + ' L '.join('%.3f %.3f' % v.p(*q) for q in lp) + ' Z' for lp in loops)
    out.append('<path d="%s" fill="url(#%s)" fill-rule="evenodd" stroke="%s" stroke-width="0.35" '
               'stroke-linejoin="round"/>' % (d, hatch_id, INK))
    return ''.join(out)


def sheet3():
    s = 3.0
    hatch = ('<defs><pattern id="h" width="1.6" height="1.6" patternUnits="userSpaceOnUse" '
             'patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="1.6" stroke="#999" '
             'stroke-width="0.25"/></pattern></defs>')
    b = [hatch]

    # A-A: cut at x = 0 through S1, S2, S3; looking from the right, front on the left
    va = View(92, 68, s)
    b.append(heading(10, 15, 'Section A-A, through S1, S2 and S3 (X = 0), front on the left'))
    loops = section(0, 0.001)
    b.append(section_view(va, loops, 'h'))
    b.append(va.line((yf - 4, 0), (yb + 4, 0), w=0.15, color=FAINT, dash='3,1'))
    for _, _, x, y in stems[:3]:
        b.append(va.line((y, -2), (y, height + 2), w=0.15, color=FAINT, dash='2,0.6,0.4,0.6'))
    ya, za = top[0][1], z_front
    yb_, zb = top[2][1], z_back
    b.append(va.dim((ya, za), (ya, 0), yf - 4, False))
    b.append(va.dim((yb_, 0), (yb_, zb), yb + 5, False))
    b.append(va.dim((-P['stab'], -1), (P['stab'], -1), -4.5, True, size=2.6))
    b.append(va.dim((0, -1), (P['stab'], -1), -9, True, size=2.6))
    b.append(va.dim((yf, 0), (yb, 0), -13.5, True, size=2.6))
    # tilt reference
    p0, p1 = va.p(ya - 2, za + 2 * math.tan(math.radians(tilt))), va.p(yb_ + 3, za)
    b.append(line(*p0, *p1, 0.15, ACCENT, '1.5,1'))
    tx_, ty_ = va.p(yb_ - 8, za + 1.4)
    b.append(text(tx_, ty_, '%.1f deg' % tilt, 2.6, 'middle', fill=ACCENT))
    x, y = va.p(y_mid, height + 3.2)
    b.append(text(x, y, '%.2f high at the key\'s middle (Y %+.3f), the tilt\'s pivot' % (height, y_mid), 2.4, 'middle', fill=FAINT))
    for lbl, yy in (('FRONT', yf - 1), ('BACK', yb + 1)):
        x, y = va.p(yy, -3.6)
        b.append(text(x, y, lbl, 2.6, 'end' if lbl == 'FRONT' else 'start', fill=FAINT))

    # B-B: cut at y = dummy y through S4, across both rows' widths; looking from the front
    yc = P['dummy'][1]
    vb = View(110, 170, s)
    b.append(heading(10, 124, 'Section B-B, through S4 (Y = %.2f), seen from the front' % yc))
    loops = section(1, yc + 0.001)
    b.append(section_view(vb, loops, 'h'))
    for _, _, x, y in (stems[3], stems[0]):
        b.append(vb.line((x, -2), (x, height + 3), w=0.15, color=FAINT, dash='2,0.6,0.4,0.6'))
    zc = top_z(yc)
    b.append(vb.dim((dish_x0, zc), (dish_x1, zc), zc + 4, True,
                    label='dish %.2f wide, R %.1f, %.2f deep' % (dish_w, dish_r, P['dish_depth']), size=2.5))
    b.append(vb.dim((xl_bot, 0), (xr, 0), -5, True, size=2.6))
    b.append(vb.dim((P['dummy'][0], 0), (0, 0), -9.5, True, size=2.6))
    b.append(vb.dim((xr, 0), (xr, zc), xr + 4, False, size=2.6))
    sx4 = P['dummy'][0] - P['stem_d'] / 2
    b.append(vb.dim((sx4, 0), (sx4, P['stem_drop']), xl_bot - 3.5, False, size=2.3))
    b.append(vb.dim((xl_bot, 0), (xl_bot + P['wall'], 0), -1.6, True, label='%.2f (horiz.)' % P['wall'],
                    size=2.3))

    # Stem detail
    sx, sy, ss = 228, 52, 6.0
    vs = View(sx, sy, ss)
    b.append(heading(185, 15, 'Stem, from below'))
    b.append(vs.circle(0, 0, P['stem_d'], w=0.35))
    cl, cw = P['cross_l'] / 2, P['cross_w'] / 2
    b.append(vs.poly([(-cl, -cw), (-cw, -cw), (-cw, -cl), (cw, -cl), (cw, -cw), (cl, -cw), (cl, cw), (cw, cw),
                      (cw, cl), (-cw, cl), (-cw, cw), (-cl, cw)], w=0.3, fill='#ddd'))
    b.append(vs.dim((-P['stem_d'] / 2, 0), (P['stem_d'] / 2, 0), -4.2, True, size=2.4))
    b.append(vs.dim((-cl, 0), (cl, 0), 3.4, True, size=2.4))
    b.append(vs.dim((0, -cw), (0, cw), 3.9, False, size=2.4))
    s_, _ = wrap(185, sy + 33, 'Standard Cherry MX female cross. Figures are the print\'s (cross %.1f deep), '
                 'tuned for FDM; please use your MX standard. All four stems are the same.' % P['cross_depth'],
                 82, 2.6)
    b.append(s_)
    # Measured
    my = 112
    b.append(heading(185, my, 'From the attached STL'))
    my += 7
    for k, val in (('X extent', '%+.3f to %+.3f' % bbox[0]), ('Y extent', '%+.3f to %+.3f' % bbox[1]),
                   ('Z extent', '%.3f to %.3f' % bbox[2])):
        b.append(text(185, my, k, 2.8, weight='bold') + text(205, my, val, 2.8))
        my += 4.4
    s_, _ = wrap(185, my + 1.5, 'Z is up from the skirt bottom. The top\'s back edge sits %.2f behind the skirt '
                 '(the print has no draft there); please add draft as your tooling needs.'
                 % (bbox[1][1] - yb), 82, 2.6, fill=FAINT)
    b.append(s_)
    b.append(title_block(3, 'Sections, profile and stem', '3 : 1 (stem 6 : 1)'))
    return page(''.join(b))


pages = [sheet1(), sheet2(), sheet3()]
w = PdfWriter()
for i, svg in enumerate(pages):
    w.append(PdfReader(io.BytesIO(cairosvg.svg2pdf(bytestring=svg.encode()))))
    if '--png' in sys.argv:
        cairosvg.svg2png(bytestring=svg.encode(), write_to=OUT.replace('.pdf', '-%d.png' % (i + 1)), scale=2)
w.write(OUT)
print('wrote', OUT, '- bbox', bbox)

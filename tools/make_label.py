"""Generate the sticker for the label recess under the case, 1:1, as an SVG.

Usage: make_label.py <out.svg> <board revision> [version]

Laid out after the original Commodore label (logo, two lines of text and a serial number between
rules, the maker's name in small type at the foot), but carrying this project's name and the board
revision instead of Commodore's logo and serial, so it is plainly a reproduction.  Positions are
scaled from a photo of an original.  Print it at 100% on sticker paper and cut on the outline.
"""
import sys

OUT, REV = sys.argv[1], sys.argv[2]
VERSION = sys.argv[3] if len(sys.argv) > 3 else ''

RECESS = (69.95, 51.46)  # the label recess under the case (BLBL in case/a1000_case.scad)
INSET = 0.5              # sticker edge inside the recess, each side
W, H = RECESS[0] - 2 * INSET, RECESS[1] - 2 * INSET
R = 1.5                  # corner radius
X0, X1 = 3.0, W - 3.5    # text and rule margins
FONT = "'Helvetica Neue', Helvetica, Arial, sans-serif"
URL = 'github.com/steveed/amiga-1000-keyboard-project'


def text(x, y, size, s, weight=400, anchor='start', spacing=0, fit=None):
    fit_attr = f' textLength="{fit}" lengthAdjust="spacingAndGlyphs"' if fit else ''
    return (f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" font-weight="{weight}" '
            f'letter-spacing="{spacing}" text-anchor="{anchor}"{fit_attr}>{s}</text>')


def rule(y):
    return f'<line x1="{X0}" y1="{y}" x2="{X1}" y2="{y}" stroke="#000" stroke-width="0.4"/>'


serial = f'Rev. {REV}' + (f'  {VERSION}' if VERSION else '')
parts = [
    # cut line
    f'<rect x="0.1" y="0.1" width="{W - 0.2:.2f}" height="{H - 0.2:.2f}" rx="{R}" fill="#fff" '
    f'stroke="#999" stroke-width="0.2"/>',
    # where the original has the Commodore logo and wordmark
    text(X0, 10.2, 6.5, 'a1000 keyboard', weight=900, fit=50),
    rule(12.2),
    text(X0, 18.9, 3.0, 'KEYBOARD FOR AMIGA<tspan font-size="1.6" dy="-1.4">TM</tspan><tspan dy="1.4"> 1000</tspan>'),
    text(X0, 22.8, 2.8, 'US Version', weight=700),
    rule(26.6),
    text(X0, 32.6, 5.0, serial, weight=300, spacing=0.4),
    rule(35.0),
    text(X1, 47.6, 1.5, URL, anchor='end'),
]

svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.2f}mm" height="{H:.2f}mm" '
       f'viewBox="0 0 {W:.2f} {H:.2f}">\n' + '\n'.join('  ' + p for p in parts) + '\n</svg>\n')
open(OUT, 'w').write(svg)
print(f'wrote {OUT}: {W:.2f} x {H:.2f} mm, rev {REV}')

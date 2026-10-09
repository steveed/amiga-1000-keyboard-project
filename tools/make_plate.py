"""Generate the switch plate from the PCB, so the two always line up.

Usage: make_plate.py <board.kicad_pcb> <plate.kicad_pcb> [us|iso]

Also writes <plate>.svg, a flat filled drawing of the plate for the README.

Writes a KiCad board containing only the plate outline and its cut-outs on
Edge.Cuts, in the same coordinates as the PCB. Measurements: docs/measurements.md.

Rev 1 (Mitsumi footprints): a 1.2 mm FR4 plate held by the switches; the original is
1.25 mm steel with tapped holes and folded edges.

Rev 2 (MX footprints): a 1.6 mm FR4 Cherry MX plate, in a US or ISO variant (the third
argument), as Henryk Richter does for the A500KB: the US left Shift's stabiliser would
land in the ISO short Shift's switch hole, so one plate can't take both. The stabiliser
cut-outs are the Cherry ones from his MX_Mitsumi_Hybrid plate footprints.
"""
import math
import re
import sys
import uuid

SRC, OUT = sys.argv[1], sys.argv[2]
VARIANT = sys.argv[3] if len(sys.argv) > 3 else None

PLATE_DEPTH = 120.9      # front to back
SIDE_MARGIN = 2.0        # plate overhang past the PCB at each end
TAB_LEFT = 50.8          # tab's left edge, from the plate's left edge
TAB_W, TAB_D = 18.0, 25.0
CASE_HOLE = 7.5
SCREW_HOLE = 2.7         # M2.5 clearance (FR4 can't be tapped); the original steel plate is tapped M2.5
THICKNESS = 1.2          # FR4; the original steel plate is 1.25 mm
CUTOUT = 14.0            # switch cut-out, square
BODY_DX = -4.75          # switch body centre relative to the pins, footprint coordinates
STAB_W, STAB_L = 3.0, 15.0
STAB_BAR = 2.6           # metal between the switch cut-out and the stabilizer slot
SPACE_STAB_W, SPACE_STAB_H = 7.1, 11.0

# Rev 2 (MX): keys left out of each plate variant, by key name
MX_SKIP = {'us': {'L SHIFT ISO', 'L SHIFT INTL', '(RET) INTL'},   # US: 2.5U Shift, Return with no dummy
           'iso': {'L SHIFT'}}                                   # ISO: short Shift, the < > key, the # key
MX_THICKNESS = 1.6
# Cherry stabiliser cut-out, around a stabiliser at x = s on the stem line, for the left stabiliser
# (s < 0); the right one mirrors it.  From Henryk Richter's MXMitsumi-2U-PlateCutout_Cherry.
CHERRY_STAB = [(-3.787, -5.53), (3.363, -5.53), (3.363, 6.77), (1.538, 6.77), (1.538, 7.97), (-1.462, 7.97),
               (-1.462, 6.77), (-3.787, 6.77), (-3.787, 0.5), (-4.162, 0.5), (-4.162, -2.3), (-3.787, -2.3)]
MX_STABS = {'2U': ('h', 11.938), 'LShift': ('h', 11.938), '7.5U': ('h', 57.15), 'Return': ('v', 11.938)}

STAB_H = {'L SHIFT', 'R SHIFT', 'TAB', 'BACKSPACE', 'KP 0', 'KP ENTER'}   # slots left and right of the switch
STAB_V = {'RETURN'}                                                    # slots above and below (the tall L-shaped key)
SPACE = 'SPACE'

src = open(SRC).read()


def block(s, start):
    depth, quoted, i = 0, False, start
    while True:
        c = s[i]
        if quoted and c == '\\':
            i += 2
            continue
        if c == '"':
            quoted = not quoted
        elif not quoted:
            if c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
                if depth == 0:
                    return s[start:i + 1]
        i += 1


def footprints():
    for m in re.finditer(r'\(footprint "([^"]+)"', src):
        b = block(src, m.start())
        at = re.search(r'\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)', b)
        ref = re.search(r'\(property "Reference" "([^"]+)"', b).group(1)
        val = re.search(r'\(property "Value" "([^"]*)"', b).group(1)
        dnp = bool(re.search(r'\(attr [^)]*\bdnp\b', b))
        yield m.group(1), ref, val, float(at.group(1)), float(at.group(2)), float(at.group(3) or 0), dnp


def place(x, y, rot, lx, ly):
    """Footprint-local point to board coordinates (KiCad: y down, rotation counter-clockwise)."""
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    return x + lx * c + ly * s, y - lx * s + ly * c


# PCB outline and its inner cut-outs, from Edge.Cuts lines
lines = [tuple(map(float, m.groups())) for m in re.finditer(
    r'\(gr_line\s*\(start ([-\d.]+) ([-\d.]+)\)\s*\(end ([-\d.]+) ([-\d.]+)\)(?:(?!\(gr_).)*?\(layer "Edge.Cuts"\)', src, re.S)]
xs = [v for l in lines for v in (l[0], l[2])]
ys = [v for l in lines for v in (l[1], l[3])]
left, right, front = min(xs), max(xs), max(ys)
# the left end's back edge: the horizontal outline segment touching the left edge
left_back = min(min(l[1], l[3]) for l in lines if min(l[0], l[2]) == left and l[1] == l[3])
inner = [l for l in lines if left < min(l[0], l[2]) and max(l[0], l[2]) < right and front - 30 < min(l[1], l[3])]

items = []
svg_paths = []   # the same shapes as SVG subpaths, for a crisp flat drawing


def uid():
    return str(uuid.uuid4())


boxes = []      # cut-out bounding boxes (x0, y0, x1, y1), so the MX plates' screw holes can avoid them


def rect(cx, cy, w, h):
    x0, y0, x1, y1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
    boxes.append((x0, y0, x1, y1))
    svg_paths.append('M%.3f %.3fH%.3fV%.3fH%.3fZ' % (x0, y0, x1, y1, x0))
    items.append('(gr_rect (start %.4f %.4f) (end %.4f %.4f) (stroke (width 0.1) (type solid)) (fill no) '
                 '(layer "Edge.Cuts") (uuid "%s"))' % (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, uid()))


def hole(cx, cy, d):
    r = d / 2
    svg_paths.append('M%.3f %.3fa%.3f %.3f 0 1 0 %.3f 0a%.3f %.3f 0 1 0 %.3f 0Z' % (cx - r, cy, r, r, d, r, r, -d))
    items.append('(gr_circle (center %.4f %.4f) (end %.4f %.4f) (stroke (width 0.1) (type solid)) (fill no) '
                 '(layer "Edge.Cuts") (uuid "%s"))' % (cx, cy, cx + d / 2, cy, uid()))


def poly(pts):
    boxes.append((min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts)))
    svg_paths.append('M' + 'L'.join('%.3f %.3f' % xy for xy in pts) + 'Z')
    p = ' '.join('(xy %.4f %.4f)' % xy for xy in pts)
    items.append('(gr_poly (pts %s) (stroke (width 0.1) (type solid)) (fill no) (layer "Edge.Cuts") (uuid "%s"))' % (p, uid()))


# outline with the tab on the back edge
pl, pr = left - SIDE_MARGIN, right + SIDE_MARGIN
pb, pf = left_back, left_back + PLATE_DEPTH
tl = pl + TAB_LEFT
poly([(pl, pb), (tl, pb), (tl, pb - TAB_D), (tl + TAB_W, pb - TAB_D), (tl + TAB_W, pb), (pr, pb), (pr, pf), (pl, pf)])
hole(tl + TAB_W / 2, pb - TAB_D / 2, CASE_HOLE)
boxes.clear()    # the outline isn't a cut-out

def mx_stab(cx, cy, kind, s):
    """Cherry stabiliser cut-outs either side of a key at (cx, cy)."""
    for side in (-1, 1):
        pts = []
        for x, y in CHERRY_STAB:
            px = -s + x if side < 0 else s - x          # left stabiliser as drawn, right one mirrored
            pts.append((px, y) if kind == 'h' else (y, -px))
        poly([(cx + px, cy + py) for px, py in pts])


counts = {'switch': 0, 'stab': 0, 'screw': 0, 'case': 1}
space = None
screws = []      # screw holes go in last, clear of every cut-out
skipped = []
for lib, ref, val, x, y, rot, dnp in footprints():
    if ':MX_A1000_' in lib and 'LED' not in lib:
        if val in MX_SKIP[VARIANT]:
            continue
        rect(x, y, CUTOUT, CUTOUT)
        counts['switch'] += 1
        stab = MX_STABS.get(lib.split('MX_A1000_')[1])
        if stab:
            mx_stab(x, y, *stab)
            counts['stab'] += 2
        continue
    if lib.endswith('Mitsumi_A1000_Switch') and not dnp:
        cx, cy = place(x, y, rot, BODY_DX, 0)
        rect(cx, cy, CUTOUT, CUTOUT)
        counts['switch'] += 1
        off = CUTOUT / 2 + STAB_BAR + STAB_W / 2
        if val in STAB_H:
            rect(cx - off, cy, STAB_W, STAB_L); rect(cx + off, cy, STAB_W, STAB_L); counts['stab'] += 2
        elif val in STAB_V:
            rect(cx, cy - off, STAB_L, STAB_W); rect(cx, cy + off, STAB_L, STAB_W); counts['stab'] += 2
        if val == SPACE:
            space = (cx, cy)
    elif 'MountingHole_3.8mm_Plate' in lib:
        screws.append((ref, x, y))
    elif 'MountingHole_7.5mm' in lib:
        hole(x, y, CASE_HOLE); counts['case'] += 1

# Plate screw holes.  On the MX plates a hole that would touch a cut-out (H8, under keypad Enter's
# stabiliser) is left out: the switches hold the plate, the screws are optional.
for ref, x, y in screws:
    r = SCREW_HOLE / 2 + 0.5
    if VARIANT and any(x0 - r < x < x1 + r and y0 - r < y < y1 + r for x0, y0, x1, y1 in boxes):
        skipped.append(ref)
        continue
    hole(x, y, SCREW_HOLE); counts['screw'] += 1

# space bar stabilizers sit over the PCB's two inner cut-outs
cuts = []
for l in inner:
    for group in cuts:
        if abs(group[0][0] - l[0]) < 15 and abs(group[0][1] - l[1]) < 15:
            group.append(l)
            break
    else:
        cuts.append([l])
for group in cuts:
    gx = [v for l in group for v in (l[0], l[2])]
    gy = [v for l in group for v in (l[1], l[3])]
    rect((min(gx) + max(gx)) / 2, (min(gy) + max(gy)) / 2, SPACE_STAB_W, SPACE_STAB_H)
    counts['stab'] += 1

head = src[:src.index('(footprint ')]
head = re.sub(r'\(title "[^"]*"\)', '(title "Amiga 1000 Keyboard - switch plate")', head, count=1)
THICKNESS = MX_THICKNESS if VARIANT else THICKNESS
head = re.sub(r'\(general\s*\(thickness [\d.]+\)', '(general\n\t\t(thickness %g)' % THICKNESS, head, count=1)
head = re.sub(r'(\(layer "dielectric 1"\s*\(type "core"\)\s*\(thickness )[\d.]+', lambda m: m.group(1) + '%g' % (THICKNESS - 0.09), head, count=1)
open(OUT, 'w').write(head + '\n'.join(items) + '\n\t(embedded_fonts no)\n)\n')
vx, vy, vw, vh = pl - 1, pb - TAB_D - 1, pr - pl + 2, PLATE_DEPTH + TAB_D + 2
open(OUT.rsplit('.', 1)[0] + '.svg', 'w').write(
    '<svg xmlns="http://www.w3.org/2000/svg" width="%.2fmm" height="%.2fmm" viewBox="%.3f %.3f %.3f %.3f">'
    '<path fill="#1f4d33" fill-rule="evenodd" stroke="#0f2a1b" stroke-width="0.15" d="%s"/></svg>\n'
    % (vw, vh, vx, vy, vw, vh, ''.join(svg_paths)))
print('plate %.2f x %.2f mm; %d switch cut-outs, %d stabilizer cut-outs, %d screw holes, %d case holes%s'
      % (pr - pl, PLATE_DEPTH, counts['switch'], counts['stab'], counts['screw'], counts['case'],
         '; space bar at (%.2f, %.2f)' % space if space else '')
      + ('; no screw hole at %s (clashes with a cut-out)' % ', '.join(skipped) if skipped else ''))

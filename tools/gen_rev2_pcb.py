"""Build the rev 2 board from rev 1's board and the rev 2 schematic.

    python3 tools/gen_rev2_pcb.py      (in the kicad container: it needs pcbnew)

Rev 1's outline, stack-up, design rules, GND pours and back silkscreen carry over; its parts and
tracks don't.  Every footprint in the rev 2 netlist is loaded, linked to its symbol (so the
schematic parity check passes) and given its nets.  Switches go where rev 1 has them, now by key
centre; each key's diode sits on the back, between its row and the one above.  The controller-strip
parts get a first placement; tracks are not drawn.
"""

import os
import re
import subprocess
import sys
import uuid

import pcbnew

sys.path.insert(0, os.path.dirname(__file__))
from kisexp import Sym, parse, dump, find, find_all  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REV1 = os.path.join(REPO, 'pcb/amiga-1000-keyboard.kicad_pcb')
SCH = os.path.join(REPO, 'pcb/rev_2/amiga-1000-keyboard-rev2.kicad_sch')
OUT = os.path.join(REPO, 'pcb/rev_2/amiga-1000-keyboard-rev2.kicad_pcb')
NET = '/tmp/rev2.net'
BASE = '/tmp/rev2-base.kicad_pcb'
LIBS = {'amiga1000': os.path.join(REPO, 'pcb/lib_fp.pretty')}
STOCK = '/usr/share/kicad/footprints'

MITSUMI_OFFSET = 4.75      # rev 1's footprints sit on the pin midpoint, 4.75 mm right of the key centre
DIODE_TRIES = [(dx, dy) for dy in (-9.525, 9.525) for dx in (0, -3, 3, -6, 6, -9, 9)]   # key diode, on the back
DIODE_CLEAR = 0.5

# Controller strip, first placement: (x, y, rotation, back side).  KiCad coordinates.
PLACE = {
    # controller group, central on the strip.  U1 is turned 180 degrees so its six row pins (PF0-PF7)
    # face the keyboard instead of the back edge; the crystal sits on the back-edge side, where the
    # XTAL pins now are.  The caps that would block the pins are on the back, under U1.
    'U1': (192.0, 54.0, 180, False), 'Y1': (191.5, 43.4, 0, False),
    'C1': (187.0, 43.4, 90, False), 'C2': (196.0, 43.4, 90, False),
    'C3': (188.5, 50.5, 0, True), 'C4': (195.5, 50.5, 180, True), 'C5': (199.0, 60.5, 0, False),
    'C6': (205.0, 58.0, 90, False), 'C7': (179.0, 54.0, 90, False),
    'C8': (202.6, 54.0, 90, False), 'C9': (194.4, 64.4, 90, False),     # UCAP and AREF, outside U1's via ring
    'R1': (214.0, 49.0, 90, False), 'SW93': (220.0, 53.0, 0, False),
    'R2': (228.0, 49.0, 90, False), 'SW94': (234.0, 53.0, 0, False),
    'J3': (248.0, 53.0, 0, False), 'TP1': (260.0, 53.0, 0, False),
    'R3': (214.0, 60.0, 0, False),
    # USB-C on the step face at x 118.55, opening to the left; fuse, CC resistors, ESD, series resistors
    'J2': (122.42, 45.35, 270, False), 'F1': (131.0, 41.8, 0, False),
    'R7': (130.0, 52.0, 90, False), 'R8': (133.0, 52.0, 90, False),
    'U3': (139.0, 46.5, 0, False), 'R9': (146.0, 45.0, 0, False), 'R10': (146.0, 48.5, 0, False),
    # power mux and its parts, between the USB group and the controller, clear of the back edge
    'U2': (161.0, 49.0, 0, False), 'C10': (154.0, 45.0, 0, False), 'C11': (158.0, 44.5, 0, False),
    'C12': (167.0, 47.0, 90, False), 'R4': (154.0, 55.0, 90, False), 'R5': (157.0, 55.0, 90, False),
    'R6': (166.0, 54.0, 90, False),
    # Amiga cable header on the left step's back edge, behind the case's jack at x 90 (doc)
    'J1': (104.9, 55.3, 180, False), 'FB1': (96.0, 62.0, 0, False), 'FB2': (100.0, 62.0, 0, False),
    'FB3': (104.0, 62.0, 0, False), 'C13': (108.0, 62.0, 0, False), 'C14': (112.0, 62.0, 0, False),
    'C15': (116.0, 62.0, 0, False),
}


def mm(v):
    return pcbnew.FromMM(v)


def netlist():
    subprocess.run(['kicad-cli', 'sch', 'export', 'netlist', '--format', 'kicadsexpr', '-o', NET, SCH],
                   check=True, capture_output=True)
    n = parse(open(NET).read())
    comps = {}
    for c in find_all(find(n, 'components'), 'comp'):
        fields = {f[1][1]: (f[2] if len(f) > 2 else '') for f in find_all(find(c, 'fields') or [], 'field')}
        props = {p[1][1]: (p[2][1] if len(p) > 2 else '') for p in find_all(c, 'property')}
        comps[find(c, 'ref')[1]] = dict(value=find(c, 'value')[1], footprint=find(c, 'footprint')[1],
                                        tstamp=find(c, 'tstamps')[1], fields=fields, props=props)
    pins = {}
    for net in find_all(find(n, 'nets'), 'net'):
        name = find(net, 'name')[1]
        for node in find_all(net, 'node'):
            pins[(find(node, 'ref')[1], str(find(node, 'pin')[1]))] = name
    return comps, pins


def rev1_switches():
    """{ref: (key centre x, y)} from rev 1, plus the Return stem."""
    s = open(REV1).read()
    out = {}
    for m in re.finditer(r'\(footprint "amiga1000:Mitsumi_A1000_Switch".*?\n\t\t\(at ([-\d.]+) ([-\d.]+) ?([-\d.]*)\)'
                         r'.*?\(property "Reference" "(SW\d+)"', s, re.S):
        x, y, rot, ref = float(m[1]), float(m[2]), m[3], m[4]
        if rot == '270':                 # Return: pins face the front, the stem is behind them
            out[ref] = (x, y - MITSUMI_OFFSET)
        else:
            assert not rot, (ref, rot)
            out[ref] = (x - MITSUMI_OFFSET, y)
    return out


def rev1_positions(board):
    return {fp.GetReference(): fp.GetPosition() for fp in board.GetFootprints()}


def strip_rev1():
    """Rev 1's board without its footprints, tracks, vias and pour fills, written to BASE.  Done on
    the file because KiCad 10's Python can't list a board's tracks (GetTracks fails)."""
    b = parse(open(REV1).read())
    keep = []
    for x in b:
        if isinstance(x, list) and x and x[0] in ('footprint', 'segment', 'via', 'arc'):
            continue
        if isinstance(x, list) and x and x[0] == 'zone':
            x = [y for y in x if not (isinstance(y, list) and y and y[0] == 'filled_polygon')]
        keep.append(x)
    with open(BASE, 'w') as f:
        f.write(dump(keep) + '\n')


def circles(fp, back_only=False):
    """Pads and holes as (x, y, r) circles, mm.  SMD pads count only on the side asked for."""
    out = []
    for p in fp.Pads():
        smd = p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD
        if smd and back_only and not p.IsOnLayer(pcbnew.B_Cu):
            continue
        sz = p.GetSize(pcbnew.B_Cu if p.IsOnLayer(pcbnew.B_Cu) else pcbnew.F_Cu)
        q = p.GetPosition()
        out.append((pcbnew.ToMM(q.x), pcbnew.ToMM(q.y), pcbnew.ToMM(max(sz.x, sz.y)) / 2))
    return out


def edge_segments(board):
    segs = []
    for d in board.GetDrawings():
        if isinstance(d, pcbnew.PCB_SHAPE) and d.GetLayer() == pcbnew.Edge_Cuts:
            a, b = d.GetStart(), d.GetEnd()
            segs.append((pcbnew.ToMM(a.x), pcbnew.ToMM(a.y), pcbnew.ToMM(b.x), pcbnew.ToMM(b.y)))
    return segs


def seg_dist(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy or 1)))
    return ((px - x1 - t * dx) ** 2 + (py - y1 - t * dy) ** 2) ** 0.5


def place_diodes(board, diodes, keys):
    """Each key's diode goes on the back at the first spot in DIODE_TRIES that clears every pad and
    hole (both sides for through-hole, the back for SMD), the other diodes and the board edge."""
    others = [fp for fp in board.GetFootprints() if fp not in diodes]
    obstacles = [c for fp in others for c in circles(fp, back_only=True)]
    edges = edge_segments(board)
    for fp in sorted(diodes, key=lambda f: int(f.GetReference()[1:])):
        kx, ky = keys['SW' + fp.GetReference()[1:]]
        fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        for dx, dy in DIODE_TRIES:
            fp.SetPosition(pcbnew.VECTOR2I(mm(kx + dx), mm(ky + dy)))
            mine = circles(fp)
            if all(((x - ox) ** 2 + (y - oy) ** 2) ** 0.5 - r - orr >= DIODE_CLEAR
                   for x, y, r in mine for ox, oy, orr in obstacles) and \
               all(seg_dist(x, y, *e) - r >= DIODE_CLEAR for x, y, r in mine for e in edges):
                obstacles += mine
                break
        else:
            raise SystemExit(f'{fp.GetReference()}: no room for the diode')


def stable(text):
    """Make the saved board the same on every run.  KiCad gives each loaded footprint a random UUID
    and saves footprints in UUID order, and the router works through parts in file order, so a
    random order routes differently each time.  Footprints go in reference order and every UUID
    inside them is derived from the reference."""
    blocks = []
    for m in re.finditer(r'\n\t\(footprint .*?\n\t\)(?=\n)', text, re.S):
        blocks.append((m.start(), m.end(), m.group(0)))
    def key(b):
        ref = re.search(r'\(property "Reference" "([^"]+)"', b[2]).group(1)
        m = re.fullmatch(r'([A-Z#]+)(\d+)', ref)
        return (m.group(1), int(m.group(2))) if m else (ref, 0)
    def renumber(block):
        ref = re.search(r'\(property "Reference" "([^"]+)"', block).group(1)
        n = iter(range(10 ** 6))
        return re.sub(r'\(uuid "[^"]+"\)', lambda _: f'(uuid "{uuid.uuid5(uuid.NAMESPACE_URL, f"rev2/{ref}/{next(n)}")}")', block)
    ordered = ''.join(renumber(b[2]) for b in sorted(blocks, key=key))
    return text[:blocks[0][0]] + ordered + text[blocks[-1][1]:] if blocks else text


# Pre-routed escapes for pins the router struggles to reach: (part, pad, net, layer-side length mm).
# The TPS2116's pins are 0.5 mm apart; VIN2 sits mid-side between two power pins and its GND pin
# sits in a corner, and the router kept leaving one or the other just short.
ESCAPES = [('U2', '6', '/VBUS', 2.4), ('U2', '1', 'GND', 2.4)]


# Fan-out for the 32U4: every pin but the crystal and USB data pins gets a short track straight out
# to its own via, the vias alternating between two radii so neighbours 0.8 mm apart don't collide.
# About 20 matrix lines converge on this chip on two layers; the router finds a ring of vias with room
# around it far easier to reach than 0.8 mm-pitch pads.
FANOUT = dict(ref='U1', radii=(7.6, 8.6), skip={'/XTAL1', '/XTAL2', '/USB_DP_MCU', '/USB_DN_MCU'})


def fanout(board):
    fp = board.FindFootprintByReference(FANOUT['ref'])
    c = fp.GetPosition()
    for pad in fp.Pads():
        net = pad.GetNet()
        if not pad.GetNetname() or pad.GetNetname() in FANOUT['skip'] or pad.GetNetname().startswith('unconnected'):
            continue
        p = pad.GetPosition()
        dx, dy = pcbnew.ToMM(p.x - c.x), pcbnew.ToMM(p.y - c.y)
        r = FANOUT['radii'][int(pad.GetNumber()) % 2]
        if abs(dx) > abs(dy):                       # a pin on the left or right side
            v = pcbnew.VECTOR2I(c.x + mm(r if dx > 0 else -r), p.y)
        else:                                       # top or bottom
            v = pcbnew.VECTOR2I(p.x, c.y + mm(r if dy > 0 else -r))
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(p); t.SetEnd(v); t.SetWidth(mm(0.2)); t.SetLayer(pcbnew.F_Cu); t.SetNet(net)
        board.Add(t)
        via = pcbnew.PCB_VIA(board)
        via.SetPosition(v); via.SetWidth(mm(0.6)); via.SetDrill(mm(0.3)); via.SetNet(net)
        board.Add(via)


def escapes(board, nets):
    """A short top-layer track straight out of each listed pad, away from the part, to a via."""
    for ref, num, net, length in ESCAPES:
        fp = board.FindFootprintByReference(ref)
        pad = [p for p in fp.Pads() if p.GetNumber() == num][0]
        a = pad.GetPosition()
        out = 1 if a.x > fp.GetPosition().x else -1
        b = pcbnew.VECTOR2I(a.x + out * mm(length), a.y)
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(a); t.SetEnd(b); t.SetWidth(mm(0.2)); t.SetLayer(pcbnew.F_Cu); t.SetNet(nets[net])
        board.Add(t)
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(b); v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3)); v.SetNet(nets[net])
        board.Add(v)


def load_fp(fpid):
    lib, name = fpid.split(':')
    path = LIBS.get(lib, f'{STOCK}/{lib}.pretty')
    fp = pcbnew.FootprintLoad(path, name)
    if fp is None:
        raise SystemExit(f'footprint {fpid} not found')
    fp.SetFPIDAsString(fpid)
    return fp


def main():
    comps, pins = netlist()
    old = rev1_positions(pcbnew.LoadBoard(REV1))
    keys = rev1_switches()
    strip_rev1()
    board = pcbnew.LoadBoard(BASE)

    for d in list(board.GetDrawings()):
        if isinstance(d, pcbnew.PCB_TEXT) and d.GetLayer() == pcbnew.B_SilkS:
            d.SetText('AMIGA 1000 KEYBOARD REV 2 ${VERSION}\nATmega32U4, Cherry MX switches\n'
                      'github.com/steveed/amiga-1000-keyboard-project')
        if isinstance(d, pcbnew.PCB_TEXT) and d.GetLayer() == pcbnew.Cmts_User:
            board.Remove(d)
        # drop the space bar's Mitsumi stabiliser cutouts: rev 2 takes MX switches only
        if isinstance(d, pcbnew.PCB_SHAPE) and d.GetLayer() == pcbnew.Edge_Cuts:
            ends = [(pcbnew.ToMM(q.x), pcbnew.ToMM(q.y)) for q in (d.GetStart(), d.GetEnd())]
            if all(165 < y < 177 and (100 < x < 108 or 215 < x < 223) for x, y in ends):
                board.Remove(d)

    nets = {}
    for name in sorted(set(pins.values())):
        ni = pcbnew.NETINFO_ITEM(board, name)
        board.Add(ni)
        nets[name] = ni

    caps = keys['SW43']
    diodes = []
    for ref, c in sorted(comps.items()):
        fp = load_fp(c['footprint'])
        fp.SetReference(ref)
        fp.SetValue(c['value'])
        fp.SetPath(pcbnew.KIID_PATH('/' + c['tstamp']))
        for k, v in c['fields'].items():
            if k not in ('Reference', 'Value', 'Footprint', 'Datasheet', 'Description'):
                fp.SetField(k, v)
                fld = [f for f in fp.GetFields() if f.GetName() == k][0]
                fld.SetVisible(False)
                fld.SetLayer(pcbnew.F_Fab)
        fp.SetDNP('dnp' in c['props'])
        fp.SetExcludedFromBOM('exclude_from_bom' in c['props'])
        board.Add(fp)

        if ref.startswith('SW') and ref in keys:
            x, y = keys[ref]
            fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        elif re.fullmatch(r'D\d+', ref) and int(ref[1:]) <= 91:
            diodes.append(fp)                    # placed once everything else is down
        elif ref == 'D92':                       # Caps Lock LED: 5.08 mm south of the key centre
            fp.SetPosition(pcbnew.VECTOR2I(mm(caps[0]), mm(caps[1] + 5.08)))
        elif re.fullmatch(r'H\d+', ref):
            fp.SetPosition(old[ref])
        elif ref in PLACE:
            x, y, rot, back = PLACE[ref]
            fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
            fp.SetOrientationDegrees(rot)
            if back:
                fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        elif not ref.startswith('SW'):
            raise SystemExit(f'{ref}: no placement')
        else:
            raise SystemExit(f'{ref}: not a rev 1 switch position')

        for pad in fp.Pads():
            name = pins.get((ref, pad.GetNumber()))
            if name:
                pad.SetNet(nets[name])

    place_diodes(board, diodes, keys)
    escapes(board, nets)
    fanout(board)
    # Save beside a throwaway project: SaveBoard rewrites the project file next to the board,
    # which would drop the ERC settings and the VERSION text variable from rev 2's.
    tmp = '/tmp/rev2-out/' + os.path.basename(OUT)
    os.makedirs(os.path.dirname(tmp), exist_ok=True)
    board.SetFileName(tmp)
    pcbnew.SaveBoard(tmp, board)
    with open(OUT, 'w') as f:
        f.write(stable(open(tmp).read()))
    print(f'wrote {os.path.relpath(OUT, REPO)}: {len(comps)} footprints, {len(nets)} nets')


if __name__ == '__main__':
    main()

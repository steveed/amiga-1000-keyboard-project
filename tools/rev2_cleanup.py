"""Tidy the routed rev 2 board: remove the vias and tracks KiCad's DRC reports as dangling.

    python3 tools/rev2_cleanup.py build/rev2-dangling.json   (make rev2-route runs it)

The U1 fan-out gives every pin a via; where the router reached the pad directly, the via and its stub
are left going nowhere.  Each round removes only what DRC reports as dangling: a via that at most one
track touches (KiCad calls a via dangling when it connects on one layer only, but the router may end
two tracks on its ring and use it as the joint, so a via with two or more tracks stays), and any
track with a free end.  A stub that ran to a removed via shows up as dangling on the next round,
while a track that still carries a connection never does, so repeating this can't open a net.  Run
it with the JSON from `kicad-cli pcb drc --format json --severity-warning`; it prints how many items
it removed, and make repeats it until there are none.
"""

import json
import re
import sys

BOARD = 'pcb/rev_2/amiga-1000-keyboard-rev2.kicad_pcb'


def blocks(text, kind):
    """{uuid: (start, end)} spans of top-level (kind ...) items."""
    out = {}
    for m in re.finditer(rf'\n\t\({kind}\n.*?\n\t\)(?=\n)', text, re.S):
        u = re.search(r'\(uuid "([^"]+)"\)', m.group(0))
        out[u.group(1)] = (m.start(), m.end(), m.group(0))
    return out


def main():
    drc = json.load(open(sys.argv[1]))
    dead = {i['uuid'] for v in drc['violations'] if v['type'] in ('via_dangling', 'track_dangling')
            for i in v['items']}
    text = open(BOARD).read()
    vias, segs = blocks(text, 'via'), blocks(text, 'segment')
    def touching(via):
        x, y = map(float, re.search(r'\(at ([-\d.]+) ([-\d.]+)\)', via).groups())
        r = float(re.search(r'\(size ([\d.]+)\)', via).group(1)) / 2 + 0.01
        n = 0
        for _, _, seg in segs.values():
            if re.search(r'\(net (?:\d+ )?"([^"]*)"\)', seg).group(1) != re.search(r'\(net (?:\d+ )?"([^"]*)"\)', via).group(1):
                continue
            for k in ('start', 'end'):
                ex, ey = map(float, re.search(rf'\({k} ([-\d.]+) ([-\d.]+)\)', seg).groups())
                n += (ex - x) ** 2 + (ey - y) ** 2 <= r * r
        return n

    drop = [u for u in dead if u in segs or (u in vias and touching(vias[u][2]) <= 1)]
    spans = sorted({(vias.get(u) or segs[u])[:2] for u in drop}, reverse=True)
    for a, b in spans:
        text = text[:a] + text[b:]
    open(BOARD, 'w').write(text)
    print(len(spans))


if __name__ == '__main__':
    main()

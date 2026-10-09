"""Generate the rev 2 hybrid keyswitch footprints: an Amiga 1000 Mitsumi KCT switch or a Cherry MX
switch in the same place, after the idea in Henryk Richter's MX_Mitsumi_Hybrid footprints (A500KB).

    python3 tools/gen_hybrid_fp.py

Origin is the keycap centre.  The Mitsumi pins are where rev 1 has them: 9.04 mm apart, one above
the other, 4.75 mm right of the centre.  The MX switch is turned 180 degrees (pins south, LED holes
north), which keeps its pins clear of the Mitsumi Caps Lock LED leads.  The MX pin that lands 2.2 mm
from a Mitsumi pin gets the same pad number, so the two overlap instead of needing clearance.

Wide keys add MX PCB-mount stabiliser holes (Cherry spacing: 23.876 mm for 2U-2.75U, 114.3 mm for
the space bar, which uses a 7U stabiliser).  The Mitsumi stabilisers are plate mounted.
"""

import os
import uuid

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, 'pcb/lib_fp.pretty')
NS = uuid.UUID('0b5e9b1e-4f7a-4c1e-9d3e-a1000f00f002')
U = 19.05

MITSUMI = [('1', 4.75, -4.52), ('2', 4.75, 4.52)]
MITSUMI_PAD, MITSUMI_DRILL = 2.5, 1.2          # rev 1 used 2.3; 2.5 makes the shared pad overlap solid
MX = [('2', 3.81, 2.54), ('1', -2.54, 5.08)]   # standard MX pins, turned 180 degrees
MX_PAD, MX_DRILL = 2.25, 1.5
MX_CENTRE, MX_PEG = 3.988, 1.75                # PCB-mount pegs at +-5.08
STAB_SMALL, STAB_LARGE = 3.048, 3.988          # at y -6.985 and +8.255 from the stem line

# name: (keycap width in U, stabiliser half-spacing in mm or None)
KEYS = {
    '1U': (1, None), '1.25U': (1.25, None), '1.5U': (1.5, None), '1.75U': (1.75, None),
    '2U': (2, 11.938), '2.5U': (2.5, 11.938), '7.5U': (7.5, 57.15),
}


def u(name, *k):
    return str(uuid.uuid5(NS, '/'.join([name] + [str(x) for x in k])))


def n(v):
    s = f'{v:.4f}'.rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


def line(name, x1, y1, x2, y2, layer, w):
    return (f'\t(fp_line (start {n(x1)} {n(y1)}) (end {n(x2)} {n(y2)}) (stroke (width {w}) (type solid)) '
            f'(layer "{layer}") (uuid "{u(name, "line", layer, x1, y1, x2, y2)}"))')


def rect(name, x0, y0, x1, y1, layer, w):
    return [line(name, x0, y0, x1, y0, layer, w), line(name, x1, y0, x1, y1, layer, w),
            line(name, x1, y1, x0, y1, layer, w), line(name, x0, y1, x0, y0, layer, w)]


def pad(name, num, x, y, size, drill):
    kind = 'np_thru_hole' if num == '' else 'thru_hole'
    layers = '"*.Cu" "*.Mask"'
    return (f'\t(pad "{num}" {kind} circle (at {n(x)} {n(y)}) (size {n(size)} {n(size)}) (drill {n(drill)}) '
            f'(layers {layers}) (remove_unused_layers no) (uuid "{u(name, "pad", num, x, y)}"))')


def text(name, kind, value, y, layer):
    return (f'\t(property "{kind}" "{value}" (at 0 {n(y)} 0) (layer "{layer}") (uuid "{u(name, kind)}") '
            f'(effects (font (size 1 1) (thickness 0.15))))')


def footprint(name, descr, body):
    head = [f'(footprint "{name}" (version 20260206) (generator "pcbnew") (generator_version "10.0") (layer "F.Cu")',
            f'\t(descr "{descr}")', '\t(tags "keyswitch Mitsumi KCT Cherry MX hybrid Amiga 1000")']
    return '\n'.join(head + body + ['\t(attr through_hole)', ')']) + '\n'


def switch(name, width, stab):
    hw = width * U / 2
    body = [text(name, 'Reference', 'REF**', -11.5, 'F.SilkS'), text(name, 'Value', name, 11.5, 'F.Fab')]
    body += rect(name, -hw, -U / 2, hw, U / 2, 'Dwgs.User', 0.1)        # keycap
    body += rect(name, -7, -7, 7, 7, 'F.Fab', 0.1)                       # 14 mm switch body / plate cutout
    body += rect(name, -7.5, -7.5, 7.5, 7.5, 'F.CrtYd', 0.05)
    body += [line(name, x, -7.2, x, 7.2, 'F.SilkS', 0.12) for x in (-7.2, 7.2)]
    body += [line(name, -7.2, y, 7.2, y, 'F.SilkS', 0.12) for y in (-7.2, 7.2)]
    for num, x, y in MITSUMI:
        body.append(pad(name, num, x, y, MITSUMI_PAD, MITSUMI_DRILL))
    for num, x, y in MX:
        body.append(pad(name, num, x, y, MX_PAD, MX_DRILL))
    body.append(pad(name, '', 0, 0, MX_CENTRE, MX_CENTRE))
    for x in (-5.08, 5.08):
        body.append(pad(name, '', x, 0, MX_PEG, MX_PEG))
    if stab:
        for x in (-stab, stab):
            body.append(pad(name, '', x, -6.985, STAB_SMALL, STAB_SMALL))
            body.append(pad(name, '', x, 8.255, STAB_LARGE, STAB_LARGE))
            body += rect(name, x - 3.4, -8.6, x + 3.4, 10.3, 'F.CrtYd', 0.05)
    descr = (f'{width}U key, Amiga 1000 Mitsumi KCT or Cherry MX (turned 180 deg). Mitsumi pins 9.04 mm apart, '
             f'4.75 mm right of centre' + (f'; MX PCB-mount stabiliser at +-{stab} mm' if stab else ''))
    return footprint(name, descr, body)


def mx_led():
    name = 'Hybrid_A1000_MX_LED'
    body = [text(name, 'Reference', 'REF**', -2.2, 'F.SilkS'), text(name, 'Value', name, 2.2, 'F.Fab')]
    body.append(pad(name, '1', -1.27, 0, 1.6, 0.9).replace('circle', 'rect', 1))
    body.append(pad(name, '2', 1.27, 0, 1.6, 0.9))
    body += rect(name, -2.3, -1.1, 2.3, 1.1, 'F.CrtYd', 0.05)
    return footprint(name, '3 mm LED through a Cherry MX switch (Caps Lock), placed 5.08 mm north of the key centre: '
                     'cathode pad 1 (square) west, anode pad 2 east', body)


def main():
    for k, (w, stab) in KEYS.items():
        name = f'Hybrid_A1000_{k}'
        with open(os.path.join(OUT, name + '.kicad_mod'), 'w') as f:
            f.write(switch(name, w, stab))
    with open(os.path.join(OUT, 'Hybrid_A1000_MX_LED.kicad_mod'), 'w') as f:
        f.write(mx_led())
    print(f'wrote {len(KEYS) + 1} footprints to {os.path.relpath(OUT, REPO)}')


if __name__ == '__main__':
    main()

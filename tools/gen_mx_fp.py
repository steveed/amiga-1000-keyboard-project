"""Generate the rev 2 keyswitch footprints: Cherry MX (and compatible) switches on the Amiga 1000
key positions.  Rev 1 is the Mitsumi replacement; rev 2 takes MX switches only.

    python3 tools/gen_mx_fp.py

Origin is the keycap centre.  Switches stand in the standard orientation: pins north, LED holes
south.  PCB-mount pegs and the centre hole are drilled for every key.

Wide keys add MX PCB-mount stabiliser holes (Cherry spacing: 23.876 mm for 2U-2.75U, 114.3 mm for
the space bar, which uses a 7U stabiliser).  Return (the US inverted L, or the international one) has
a vertical 2U stabiliser, as on Henryk Richter's US Return for the A500KB; its origin is the stem, at
the centre of the column the cap has on both rows.
"""

import os
import uuid

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, 'pcb/lib_fp.pretty')
NS = uuid.UUID('0b5e9b1e-4f7a-4c1e-9d3e-a1000f00f003')
U = 19.05

MX = [('1', -3.81, -2.54), ('2', 2.54, -5.08)]     # standard MX pins
MX_PAD, MX_DRILL = 2.25, 1.5
MX_CENTRE, MX_PEG = 3.988, 1.75                    # PCB-mount pegs at +-5.08
STAB_SMALL, STAB_LARGE = 3.048, 3.988              # at -6.985 and +8.255 from the stem line

# name: (keycap width in U, stabiliser half-spacing in mm or None)
KEYS = {
    '1U': (1, None), '1.25U': (1.25, None), '1.75U': (1.75, None), '2U': (2, 11.938), '7.5U': (7.5, 57.15),
}

# The left Shift cluster: SW87 (US 2.5U Shift) and SW92 (ISO 1.5U Shift) are alternatives under the
# same keycaps.  Their facing pegs would be 0.54 mm apart, so SW87 has no west peg and SW92's east peg
# is a slot that takes either switch's peg.
LSHIFT_GAP = 9.62          # SW92 centre to SW87 centre, from rev 1
SPECIAL = {
    'LShift': dict(width=2.5, stab=11.938, pegs=[(5.08, 0)],
                   note='US left Shift (SW87); its west peg goes in the slot in SW92'),
    'LShift_ISO': dict(width=1.5, pegs=[(-5.08, 0)],
                       slot=((5.08 + LSHIFT_GAP - 5.08) / 2, 5.08 - (LSHIFT_GAP - 5.08)),
                       note='ISO short left Shift (SW92); east peg is a slot shared with SW87'),
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


def pad(name, num, x, y, size, drill, shape='circle'):
    kind = 'np_thru_hole' if num == '' else 'thru_hole'
    return (f'\t(pad "{num}" {kind} {shape} (at {n(x)} {n(y)}) (size {n(size)} {n(size)}) (drill {n(drill)}) '
            f'(layers "*.Cu" "*.Mask") (remove_unused_layers no) (uuid "{u(name, "pad", num, x, y)}"))')


def text(name, kind, value, y, layer):
    return (f'\t(property "{kind}" "{value}" (at 0 {n(y)} 0) (layer "{layer}") (uuid "{u(name, kind)}") '
            f'(effects (font (size 1 1) (thickness 0.15))))')


def footprint(name, descr, body):
    head = [f'(footprint "{name}" (version 20260206) (generator "pcbnew") (generator_version "10.0") (layer "F.Cu")',
            f'\t(descr "{descr}")', '\t(tags "keyswitch Cherry MX Amiga 1000")']
    return '\n'.join(head + body + ['\t(attr through_hole)', ')']) + '\n'


def body_outline(name):
    out = rect(name, -7, -7, 7, 7, 'F.Fab', 0.1)                         # 14 mm switch body / plate cutout
    out += rect(name, -7.5, -7.5, 7.5, 7.5, 'F.CrtYd', 0.05)
    out += [line(name, x, -7.2, x, 7.2, 'F.SilkS', 0.12) for x in (-7.2, 7.2)]
    out += [line(name, -7.2, y, 7.2, y, 'F.SilkS', 0.12) for y in (-7.2, 7.2)]
    return out


def switch(name, width, stab, pegs=((-5.08, 0), (5.08, 0)), slot=None, note=None):
    body = [text(name, 'Reference', 'REF**', -11.5, 'F.SilkS'), text(name, 'Value', name, 11.5, 'F.Fab')]
    body += rect(name, -width * U / 2, -U / 2, width * U / 2, U / 2, 'Dwgs.User', 0.1)    # keycap
    body += body_outline(name)
    for num, x, y in MX:
        body.append(pad(name, num, x, y, MX_PAD, MX_DRILL))
    body.append(pad(name, '', 0, 0, MX_CENTRE, MX_CENTRE))
    for x, y in pegs:
        body.append(pad(name, '', x, y, MX_PEG, MX_PEG))
    if slot:                                       # (centre x, extra length): an oval peg hole
        cx, extra = slot
        body.append(f'\t(pad "" np_thru_hole oval (at {n(cx)} 0) (size {n(MX_PEG + extra)} {n(MX_PEG)}) '
                    f'(drill oval {n(MX_PEG + extra)} {n(MX_PEG)}) (layers "*.Cu" "*.Mask") (remove_unused_layers no) '
                    f'(uuid "{u(name, "slot")}"))')
    if stab:
        for x in (-stab, stab):
            body.append(pad(name, '', x, -6.985, STAB_SMALL, STAB_SMALL))
            body.append(pad(name, '', x, 8.255, STAB_LARGE, STAB_LARGE))
            body += rect(name, x - 3.4, -8.6, x + 3.4, 10.3, 'F.CrtYd', 0.05)
    descr = (f'{width}U key, Cherry MX, Amiga 1000' + (f'; PCB-mount stabiliser at +-{stab} mm' if stab else '')
             + (f'. {note}' if note else ''))
    return footprint(name, descr, body)


def return_key():
    name = 'MX_A1000_Return'
    body = [text(name, 'Reference', 'REF**', -22.0, 'F.SilkS'), text(name, 'Value', name, 22.0, 'F.Fab')]
    body += rect(name, -1.25 * U / 2, -U, 1.25 * U / 2, U, 'Dwgs.User', 0.1)   # the column both rows share
    body += body_outline(name)
    for num, x, y in MX:
        body.append(pad(name, num, x, y, MX_PAD, MX_DRILL))
    body.append(pad(name, '', 0, 0, MX_CENTRE, MX_CENTRE))
    for x in (-5.08, 5.08):
        body.append(pad(name, '', x, 0, MX_PEG, MX_PEG))
    for y in (-11.938, 11.938):                    # vertical 2U stabiliser, as on Henryk's US Return
        body.append(pad(name, '', -6.985, y, STAB_SMALL, STAB_SMALL))
        body.append(pad(name, '', 8.255, y, STAB_LARGE, STAB_LARGE))
        body += rect(name, -8.6, y - 3.4, 10.3, y + 3.4, 'F.CrtYd', 0.05)
    return footprint(name, 'Return key (US inverted L or international), Cherry MX, Amiga 1000. Origin is the '
                     'stem; vertical 2U stabiliser', body)


def mx_led():
    name = 'MX_A1000_LED'
    body = [text(name, 'Reference', 'REF**', -2.2, 'F.SilkS'), text(name, 'Value', name, 2.2, 'F.Fab')]
    body.append(pad(name, '1', -1.27, 0, 1.6, 0.9, shape='rect'))
    body.append(pad(name, '2', 1.27, 0, 1.6, 0.9))
    body += rect(name, -2.3, -1.1, 2.3, 1.1, 'F.CrtYd', 0.05)
    return footprint(name, '3 mm LED through a Cherry MX switch (Caps Lock), placed 5.08 mm south of the key centre: '
                     'cathode pad 1 (square) west, anode pad 2 east', body)


def main():
    files = {}
    for k, (w, stab) in KEYS.items():
        files[f'MX_A1000_{k}'] = switch(f'MX_A1000_{k}', w, stab)
    for k, opt in SPECIAL.items():
        opt = dict(opt)
        w, stab = opt.pop('width'), opt.pop('stab', None)
        files[f'MX_A1000_{k}'] = switch(f'MX_A1000_{k}', w, stab, **opt)
    files['MX_A1000_Return'] = return_key()
    files['MX_A1000_LED'] = mx_led()
    for name, text_ in files.items():
        with open(os.path.join(OUT, name + '.kicad_mod'), 'w') as f:
            f.write(text_)
    print(f'wrote {len(files)} footprints to {os.path.relpath(OUT, REPO)}')


if __name__ == '__main__':
    main()

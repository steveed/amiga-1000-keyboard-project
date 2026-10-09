"""Turn KiCad's BOM and position exports into JLCPCB's assembly files.

    python3 tools/jlc_export.py <bom.csv> <pos.csv> <out dir>   (make rev2-jlc runs it)

<bom.csv> is `kicad-cli sch export bom` with the fields Reference, Value, Footprint, LCSC, DNP;
<pos.csv> is `kicad-cli pcb export pos --format csv --units mm --side both`.  Only parts with an LCSC
number and no DNP mark go to JLC: the switches, the Caps Lock LED, the ISP header and the jumper and
test pads are fitted by hand or not at all.

Writes <out>/bom-jlc.csv (Comment, Designator, Footprint, LCSC Part #) and <out>/cpl-jlc.csv
(Designator, Mid X, Mid Y, Layer, Rotation).  JLC's part models don't always share KiCad's zero
rotation; ROTATION holds the corrections known for the footprints on this board.  Check JLC's
placement preview before ordering all the same.
"""

import csv
import os
import re
import sys
from collections import OrderedDict

# footprint name pattern -> degrees added to KiCad's rotation for JLC
ROTATION = [
    (r'^SOT-23', 180),          # SOT-23-6 (USBLC6-2SC6)
    (r'^TQFP-', 270),           # ATmega32U4
]


def natural(ref):
    m = re.fullmatch(r'([A-Z]+)(\d+)', ref)
    return (m.group(1), int(m.group(2))) if m else (ref, 0)


def main():
    bom_in, pos_in, out = sys.argv[1:4]
    os.makedirs(out, exist_ok=True)

    parts = {}
    for row in csv.DictReader(open(bom_in)):
        refs = [r.strip() for r in row['Reference'].split(',')]
        for ref in refs:
            parts[ref] = row
    fitted = {ref: row for ref, row in parts.items()
              if row.get('LCSC', '').strip() and not row.get('DNP', '').strip()}

    groups = OrderedDict()
    for ref in sorted(fitted, key=natural):
        row = fitted[ref]
        fp = row['Footprint'].split(':')[-1]
        groups.setdefault((row['Value'], fp, row['LCSC'].strip()), []).append(ref)
    with open(os.path.join(out, 'bom-jlc.csv'), 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['Comment', 'Designator', 'Footprint', 'LCSC Part #'])
        for (value, fp, lcsc), refs in groups.items():
            w.writerow([value, ','.join(refs), fp, lcsc])

    placed = 0
    with open(os.path.join(out, 'cpl-jlc.csv'), 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation'])
        for row in sorted(csv.DictReader(open(pos_in)), key=lambda r: natural(r['Ref'])):
            if row['Ref'] not in fitted:
                continue
            rot = float(row['Rot'])
            for pat, add in ROTATION:
                if re.search(pat, row['Package']):
                    rot += add
                    break
            layer = 'Top' if row['Side'].lower() == 'top' else 'Bottom'
            w.writerow([row['Ref'], f"{float(row['PosX']):.3f}mm", f"{float(row['PosY']):.3f}mm", layer,
                        f'{rot % 360:g}'])
            placed += 1

    missing = sorted(set(fitted) - {r['Ref'] for r in csv.DictReader(open(pos_in))}, key=natural)
    print(f'{len(fitted)} parts in {len(groups)} BOM lines, {placed} placed')
    if missing:
        sys.exit(f'not on the board: {" ".join(missing)}')


if __name__ == '__main__':
    main()

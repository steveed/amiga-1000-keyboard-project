"""Generate the rev 2 schematic (ATmega32U4, SMD, Amiga and USB both live).

    python3 tools/gen_rev2_sch.py      (in the kicad container: it reads the stock symbol libraries)

The switches keep rev 1's references and key names, read from the rev 1 schematic, and rev 1's
positions decide the matrix: each physical row's first 12 keys (left to right) take electrical
rows 0-5, and what is left over fills rows 6 and 7.  Every key has its own diode.

Connections are drawn as a short wire stub and a net label on every pin, so the sheet reads as a
netlist.  UUIDs are derived from names, so regenerating gives the same file.
"""

import os
import re
import sys
import uuid

sys.path.insert(0, os.path.dirname(__file__))
from kisexp import Sym, parse, dump, find, find_all  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STOCK = '/usr/share/kicad/symbols'
LOCAL_LIB = os.path.join(REPO, 'pcb/lib_sch/amiga1000.kicad_sym')
REV1_SCH = os.path.join(REPO, 'pcb/amiga-1000-keyboard.kicad_sch')
REV1_PCB = os.path.join(REPO, 'pcb/amiga-1000-keyboard.kicad_pcb')
PROJECT = 'amiga-1000-keyboard-rev2'
OUT = os.path.join(REPO, f'pcb/rev_2/{PROJECT}.kicad_sch')

NS = uuid.UUID('6f1d8a52-3c1e-4c55-9a59-a1000c0de002')
ROOT_UUID = str(uuid.uuid5(NS, 'root'))


def uid(*parts):
    return str(uuid.uuid5(NS, '/'.join(map(str, parts))))


# ------------------------------------------------------------------ pin map

ROWS = ['PF0', 'PF1', 'PF4', 'PF5', 'PF6', 'PF7', 'PC6', 'PD7']       # driven low one at a time
COLS = ['PB0', 'PB1', 'PB2', 'PB3', 'PB4', 'PB5', 'PB6',              # inputs with pull-ups
        'PD0', 'PD1', 'PD4', 'PD5', 'PD6']
MCU_NETS = {
    'PD2': 'KCLK',            # INT2 / RXD1: Henryk's debug UART also lives on clock and data
    'PD3': 'KDAT',            # INT3 / TXD1
    'PB7': 'CAPS_LED',        # OC1C, can dim the LED
    'PE6': 'AMIGA_PWR',       # TPS2116 ST: high while the Amiga's 5 V is the supply in use
    '~{HWB}/PE2': 'HWB',      # held low at reset -> USB bootloader
    'PC7': 'SPARE',           # brought out to a test pad
    '~{RESET}': 'RESET',
    'XTAL1': 'XTAL1', 'XTAL2': 'XTAL2',
    'D+': 'USB_DP_MCU', 'D-': 'USB_DN_MCU',
    'VBUS': 'VBUS', 'UCAP': 'UCAP', 'AREF': 'AREF',
    'VCC': '+5V', 'AVCC': '+5V', 'UVCC': '+5V',
    'GND': 'GND', 'UGND': 'GND',
}
for i, p in enumerate(ROWS):
    MCU_NETS[p] = f'ROW{i}'
for i, p in enumerate(COLS):
    MCU_NETS[p] = f'COL{i}'


# ------------------------------------------------------------------ libraries

_libs = {}


def lib_symbol(lib_id):
    """The library symbol for lib_id, flattened (no `extends`), renamed to the full lib_id."""
    lib, name = lib_id.split(':')
    if lib not in _libs:
        path = LOCAL_LIB if lib == 'amiga1000' else f'{STOCK}/{lib}.kicad_sym'
        _libs[lib] = {s[1]: s for s in find_all(parse(open(path).read()), 'symbol')}
    syms = _libs[lib]
    sym = syms[name]
    ext = find(sym, 'extends')
    if ext:
        parent = lib_symbol(f'{lib}:{ext[1]}')
        own = {p[1]: p for p in find_all(sym, 'property')}
        body = []
        for x in parent[2:]:
            if isinstance(x, list) and x[0] == 'property' and x[1] in own:
                body.append(own.pop(x[1]))
            elif isinstance(x, list) and x[0] == 'symbol':
                body.append([x[0], x[1].replace(ext[1], name, 1)] + x[2:])
            else:
                body.append(x)
        body += list(own.values())
        sym = [Sym('symbol'), name] + body
    out = [sym[0], lib_id] + sym[2:]
    return out


def pins_of(sym):
    """[(number, name, x, y, angle)] in library coordinates (y up)."""
    out = []

    def walk(n):
        for x in n:
            if isinstance(x, list) and x:
                if x[0] == 'pin':
                    at = find(x, 'at')
                    out.append((str(find(x, 'number')[1]), str(find(x, 'name')[1]), at[1], at[2], at[3]))
                elif x[0] == 'symbol':
                    walk(x)
    walk(sym)
    return out


# ------------------------------------------------------------------ sheet items

items = []          # placed symbols, wires, labels, no-connects
used_libs = {}
_pwr_count = [0]


def g(v):
    """Snap to the 1.27 mm grid KiCad connects on."""
    return round(round(v / 1.27) * 1.27, 4)


def prop(name, value, x, y, hide=False, justify=None, angle=0):
    p = [Sym('property'), name, value, [Sym('at'), x, y, angle]]
    if hide:
        p.append([Sym('hide'), Sym('yes')])
    eff = [Sym('effects'), [Sym('font'), [Sym('size'), 1.27, 1.27]]]
    if justify:
        eff.append([Sym('justify')] + [Sym(j) for j in justify.split()])
    p.append(eff)
    return p


def wire(x1, y1, x2, y2):
    items.append([Sym('wire'), [Sym('pts'), [Sym('xy'), x1, y1], [Sym('xy'), x2, y2]],
                  [Sym('stroke'), [Sym('width'), 0], [Sym('type'), Sym('default')]],
                  [Sym('uuid'), uid('wire', x1, y1, x2, y2)]])


def label(net, x, y, outward):
    angle, just = {(-1, 0): (180, 'right bottom'), (1, 0): (0, 'left bottom'),
                   (0, -1): (90, 'left bottom'), (0, 1): (270, 'right bottom')}[outward]
    items.append([Sym('label'), net, [Sym('at'), x, y, angle],
                  [Sym('effects'), [Sym('font'), [Sym('size'), 1.27, 1.27]], [Sym('justify')] + [Sym(j) for j in just.split()]],
                  [Sym('uuid'), uid('label', net, x, y)]])


def no_connect(x, y):
    items.append([Sym('no_connect'), [Sym('at'), x, y], [Sym('uuid'), uid('nc', x, y)]])


def place(lib_id, ref, value, x, y, nets, footprint='', part='', dnp=False, in_bom=True, desc='',
          stub=2.54, power=False):
    """Place a symbol at (x, y) and hang a stub + label on each pin.

    nets maps pin number (or pin name) -> net name, None for a no-connect, or '' to leave the pin
    bare (used where a pin is wired by hand).  Pins stacked at one point share one stub."""
    sym = lib_symbol(lib_id)
    used_libs[lib_id] = sym
    x, y = g(x), g(y)
    pins = pins_of(sym)
    s = [Sym('symbol'), [Sym('lib_id'), lib_id], [Sym('at'), x, y, 0], [Sym('unit'), 1],
         [Sym('exclude_from_sim'), Sym('no')], [Sym('in_bom'), Sym('yes' if in_bom else 'no')],
         [Sym('on_board'), Sym('yes')], [Sym('dnp'), Sym('yes' if dnp else 'no')],
         [Sym('uuid'), uid('sym', ref)]]
    if pins and all(int(p[4]) % 180 == 90 for p in pins):
        # pins only top and bottom (R, C, holes, power symbols): their stubs and labels run up
        # and down, so the text goes beside the body
        s.append(prop('Reference', ref, g(x + 2.54), g(y - 1.27), hide=power, justify='left'))
        s.append(prop('Value', value, g(x + 2.54), g(y + 1.27), justify='left'))
    else:
        ys = [-p[3] for p in pins] or [0]
        s.append(prop('Reference', ref, x, g(y + min(ys) - 2.54), hide=power))
        s.append(prop('Value', value, x, g(y + max(ys) + 2.54)))
    s.append(prop('Footprint', footprint, x, y, hide=True))
    s.append(prop('Datasheet', '', x, y, hide=True))
    s.append(prop('Description', desc, x, y, hide=True))
    if part:
        s.append(prop('Part', part, x, y, hide=True))
    for num, *_ in pins:
        s.append([Sym('pin'), num, [Sym('uuid'), uid('pin', ref, num)]])
    s.append([Sym('instances'), [Sym('project'), PROJECT, [Sym('path'), '/' + ROOT_UUID,
                                                          [Sym('reference'), ref], [Sym('unit'), 1]]]])
    items.append(s)

    done = {}
    for num, name, px, py, pa in pins:
        net = nets.get(num, nets.get(name, '__missing__'))
        if net == '__missing__':
            raise SystemExit(f'{ref}: pin {num} ({name}) has no net')
        sx, sy = g(x + px), g(y - py)
        if (sx, sy) in done:
            if done[(sx, sy)] != net:
                raise SystemExit(f'{ref}: stacked pins at {sx},{sy} on {done[(sx, sy)]} and {net}')
            continue
        done[(sx, sy)] = net
        if net == '':
            continue
        if net is None:
            no_connect(sx, sy)
            continue
        # the pin points from its end into the body; the stub goes the other way
        d = {0: (-1, 0), 90: (0, 1), 180: (1, 0), 270: (0, -1)}[int(pa) % 360]
        ex, ey = g(sx + d[0] * stub), g(sy + d[1] * stub)
        wire(sx, sy, ex, ey)
        label(net, ex, ey, d)
    return {num: (g(x + px), g(y - py)) for num, name, px, py, pa in pins}


def power_symbol(lib_id, net, x, y):
    """A power or PWR_FLAG symbol on its own stub, labelled onto `net`."""
    _pwr_count[0] += 1
    ref = f'#{"FLG" if "FLAG" in lib_id else "PWR"}{_pwr_count[0]:02d}'
    pins = place(lib_id, ref, net if 'FLAG' not in lib_id else 'PWR_FLAG', x, y, {'1': ''},
                 in_bom=False, power=True)
    px, py = pins['1']
    wire(px, py, px, g(py + 2.54) if lib_id != 'power:GND' else g(py - 2.54))
    label(net, px, g(py + 2.54) if lib_id != 'power:GND' else g(py - 2.54),
          (0, 1) if lib_id != 'power:GND' else (0, -1))


def text(t, x, y, size=2.54):
    items.append([Sym('text'), t, [Sym('exclude_from_sim'), Sym('no')], [Sym('at'), g(x), g(y), 0],
                  [Sym('effects'), [Sym('font'), [Sym('size'), size, size]], [Sym('justify'), Sym('left'), Sym('bottom')]],
                  [Sym('uuid'), uid('text', t)]])


# ------------------------------------------------------------------ parts

R0402, C0402, C0603 = 'Resistor_SMD:R_0402_1005Metric', 'Capacitor_SMD:C_0402_1005Metric', 'Capacitor_SMD:C_0603_1608Metric'


def R(ref, value, x, y, a, b, part=None):
    place('Device:R', ref, value, x, y, {'1': a, '2': b}, R0402, part or f'{value} 1% 0402')


def C(ref, value, x, y, a, b, fp=C0402, part=None, dnp=False):
    place('Device:C', ref, value, x, y, {'1': a, '2': b}, fp, part or f'{value} 0402', dnp=dnp)


def build():
    # --- controller
    text('Controller: ATmega32U4, 16 MHz.', 30.48, 33.02)
    place('MCU_Microchip_ATmega:ATmega32U4-A', 'U1', 'ATmega32U4-AU', 101.6, 147.32, MCU_NETS,
          'Package_QFP:TQFP-44_10x10mm_P0.8mm', 'ATMEGA32U4-AU, TQFP-44',
          desc='Keyboard controller; firmware ported from A500KB')
    place('Device:Crystal_GND24', 'Y1', '16MHz', 60.96, 233.68,
          {'1': 'XTAL1', '3': 'XTAL2', '2': 'GND', '4': 'GND'},
          'Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm', '16 MHz crystal, 3225, CL 20 pF')
    C('C1', '22pF', 45.72, 254.0, 'XTAL1', 'GND', part='22 pF C0G 0402')
    C('C2', '22pF', 76.2, 254.0, 'XTAL2', 'GND', part='22 pF C0G 0402')
    C('C3', '100nF', 175.26, 63.5, '+5V', 'GND', part='100 nF X7R 0402')
    C('C4', '100nF', 195.58, 63.5, '+5V', 'GND', part='100 nF X7R 0402')
    C('C5', '100nF', 215.9, 63.5, '+5V', 'GND', part='100 nF X7R 0402')
    C('C6', '100nF', 236.22, 63.5, '+5V', 'GND', part='100 nF X7R 0402')
    C('C7', '10uF', 256.54, 63.5, '+5V', 'GND', C0603, '10 uF X5R 10 V 0603')
    C('C8', '1uF', 175.26, 93.98, 'UCAP', 'GND', part='1 uF X5R 0402')
    C('C9', '100nF', 195.58, 93.98, 'AREF', 'GND', part='100 nF X7R 0402')
    # reset and bootloader
    R('R1', '10k', 175.26, 127.0, '+5V', 'RESET')
    place('Switch:SW_Push', 'SW93', 'RESET', 203.2, 134.62, {'1': 'RESET', '2': 'GND'},
          'Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A', 'XKB TS-1187A tactile switch')
    R('R2', '10k', 175.26, 157.48, '+5V', 'HWB')
    place('Switch:SW_Push', 'SW94', 'BOOT', 203.2, 165.1, {'1': 'HWB', '2': 'GND'},
          'Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A', 'XKB TS-1187A tactile switch',
          desc='Hold while pressing RESET to enter the USB (DFU) bootloader')
    place('Connector_Generic:Conn_02x03_Odd_Even', 'J3', 'ISP', 180.34, 200.66,
          {'1': 'COL3', '2': '+5V', '3': 'COL1', '4': 'COL2', '5': 'RESET', '6': 'GND'},
          'Connector_PinHeader_2.54mm:PinHeader_2x03_P2.54mm_Vertical', 'AVR ISP header (recovery only)',
          dnp=True, desc='MISO/PB3, SCK/PB1 and MOSI/PB2 are shared with matrix columns 3, 1 and 2')
    place('Connector:TestPoint', 'TP1', 'SPARE (PC7)', 233.68, 200.66, {'1': 'SPARE'},
          'TestPoint:TestPoint_Pad_D1.5mm', 'test pad', in_bom=False)
    # Caps Lock LED, a 3 mm LED through the Caps Lock switch
    R('R3', '330', 175.26, 233.68, 'CAPS_LED', 'CAPS_LED_A')
    place('Device:LED', 'D92', 'CAPS LOCK', 203.2, 243.84, {'1': 'GND', '2': 'CAPS_LED_A'},
          'amiga1000:MX_A1000_LED', '3 mm LED through a Cherry MX switch', in_bom=False,
          desc='Fitted by hand with the Caps Lock switch')

    # --- power: Amiga 5 V has priority, USB takes over when it is absent
    text('Power: the Amiga 5 V (VIN1) has priority; USB VBUS (VIN2) takes over below about 4.3 V.', 330.2, 33.02)
    place('amiga1000:TPS2116', 'U2', 'TPS2116DRLR', 424.18, 73.66,
          {'3': 'VCC_AMIGA', '6': 'VBUS', '4': 'PR1', '5': 'VCC_AMIGA', '2': '+5V', '7': '+5V',
           '8': 'AMIGA_PWR', '1': 'GND'}, 'Package_TO_SOT_SMD:SOT-583-8', 'TPS2116DRLR power mux')
    R('R4', '33k', 350.52, 101.6, 'VCC_AMIGA', 'PR1')
    R('R5', '10k', 370.84, 101.6, 'PR1', 'GND')
    R('R6', '10k', 474.98, 101.6, '+5V', 'AMIGA_PWR')
    C('C10', '1uF', 350.52, 60.96, 'VCC_AMIGA', 'GND', part='1 uF X5R 10 V 0402')
    C('C11', '1uF', 370.84, 60.96, 'VBUS', 'GND', part='1 uF X5R 10 V 0402')
    C('C12', '10uF', 495.3, 60.96, '+5V', 'GND', C0603, '10 uF X5R 10 V 0603')

    # --- USB
    text('USB-C (USB 2.0 device): ESD protection, 500 mA fuse, 22R series resistors.', 330.2, 139.7)
    place('Connector:USB_C_Receptacle_USB2.0_16P', 'J2', 'USB-C', 360.68, 190.5,
          {'A4': 'VBUS_IN', 'A9': 'VBUS_IN', 'B4': 'VBUS_IN', 'B9': 'VBUS_IN',
           'A5': 'CC1', 'B5': 'CC2', 'A6': 'USB_DP', 'B6': 'USB_DP', 'A7': 'USB_DN', 'B7': 'USB_DN',
           'A8': None, 'B8': None, 'A1': 'GND', 'A12': 'GND', 'B1': 'GND', 'B12': 'GND', 'SH': 'GND'},
          'Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12', 'HRO TYPE-C-31-M-12 USB-C receptacle')
    R('R7', '5.1k', 416.56, 213.36, 'CC1', 'GND')
    R('R8', '5.1k', 436.88, 213.36, 'CC2', 'GND')
    place('Device:Polyfuse', 'F1', '500mA', 416.56, 165.1, {'1': 'VBUS_IN', '2': 'VBUS'},
          'Fuse:Fuse_1206_3216Metric', '500 mA hold PTC fuse, 1206')
    place('Power_Protection:USBLC6-2SC6', 'U3', 'USBLC6-2SC6', 467.36, 187.96,
          {'1': 'USB_DP', '6': 'USB_DP', '3': 'USB_DN', '4': 'USB_DN', '5': 'VBUS', '2': 'GND'},
          'Package_TO_SOT_SMD:SOT-23-6', 'USBLC6-2SC6 USB ESD protection')
    R('R9', '22', 502.92, 182.88, 'USB_DP', 'USB_DP_MCU')
    R('R10', '22', 523.24, 182.88, 'USB_DN', 'USB_DN_MCU')

    # --- Amiga cable (same pin order as rev 1's J1, so the jack pigtail carries over)
    text('Amiga keyboard cable to the 4P4C jack.  KCLK and KDAT are open drain: the firmware only pulls them low.', 571.5, 33.02)
    place('Connector_Generic:Conn_01x04', 'J1', 'AMIGA', 586.74, 78.74,
          {'1': 'GND', '2': 'VCC_EXT', '3': 'KCLK_EXT', '4': 'KDAT_EXT'},
          'Connector_JST:JST_PH_S4B-PH-SM4-TB_1x04-1MP_P2.00mm_Horizontal', 'JST PH 4-pin SMD right angle',
          desc='1 GND (black), 2 +5V (red), 3 KCLK (white), 4 KDAT (green)')
    for ref, a, b, x in (('FB1', 'VCC_EXT', 'VCC_AMIGA', 624.84), ('FB2', 'KCLK_EXT', 'KCLK', 645.16),
                         ('FB3', 'KDAT_EXT', 'KDAT', 665.48)):
        place('Device:FerriteBead_Small', ref, 'FB', x, 81.28, {'1': a, '2': b},
              'Inductor_SMD:L_0603_1608Metric', 'Ferrite bead 600R@100MHz 0603')
    for ref, net, x in (('C13', 'VCC_EXT', 695.96), ('C14', 'KCLK_EXT', 716.28), ('C15', 'KDAT_EXT', 736.6)):
        C(ref, '1nF', x, 81.28, net, 'GND', part='1 nF X7R 0402', dnp=True)

    # --- power symbols and flags
    power_symbol('power:+5V', '+5V', 581.66, 251.46)
    power_symbol('power:GND', 'GND', 601.98, 261.62)
    power_symbol('power:PWR_FLAG', 'GND', 627.38, 251.46)
    power_symbol('power:PWR_FLAG', 'VCC_AMIGA', 652.78, 251.46)
    power_symbol('power:PWR_FLAG', 'VBUS', 678.18, 251.46)

    # --- mounting holes
    text('Mounting holes: H1-H9 screw the plate down and ground it; H10-H12 clear the case screws.', 571.5, 139.7)
    for i in range(9):
        place('Mechanical:MountingHole_Pad', f'H{i + 1}', 'Plate GND', 581.66 + 25.4 * (i % 5), 157.48 + 22.86 * (i // 5),
              {'1': 'GND'}, 'amiga1000:MountingHole_3.8mm_Plate_GND', in_bom=False)
    for i in range(3):
        place('Mechanical:MountingHole', f'H{i + 10}', 'Case screw', 581.66 + 25.4 * i, 203.2,
              {}, 'amiga1000:MountingHole_7.5mm_CaseClearance', in_bom=False)

    matrix()


# ------------------------------------------------------------------ matrix

def rev1_keys():
    """[(ref, name, x, y)] for rev 1's switches: x from the PCB's left edge, y up from its front edge."""
    sch = open(REV1_SCH).read()
    names = dict(re.findall(r'\(property "Reference" "(SW\d+)".*?\(property "Value" "([^"]+)"', sch, re.S))
    pcb = open(REV1_PCB).read()
    keys = []
    for m in re.finditer(r'\(footprint "amiga1000:Mitsumi_A1000_Switch".*?\n\t\t\(at ([-\d.]+) ([-\d.]+)[^)]*\)'
                         r'.*?\(property "Reference" "(SW\d+)"', pcb, re.S):
        x, y, ref = m.groups()
        keys.append((ref, names[ref], float(x) - 14.9 - 4.75, 185.15 - float(y)))
    return keys


def matrix_map():
    keys = [k for k in rev1_keys() if k[0] != 'SW92']          # SW92 shares SW87's position
    keys.sort(key=lambda k: (-k[3], k[2]))
    phys = []
    for k in keys:
        if phys and abs(phys[-1][0][3] - k[3]) < 6:
            phys[-1].append(k)
        else:
            phys.append([k])
    assert len(phys) == 6, [len(r) for r in phys]
    cells, rest = {}, []
    for r, row in enumerate(phys):
        row.sort(key=lambda k: k[2])
        for c, k in enumerate(row[:12]):
            cells[k[0]] = (r, c)
        rest += row[12:]
    for i, k in enumerate(rest):
        cells[k[0]] = (6 + i // 12, i % 12)
    assert len(set(cells.values())) == len(cells) == 91
    return cells, {k[0]: k[1] for k in rev1_keys()}


# Keycap widths, from rev 1's switch spacing (the rest are 1U).  RETURN has its own footprint.
WIDTHS = {**{f'F{i}': '1.25U' for i in range(1, 11)}, '`': '1.25U', 'L ALT': '1.25U', 'L AMIGA': '1.25U',
          'R AMIGA': '1.25U', 'R ALT': '1.25U', 'TAB': '1.75U', 'BACKSPACE': '1.75U',
          'R SHIFT': '2U', 'KP 0': '2U', 'KP ENTER': '2U', 'SPACE': '7.5U',
          # SW87 and SW92 share a peg slot (see tools/gen_mx_fp.py)
          'L SHIFT': 'LShift', 'L SHIFT ISO': 'LShift_ISO'}


def switch_fp(name):
    if name == 'RETURN':
        return 'amiga1000:MX_A1000_Return'
    return f'amiga1000:MX_A1000_{WIDTHS.get(name, "1U")}'


SWITCH_PART = 'Cherry MX (or compatible) keyswitch'


def matrix():
    cells, names = matrix_map()
    x0, y0, dx, dy = 76.2, 309.88, 58.42, 33.02
    text('Key matrix, 8 rows x 12 columns, rows driven low one at a time: COLn - switch - diode (anode) - (cathode) ROWn.  '
         'SW92 (short ISO left shift) is fitted instead of SW87 and shares its position.', x0, y0 - 15.24)
    for r in range(8):
        text(f'ROW{r} = {ROWS[r]}', x0 - 45.72, y0 + r * dy, 1.27)
    for c in range(12):
        text(f'COL{c} = {COLS[c]}', x0 + c * dx, y0 - 7.62, 1.27)
    for ref, (r, c) in sorted(cells.items(), key=lambda kv: kv[1]):
        n = int(ref[2:])
        x, y = x0 + c * dx, y0 + r * dy
        sw = place('Switch:SW_Push', ref, names[ref], x, y, {'1': f'COL{c}', '2': ''},
                   switch_fp(names[ref]), SWITCH_PART, in_bom=False, desc=f'Matrix row {r}, column {c}')
        d = place('Device:D', f'D{n}', '1N4148W', x + 17.78, y + 7.62, {'1': f'ROW{r}', '2': ''},
                  'Diode_SMD:D_SOD-123', '1N4148W SOD-123')
        (sx, sy), (ax, ay) = sw['2'], d['2']
        wire(sx, sy, ax, sy)
        wire(ax, sy, ax, ay)
        if ref == 'SW87':
            label('SW87_A', ax, sy, (0, -1))
    # SW92 beside the grid, on SW87's anode node
    sw = place('Switch:SW_Push', 'SW92', names['SW92'], x0 + 12 * dx, y0 + 4 * dy,
               {'1': f'COL{cells["SW87"][1]}', '2': 'SW87_A'}, switch_fp(names['SW92']),
               SWITCH_PART, in_bom=False, dnp=True,
               desc='Short ISO left shift position; fitted instead of SW87 (L SHIFT) on international layouts')
    return cells


# ------------------------------------------------------------------ output

def write():
    build()
    sch = [Sym('kicad_sch'), [Sym('version'), 20260306], [Sym('generator'), 'eeschema'],
           [Sym('generator_version'), '10.0'], [Sym('uuid'), ROOT_UUID], [Sym('paper'), 'A1'],
           [Sym('title_block'), [Sym('title'), 'Amiga 1000 Keyboard, rev 2'], [Sym('date'), '2026-10-08'],
            [Sym('rev'), '2'], [Sym('comment'), 1, 'ATmega32U4, surface mount, Cherry MX switches; Amiga and USB both live'],
            [Sym('comment'), 2, 'Generated by tools/gen_rev2_sch.py - edit the script, not this file'],
            [Sym('comment'), 3, 'License: CC BY-NC-SA 4.0']],
           [Sym('lib_symbols')] + [used_libs[k] for k in sorted(used_libs)]]
    sch += items
    sch += [[Sym('sheet_instances'), [Sym('path'), '/', [Sym('page'), '1']]],
            [Sym('embedded_fonts'), Sym('no')]]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w') as f:
        f.write(dump(sch) + '\n')
    print(f'wrote {os.path.relpath(OUT, REPO)}: {sum(1 for i in items if i[0] == "symbol")} symbols')


if __name__ == '__main__':
    write()

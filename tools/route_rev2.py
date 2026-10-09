"""Route the rev 2 board with KiCadRoutingTools (KRT), following tools/rev2_route.json.

    make rev2-route
    (= docker run --rm -v "$PWD":/repo krt:local python3 /repo/tools/route_rev2.py)

krt:local is built from a KiCadRoutingTools checkout; see pcb/rev_2/README.md.  The passes, their
nets, clearances and widths live in the JSON config, so nothing depends on shell quoting.

It routes a copy under KRT_WORK (default /tmp/route), because the router writes its design-rule
floor into the board's sibling .kicad_pro, and copies back only the routed .kicad_pcb.  The exit
status is 0 only if KRT's connectivity check finds every net connected.
"""

import json
import os
import re
import shutil
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(REPO, 'tools/rev2_route.json')
BOARD = 'amiga-1000-keyboard-rev2'
KRT = '/krt'
WORK = os.environ.get('KRT_WORK', '/tmp/route')


def expand(nets, groups):
    out = []
    for n in nets:
        out += groups[n[1:]] if n.startswith('@') else [n]
    return out


def flags(opts):
    args = []
    for k, v in opts.items():
        if k.startswith('_') or v is False or v is None:
            continue
        args.append('--' + k)
        if v is True:
            continue
        args += [str(x) for x in v] if isinstance(v, list) else [str(v)]
    return args


def route(cfg, name, src, dst, nets, clearance, power=None, exclude=(), extra=None, rip=False):
    board = os.path.join(WORK, 'rev_2')
    args = [sys.executable, 'py_router/route.py', f'{board}/{src}.kicad_pcb', f'{board}/{dst}.kicad_pcb',
            '--nets', *nets, *('!' + n for n in exclude), '--clearance', str(clearance)]
    if rip:
        args += ['--rip-existing-nets', *nets]
    if power:
        args += ['--power-nets', *power, '--power-nets-widths', *(str(w) for w in power.values())]
    args += flags(cfg['common']) + flags(extra or {})
    with open(os.path.join(WORK, name + '.log'), 'w') as log:
        subprocess.run(args, cwd=KRT, stdout=log, stderr=subprocess.STDOUT)
    text = open(os.path.join(WORK, name + '.log')).read()
    m = re.search(r'^JSON_SUMMARY_MIN: (\{.*\})$', text, re.M)
    still = json.loads(m.group(1)).get('pad_pairs_open', {}).get('nets', []) if m else ['(no summary)']
    print(f'{name}: open {still}' if still else f'{name}: done')
    return dst


def open_nets(board):
    r = subprocess.run([sys.executable, 'py_router/check_connected.py', board], cwd=KRT,
                       capture_output=True, text=True)
    with open(os.path.join(WORK, 'check.log'), 'w') as f:
        f.write(r.stdout + r.stderr)
    return [] if r.returncode == 0 else re.findall(r'^  (\S+) \(net \d+\):', r.stdout, re.M)


def main():
    cfg = json.load(open(CONFIG))
    groups = cfg['groups']
    shutil.rmtree(WORK, ignore_errors=True)
    os.makedirs(WORK)
    for d in ('rev_2', 'lib_fp.pretty', 'lib_sch'):
        shutil.copytree(os.path.join(REPO, 'pcb', d), os.path.join(WORK, d),
                        ignore=shutil.ignore_patterns('.history', '*-backups'))

    last = BOARD
    for i, p in enumerate(cfg['passes'], 1):
        last = route(cfg, p['name'], last, f'r{i}', expand(p['nets'], groups), p['clearance'],
                     p.get('power-nets'), expand(p.get('exclude', []), groups), p.get('options'))

    rep = cfg['repair']
    tight = set(expand(rep['tight']['nets'], groups))
    gnd = cfg['passes'][-1]
    for t in range(1, rep['tries'] + 1):
        nets = open_nets(os.path.join(WORK, 'rev_2', last + '.kicad_pcb'))
        if not nets:
            break
        print(f'repair {t}: {" ".join(nets)}')
        for kind, group, clr in (('tight', [n for n in nets if n in tight], rep['tight']['clearance']),
                                 ('loose', [n for n in nets if n not in tight], rep['loose_clearance'])):
            if group:
                last = route(cfg, f'repair{t}-{kind}', last, f'{kind}{t}', group, clr,
                             extra=rep.get('options'), rip=True)
        last = route(cfg, f'repair{t}-gnd', last, f'gnd{t}', gnd['nets'], gnd['clearance'], gnd.get('power-nets'))

    shutil.copyfile(os.path.join(WORK, 'rev_2', last + '.kicad_pcb'),
                    os.path.join(REPO, 'pcb/rev_2', BOARD + '.kicad_pcb'))
    print(f'routed: pcb/rev_2/{BOARD}.kicad_pcb')
    left = open_nets(os.path.join(WORK, 'rev_2', last + '.kicad_pcb'))
    if left:
        print(f'NOT fully connected: {" ".join(left)}  (details in {WORK}/check.log)')
        sys.exit(1)
    print('all nets connected')


if __name__ == '__main__':
    main()

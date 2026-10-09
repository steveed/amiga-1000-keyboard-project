"""Minimal KiCad s-expression reader and writer, enough to lift symbols out of the stock
libraries and write a schematic.  Lists are Python lists; atoms are Sym (bare words) or str
(quoted strings) or float/int.  Quoted strings are kept exactly as written, escapes and all
(KiCad's \\n is a newline), so reading and writing a file doesn't change its text."""

import re


class Sym(str):
    """A bare (unquoted) atom such as a keyword or `yes`."""


_TOKEN = re.compile(r'\s*(?:(\()|(\))|"((?:[^"\\]|\\.)*)"|([^\s()"]+))', re.S)


def parse(text):
    stack, cur = [], []
    pos = 0
    while True:
        m = _TOKEN.match(text, pos)
        if not m:
            break
        pos = m.end()
        lp, rp, qs, atom = m.groups()
        if lp:
            stack.append(cur)
            cur = []
        elif rp:
            done, cur = cur, stack.pop()
            cur.append(done)
        elif qs is not None:
            cur.append(qs)
        else:
            cur.append(_atom(atom))
    return cur[0]


def _atom(a):
    try:
        return int(a) if re.fullmatch(r'-?\d+', a) else float(a) if re.fullmatch(r'-?\d*\.\d+(e-?\d+)?', a) else Sym(a)
    except ValueError:
        return Sym(a)


def fmt_num(v):
    if isinstance(v, float):
        s = f'{v:.4f}'.rstrip('0').rstrip('.')
        return '0' if s in ('-0', '') else s
    return str(v)


def dump(node, indent=0):
    """KiCad-style layout: one child list per line, short atom runs kept on the head line."""
    if not isinstance(node, list):
        if isinstance(node, Sym):
            return str(node)
        if isinstance(node, (int, float)):
            return fmt_num(node)
        return '"' + str(node) + '"'
    head = [dump(x) for x in node if not isinstance(x, list)]
    kids = [x for x in node if isinstance(x, list)]
    # (xy ..) runs stay on one line, as KiCad writes them
    if kids and all(k and k[0] == 'xy' for k in kids):
        return '(' + ' '.join(head) + '\n' + '\t' * (indent + 1) + ' '.join(dump(k) for k in kids) + '\n' + '\t' * indent + ')'
    if not kids:
        return '(' + ' '.join(head) + ')'
    body = ''.join('\n' + '\t' * (indent + 1) + dump(k, indent + 1) for k in kids)
    return '(' + ' '.join(head) + body + '\n' + '\t' * indent + ')'


def find(node, key):
    """First child list whose head is `key`."""
    for x in node:
        if isinstance(x, list) and x and x[0] == key:
            return x
    return None


def find_all(node, key):
    return [x for x in node if isinstance(x, list) and x and x[0] == key]

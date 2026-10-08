#!/usr/bin/env python3
"""
lint.py — Regelprüfer für die Design Identity (Arslan Chaudhry).

Aufruf:
    python3 skills/design-identity/scripts/lint.py <datei.html> [...] [--json]

Prüft eine fertige HTML-Datei gegen die Regeln aus SKILL.md, assets/tokens.css
und references/tokens.md. Der Linter ergänzt evals/evals.json: die Evals prüfen
Marken-Oberfläche ("Papierton vorhanden, Radius 4px"), dieser Linter prüft die
Disziplin dahinter (Token statt Rohwert, Raster, Skala, Kontrast, Zeichensatz,
Zeichenkodierung).

Ausgabe ist nach Fehler / Warnung / Hinweis gruppiert, jeder Fund mit Zeilennummer
und zitierter Fundstelle. Exit-Code 1, sobald mindestens ein Fehler vorliegt.
`--json` liefert dieselben Funde maschinenlesbar auf stdout.

Abhängigkeiten: Standardbibliothek. Für die Zeichensatzprüfung zusätzlich
fontTools + brotli (`pip install fonttools brotli`); fehlen sie, wird genau diese
eine Prüfung übersprungen und als Hinweis gemeldet — der Rest läuft weiter.
"""

from __future__ import annotations

import argparse
import base64
import bisect
import colorsys
import html
import io
import json
import os
import re
import sys

# --------------------------------------------------------------------------
# Konstanten aus dem Regelwerk
# --------------------------------------------------------------------------

# Eine Stelle, an der die Version steht. Stand bis 1.2.3 dreimal im File und
# war dreimal verschieden — der Docstring auf 1.2.2, `--help` auf 1.1.0.
VERSION = "1.2.3"

# Typo-Skala, references/tokens.md — elf Stufen, keine Zwischenwerte.
TYPE_SCALE = {11: "--ac-text-micro", 12: "--ac-text-caption", 13: "--ac-text-small",
              14: "--ac-text-body", 16: "--ac-text-body-lg", 18: "--ac-text-subheading",
              20: "--ac-text-heading", 24: "--ac-text-heading-lg", 30: "--ac-text-title",
              38: "--ac-text-display", 48: "--ac-text-display-lg"}

# Raumskala auf dem 4px-Raster.
SPACE_SCALE = {0: None, 4: "--ac-space-1", 8: "--ac-space-2", 12: "--ac-space-3",
               16: "--ac-space-4", 20: "--ac-space-5", 24: "--ac-space-6",
               32: "--ac-space-8", 40: "--ac-space-10", 56: "--ac-space-14",
               72: "--ac-space-18"}

RADIUS_SCALE = {0: None, 2: "--ac-radius-sm", 4: "--ac-radius", 8: "--ac-radius-lg"}

LEADING_SCALE = {1.15: "--ac-leading-display", 1.26: "--ac-leading-heading",
                 1.45: "--ac-leading-mono", 1.5: "--ac-leading-ui",
                 1.75: "--ac-leading-prose"}

WEIGHT_SCALE = {400: "--ac-weight-regular", 500: "--ac-weight-medium",
                600: "--ac-weight-semibold"}

TRACKING_SCALE = {-0.022: "--ac-tracking-display", -0.015: "--ac-tracking-heading",
                  0.0: "--ac-tracking-normal", 0.05: "--ac-tracking-label"}

SPACING_PROPS = ("margin", "margin-top", "margin-right", "margin-bottom", "margin-left",
                 "margin-block", "margin-inline", "margin-block-start", "margin-block-end",
                 "margin-inline-start", "margin-inline-end",
                 "padding", "padding-top", "padding-right", "padding-bottom", "padding-left",
                 "padding-block", "padding-inline", "padding-block-start", "padding-block-end",
                 "padding-inline-start", "padding-inline-end",
                 "gap", "row-gap", "column-gap", "grid-gap", "grid-row-gap", "grid-column-gap")

COLOR_PROPS = ("color", "background", "background-color", "border-color", "border",
               "border-top", "border-right", "border-bottom", "border-left",
               "border-top-color", "border-right-color", "border-bottom-color",
               "border-left-color", "outline", "outline-color", "fill", "stroke",
               "stop-color", "caret-color", "text-decoration-color", "accent-color",
               "column-rule-color", "border-block-color", "border-inline-color")

# Nur die Namen, die in der Praxis als "schnell hingeschrieben" auftauchen.
NAMED_COLORS = {
    "white": (255, 255, 255), "black": (0, 0, 0), "red": (255, 0, 0),
    "green": (0, 128, 0), "blue": (0, 0, 255), "yellow": (255, 255, 0),
    "orange": (255, 165, 0), "purple": (128, 0, 128), "gray": (128, 128, 128),
    "grey": (128, 128, 128), "silver": (192, 192, 192), "lightgray": (211, 211, 211),
    "lightgrey": (211, 211, 211), "darkgray": (169, 169, 169), "darkgrey": (169, 169, 169),
    "whitesmoke": (245, 245, 245), "ghostwhite": (248, 248, 255), "ivory": (255, 255, 240),
    "snow": (255, 250, 250), "gainsboro": (220, 220, 220), "teal": (0, 128, 128),
    "navy": (0, 0, 128), "maroon": (128, 0, 0), "olive": (128, 128, 0),
    "lime": (0, 255, 0), "aqua": (0, 255, 255), "cyan": (0, 255, 255),
    "fuchsia": (255, 0, 255), "magenta": (255, 0, 255), "crimson": (220, 20, 60),
    "gold": (255, 215, 0), "beige": (245, 245, 220), "tan": (210, 180, 140),
}
COLOR_KEYWORDS_OK = {"transparent", "currentcolor", "inherit", "initial", "unset",
                     "revert", "none", "auto"}

SEVERITIES = ("fehler", "warnung", "hinweis")
SEVERITY_LABEL = {"fehler": "FEHLER", "warnung": "WARNUNG", "hinweis": "HINWEIS"}

# Wie viele Funde pro Prüfung in der Textausgabe stehen; --json liefert immer alle.
MAX_PER_CHECK_TEXT = 12


# --------------------------------------------------------------------------
# Grundgerüst: Funde, Zeilenzuordnung
# --------------------------------------------------------------------------

class Finding:
    __slots__ = ("severity", "check", "line", "message", "snippet", "hint")

    def __init__(self, severity, check, line, message, snippet="", hint=""):
        self.severity = severity
        self.check = check
        self.line = line
        self.message = message
        self.snippet = snippet
        self.hint = hint

    def as_dict(self):
        d = {"severity": self.severity, "check": self.check, "line": self.line,
             "message": self.message}
        if self.snippet:
            d["snippet"] = self.snippet
        if self.hint:
            d["hint"] = self.hint
        return d


class Report:
    def __init__(self):
        self.findings = []

    def add(self, severity, check, line, message, snippet="", hint=""):
        self.findings.append(Finding(severity, check, line, message, snippet, hint))

    def counts(self):
        c = {s: 0 for s in SEVERITIES}
        for f in self.findings:
            c[f.severity] += 1
        return c


def line_index(text):
    """Startoffsets aller Zeilen, für offset -> Zeilennummer."""
    starts = [0]
    for m in re.finditer(r"\n", text):
        starts.append(m.end())
    return starts


def line_of(starts, offset):
    return bisect.bisect_right(starts, offset)


def snippet_at(text, offset, length=0, width=96):
    """Fundstelle zitieren: die Zeile, in der der Offset liegt, gekürzt."""
    start = text.rfind("\n", 0, offset) + 1
    end = text.find("\n", offset)
    if end == -1:
        end = len(text)
    line = text[start:end].strip()
    if len(line) > width:
        # um die Fundstelle herum ausschneiden
        rel = offset - start
        left = max(0, rel - width // 2)
        line = ("…" if left > 0 else "") + line[left:left + width] + "…"
    return line


# --------------------------------------------------------------------------
# Farben
# --------------------------------------------------------------------------

HEX_RE = re.compile(r"#[0-9a-fA-F]{3,8}(?![0-9a-fA-F])")
FUNC_COLOR_RE = re.compile(r"\b(rgba?|hsla?)\(([^()]*)\)", re.I)
NAME_RE = re.compile(r"(?<![\w-])(" + "|".join(sorted(NAMED_COLORS, key=len, reverse=True)) + r")(?![\w-])", re.I)


def hex_to_rgba(h):
    h = h[1:]
    if len(h) == 3:
        return (int(h[0] * 2, 16), int(h[1] * 2, 16), int(h[2] * 2, 16), 1.0)
    if len(h) == 4:
        return (int(h[0] * 2, 16), int(h[1] * 2, 16), int(h[2] * 2, 16), int(h[3] * 2, 16) / 255)
    if len(h) == 6:
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 1.0)
    if len(h) == 8:
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), int(h[6:8], 16) / 255)
    return None


def _num(tok):
    tok = tok.strip()
    if tok.endswith("%"):
        return float(tok[:-1]) / 100.0, True
    return float(tok), False


def func_to_rgba(fn, args):
    parts = [p for p in re.split(r"[,\s/]+", args.strip()) if p]
    try:
        if fn.lower().startswith("rgb"):
            vals = []
            for p in parts[:3]:
                v, pct = _num(p)
                vals.append(v * 255 if pct else v)
            a = 1.0
            if len(parts) > 3:
                a, pct = _num(parts[3])
            return (int(round(vals[0])), int(round(vals[1])), int(round(vals[2])), a)
        else:
            hnum = float(re.sub(r"deg|turn|rad", "", parts[0])) / 360.0
            s, _ = _num(parts[1])
            light, _ = _num(parts[2])
            a = 1.0
            if len(parts) > 3:
                a, _ = _num(parts[3])
            r, g, b = colorsys.hls_to_rgb(hnum % 1.0, light, s)
            return (int(round(r * 255)), int(round(g * 255)), int(round(b * 255)), a)
    except (ValueError, IndexError):
        return None


def find_colors(value):
    """Alle Farbliterale in einem CSS-Wert: (rgba, text, relativer_offset)."""
    out = []
    for m in HEX_RE.finditer(value):
        rgba = hex_to_rgba(m.group(0))
        if rgba:
            out.append((rgba, m.group(0), m.start()))
    for m in FUNC_COLOR_RE.finditer(value):
        rgba = func_to_rgba(m.group(1), m.group(2))
        if rgba:
            out.append((rgba, m.group(0), m.start()))
    for m in NAME_RE.finditer(value):
        name = m.group(1).lower()
        # 'tan', 'gold' u. ä. nur zählen, wenn sie als Farbwert stehen können
        r, g, b = NAMED_COLORS[name]
        out.append(((r, g, b, 1.0), m.group(1), m.start()))
    return out


def relative_luminance(rgb):
    def chan(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb[:3]
    return 0.2126 * chan(r) + 0.7152 * chan(g) + 0.0722 * chan(b)


def contrast_ratio(fg, bg):
    l1, l2 = relative_luminance(fg), relative_luminance(bg)
    if l1 < l2:
        l1, l2 = l2, l1
    return (l1 + 0.05) / (l2 + 0.05)


def blend(fg, bg):
    """Vordergrund mit Alpha über Hintergrund legen."""
    a = fg[3]
    if a >= 1.0:
        return fg[:3]
    return tuple(int(round(fg[i] * a + bg[i] * (1 - a))) for i in range(3))


# --------------------------------------------------------------------------
# CSS-Parser (klein gehalten, reicht für handgeschriebenes CSS)
# --------------------------------------------------------------------------

class Decl:
    __slots__ = ("prop", "value", "offset", "rule")

    def __init__(self, prop, value, offset, rule):
        self.prop = prop
        self.value = value
        self.offset = offset
        self.rule = rule


class Rule:
    __slots__ = ("selector", "at_stack", "decls", "offset", "element_text")

    def __init__(self, selector, at_stack, offset):
        self.selector = selector
        self.at_stack = at_stack
        self.decls = []
        self.offset = offset
        self.element_text = None  # nur bei style-Attributen: Inhalt des Elements

    @property
    def at_text(self):
        return " ".join(self.at_stack)

    def is_font_face(self):
        return self.selector.lower().startswith("@font-face")

    def is_keyframes(self):
        return any("@keyframes" in a for a in self.at_stack)

    def get(self, prop):
        for d in reversed(self.decls):
            if d.prop == prop:
                return d
        return None

    def is_dark_context(self):
        at = self.at_text.lower()
        sel = self.selector.lower()
        return ("prefers-color-scheme: dark" in at.replace(" ", " ")
                or "prefers-color-scheme:dark" in at.replace(" ", "")
                or 'data-theme="dark"' in sel.replace(" ", "")
                or "data-theme='dark'" in sel.replace(" ", "")
                or "ground-dark" in sel)

    def is_print_context(self):
        """Regeln unter `@media print` — der dritte Geltungsbereich neben hell
        und dunkel. Wird vor `is_dark_context()` abgefragt: ein Druckblock, der
        `[data-theme="dark"]` mitadressiert, ist Druck, nicht Dunkelmodus."""
        for at in self.at_stack:
            head = at.split("{")[0].lower()
            if head.startswith("@media") and re.search(r"\bprint\b", head):
                return True
        return False

    def is_token_home(self):
        """Blöcke, in denen Hex-Werte laut Regel 8 stehen dürfen."""
        sel = self.selector.replace(" ", "")
        return (sel.startswith(":root") or sel.startswith("html")
                or "[data-theme=" in sel or ".ground-light" in sel or ".ground-dark" in sel)


def split_decls(body):
    """Deklarationen trennen, Semikola in Klammern (url(), rgba()) ignorieren."""
    out, depth, start = [], 0, 0
    for i, ch in enumerate(body):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        elif ch == ";" and depth == 0:
            out.append((start, body[start:i]))
            start = i + 1
    if body[start:].strip():
        out.append((start, body[start:]))
    return out


def parse_css(text, base_offset=0):
    """Regeln mit Selektor, At-Regel-Kontext und Deklarationen."""
    rules, at_stack = [], []
    i, prelude_start, n = 0, 0, len(text)
    while i < n:
        ch = text[i]
        if ch == "{":
            prelude = text[prelude_start:i].strip()
            block_at_rule = prelude.startswith("@") and not prelude.lower().startswith("@font-face")
            if block_at_rule and re.match(r"@(media|supports|keyframes|-\w+-keyframes|layer|container|scope|document)\b",
                                          prelude, re.I):
                at_stack.append(prelude)
                i += 1
                prelude_start = i
                continue
            j = text.find("}", i + 1)
            if j == -1:
                j = n
            rule = Rule(prelude, list(at_stack), base_offset + i)
            body = text[i + 1:j]
            for rel, chunk in split_decls(body):
                if ":" not in chunk:
                    continue
                prop, _, value = chunk.partition(":")
                prop_clean = prop.strip().lower()
                if not prop_clean or " " in prop_clean.strip():
                    continue
                off = base_offset + i + 1 + rel + (len(chunk) - len(chunk.lstrip()))
                rule.decls.append(Decl(prop_clean, value.strip(), off, rule))
            rules.append(rule)
            i = j + 1
            prelude_start = i
            continue
        if ch == "}":
            if at_stack:
                at_stack.pop()
            i += 1
            prelude_start = i
            continue
        i += 1
    return rules


# --------------------------------------------------------------------------
# Dokument einlesen
# --------------------------------------------------------------------------

STYLE_RE = re.compile(r"<style\b[^>]*>(.*?)</style>", re.I | re.S)
SCRIPT_RE = re.compile(r"<script\b[^>]*>.*?</script>", re.I | re.S)
COMMENT_HTML_RE = re.compile(r"<!--.*?-->", re.S)
COMMENT_CSS_RE = re.compile(r"/\*.*?\*/", re.S)
DATAURI_RE = re.compile(r"(url\(\s*['\"]?data:[^,]*,)([^)'\"]*)", re.I)
# Auf Bytes, nicht auf Text: der Vorabscan des Browsers zählt Bytes, und die
# 1024-Byte-Grenze ist nur so nachzurechnen. Beide Schreibweisen der Deklaration.
META_CHARSET_RE = re.compile(
    rb"""<meta[^>]*?charset\s*=\s*["']?\s*([A-Za-z0-9_-]+)""", re.I)
FONTFACE_RE = re.compile(r"@font-face\s*\{(.*?)\}", re.I | re.S)
INLINE_STYLE_RE = re.compile(r"""\sstyle\s*=\s*(?:"([^"]*)"|'([^']*)')""", re.I)


def mask(text, spans):
    """Bereiche durch Leerzeichen ersetzen, Offsets und Zeilen bleiben erhalten."""
    if not spans:
        return text
    buf = list(text)
    for a, b in spans:
        for k in range(a, min(b, len(buf))):
            if buf[k] != "\n":
                buf[k] = " "
    return "".join(buf)


class Document:
    def __init__(self, path):
        self.path = path
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            self.raw = fh.read()

        # Base64-Blobs maskieren: sie enthalten Zeichenfolgen, die sonst als
        # Farbnamen oder Werte fehlgedeutet werden, und blähen jede Suche auf.
        blob_spans = [(m.start(2), m.end(2)) for m in DATAURI_RE.finditer(self.raw)]
        self.masked = mask(self.raw, blob_spans)
        # CSS-Kommentare maskieren (nur innerhalb von <style>), HTML-Kommentare auch.
        self.masked = mask(self.masked, [(m.start(), m.end())
                                         for m in COMMENT_CSS_RE.finditer(self.masked)])
        self.masked = mask(self.masked, [(m.start(), m.end())
                                         for m in COMMENT_HTML_RE.finditer(self.masked)])

        self.lines = line_index(self.raw)
        self.style_spans = [(m.start(1), m.end(1)) for m in STYLE_RE.finditer(self.masked)]
        self.css = "".join(self.masked[a:b] for a, b in self.style_spans)

        self.rules = []
        for a, b in self.style_spans:
            self.rules.extend(parse_css(self.masked[a:b], a))

        # Inline-style-Attribute als Pseudo-Regeln
        for m in INLINE_STYLE_RE.finditer(self.masked):
            body = m.group(1) if m.group(1) is not None else m.group(2)
            base = m.start(1) if m.group(1) is not None else m.start(2)
            rule = Rule("[style-Attribut]", [], base)
            # Textinhalt des Elements mitnehmen: bei SVG-Labels steckt die
            # Versalschreibung im Markup, nicht in text-transform.
            tag_end = self.raw.find(">", m.end())
            if tag_end != -1:
                nxt = self.raw.find("<", tag_end)
                rule.element_text = self.raw[tag_end + 1:nxt if nxt != -1 else tag_end + 80]
            for rel, chunk in split_decls(body):
                if ":" not in chunk:
                    continue
                prop, _, value = chunk.partition(":")
                rule.decls.append(Decl(prop.strip().lower(), value.strip(), base + rel, rule))
            if rule.decls:
                self.rules.append(rule)

        self.decls = [d for r in self.rules for d in r.decls]
        self.faces = self._font_faces()
        self.text = self._visible_text()

    def line(self, offset):
        return line_of(self.lines, offset)

    def snippet(self, offset):
        return snippet_at(self.masked, offset)

    def _font_faces(self):
        """(@font-face-Block, Familie, Stil, Gewicht, base64-Blobs) aus dem Original."""
        faces = []
        for m in FONTFACE_RE.finditer(self.raw):
            body = m.group(1)
            fam = re.search(r"font-family\s*:\s*([^;]+)", body, re.I)
            sty = re.search(r"font-style\s*:\s*([^;]+)", body, re.I)
            wgt = re.search(r"font-weight\s*:\s*([^;]+)", body, re.I)
            blobs = re.findall(r"base64,\s*([A-Za-z0-9+/=]+)", body)
            faces.append({
                "offset": m.start(),
                "family": fam.group(1).strip().strip("'\"") if fam else "?",
                "style": sty.group(1).strip() if sty else "normal",
                "weight": wgt.group(1).strip() if wgt else "400",
                "blobs": blobs,
                "src": re.search(r"src\s*:\s*([^;]+)", body, re.I).group(1) if re.search(r"src\s*:", body, re.I) else "",
            })
        return faces

    def _visible_text(self):
        t = SCRIPT_RE.sub(" ", self.raw)
        t = STYLE_RE.sub(" ", t)
        t = COMMENT_HTML_RE.sub(" ", t)
        t = re.sub(r"<[^>]+>", " ", t)
        return html.unescape(t)


# --------------------------------------------------------------------------
# Tokensatz laden
# --------------------------------------------------------------------------

class Tokens:
    def __init__(self, css_path):
        self.path = css_path
        self.light = {}   # name -> roher Wert
        self.dark = {}
        self.print_ = {}
        self.colors = set()      # (r,g,b) aller Tokenfarben
        self.color_names = {}    # (r,g,b) -> Tokenname
        with open(css_path, "r", encoding="utf-8") as fh:
            text = fh.read()
        text = COMMENT_CSS_RE.sub(" ", text)
        for rule in parse_css(text):
            if rule.is_print_context():
                target = self.print_
            elif rule.is_dark_context():
                target = self.dark
            else:
                target = self.light
            for d in rule.decls:
                if d.prop.startswith("--"):
                    target[d.prop] = d.value.strip()
        # Dunkel und Druck erben alles, was dort nicht überschrieben wird.
        merged_dark = dict(self.light)
        merged_dark.update(self.dark)
        self.dark = merged_dark
        # Der Druckbereich erbt vom hellen Modus — er ist dessen Papierfassung,
        # nicht ein eigenständiges drittes System.
        merged_print = dict(self.light)
        merged_print.update(self.print_)
        self.print_ = merged_print
        for scope in (self.light, self.dark, self.print_):
            for name, value in scope.items():
                if "shadow" in name:
                    continue  # der Schattenwert ist keine Palette-Farbe
                for rgba, literal, _ in find_colors(value):
                    self.colors.add(rgba[:3])
                    self.color_names.setdefault(rgba[:3], name)
        # Rohwerte -> Tokennamen, für "hier gäbe es ein Token"-Hinweise.
        # Mehrdeutig (4px ist Radius *und* Raumstufe), deshalb Liste statt Wert.
        self.value_index = {}
        for name, value in self.light.items():
            self.value_index.setdefault(value.strip().lower(), []).append(name)

    def token_for(self, value, prefix=None):
        names = self.value_index.get(value.strip().lower(), [])
        if prefix:
            names = [n for n in names if n.startswith(prefix)]
        return names[0] if names else None

    def resolve(self, value, mode="light", depth=0):
        """var()-Ketten auflösen; unauflösbar -> None."""
        if depth > 12:
            return None
        scope = {"dark": self.dark, "print": self.print_}.get(mode, self.light)
        m = re.fullmatch(r"\s*var\(\s*(--[\w-]+)\s*(?:,\s*(.*?))?\s*\)\s*", value, re.S)
        if not m:
            return value.strip()
        name, fallback = m.group(1), m.group(2)
        if name in scope:
            return self.resolve(scope[name], mode, depth + 1)
        if fallback:
            return self.resolve(fallback, mode, depth + 1)
        return None


def find_tokens_css(explicit=None):
    if explicit:
        return explicit
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(here, "..", "assets", "tokens.css"),
        os.path.join(here, "assets", "tokens.css"),
        os.path.expanduser("~/.claude/skills/design-identity/assets/tokens.css"),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return os.path.normpath(c)
    return None


# --------------------------------------------------------------------------
# Hilfen für Werte
# --------------------------------------------------------------------------

PX_RE = re.compile(r"(-?\d*\.?\d+)px\b")
NUM_RE = re.compile(r"-?\d*\.?\d+")


def px_values(value):
    return [(float(m.group(1)), m.start(), m.group(0)) for m in PX_RE.finditer(value)]


def strip_vars(value):
    """var(...)-Aufrufe entfernen, damit nur Rohwerte übrig bleiben."""
    out, depth, buf = [], 0, []
    i = 0
    while i < len(value):
        if value.startswith("var(", i):
            depth = 1
            i += 4
            while i < len(value) and depth:
                if value[i] == "(":
                    depth += 1
                elif value[i] == ")":
                    depth -= 1
                i += 1
            out.append(" ")
            continue
        out.append(value[i])
        i += 1
    return "".join(out)


def has_var(value):
    return "var(" in value


def rule_font_size_px(rule, tokens):
    d = rule.get("font-size")
    if not d:
        return None
    resolved = tokens.resolve(d.value, "light") if has_var(d.value) else d.value
    if not resolved:
        return None
    px = px_values(resolved)
    return px[0][0] if px else None


def rule_font_weight(rule, tokens):
    d = rule.get("font-weight")
    if not d:
        return None
    resolved = tokens.resolve(d.value, "light") if has_var(d.value) else d.value
    if not resolved:
        return None
    if "bold" in resolved.lower():
        return 700
    m = NUM_RE.search(resolved)
    return float(m.group(0)) if m else None


def rule_is_mono(rule, tokens):
    d = rule.get("font-family")
    if d:
        v = (tokens.resolve(d.value, "light") or d.value).lower()
        if "mono" in v:
            return True
    return "mono" in rule.selector.lower()


# --------------------------------------------------------------------------
# Prüfungen
# --------------------------------------------------------------------------

def check_pure_black_white(doc, tokens, rep):
    """Reines Schwarz/Weiß in jeder Schreibweise — Regel 7."""
    for d in doc.decls:
        # Der Popover-Schatten ist die eine dokumentierte Ausnahme und enthält
        # legitim transparentes Schwarz; Tokendefinitionen sonst mitprüfen.
        if "shadow" in d.prop or "shadow" in d.rule.selector.lower():
            continue
        for rgba, literal, rel in find_colors(d.value):
            rgb = rgba[:3]
            if rgb not in ((0, 0, 0), (255, 255, 255)):
                continue
            # Die eine deklarierte Ausnahme: im Druckbereich geht genau bei den
            # Tokens auf Weiß, für die tokens.css dort selbst Weiß vorsieht.
            # Kein Freibrief für den ganzen @media-print-Block — jedes andere
            # Token und jede Elementregel darin wird weiter gemeldet.
            if (d.rule.is_print_context() and rgb == (255, 255, 255)
                    and find_colors(tokens.print_.get(d.prop, ""))
                    and find_colors(tokens.print_[d.prop])[0][0][:3] == (255, 255, 255)):
                continue
            line = doc.line(d.offset + len(d.prop) + 1 + rel)
            if rgba[3] >= 1.0:
                rep.add("fehler", "reines-schwarz-weiss", line,
                        f"`{literal}` in `{d.prop}` — reines Schwarz/Weiß kommt im System nicht vor",
                        doc.snippet(d.offset),
                        "warme Entsprechung: --ac-ink-0 / --ac-paper-0")
            else:
                rep.add("warnung", "reines-schwarz-weiss", line,
                        f"`{literal}` in `{d.prop}` — transparentes Schwarz/Weiß kippt den warmen Grund ins Neutrale",
                        doc.snippet(d.offset))

    # Präsentationsattribute in eingebettetem SVG
    for m in re.finditer(r"""\b(fill|stroke|stop-color|bgcolor|color)\s*=\s*["']([^"']+)["']""",
                         doc.masked, re.I):
        for rgba, literal, _ in find_colors(m.group(2)):
            if rgba[:3] in ((0, 0, 0), (255, 255, 255)) and rgba[3] >= 1.0:
                rep.add("fehler", "reines-schwarz-weiss", doc.line(m.start()),
                        f"`{literal}` als `{m.group(1)}`-Attribut — reines Schwarz/Weiß",
                        doc.snippet(m.start()),
                        "SVG erbt mit fill=\"currentColor\" die Tinte des Kontexts")


def check_box_shadow(doc, tokens, rep):
    """Keine Schatten — Regel 5. Einzige Ausnahme: das Popover-Token."""
    popover_light = tokens.light.get("--ac-shadow-popover", "").strip().lower()
    popover_dark = tokens.dark.get("--ac-shadow-popover", "").strip().lower()
    allowed = {popover_light, popover_dark, "none", "0", "inherit", "unset", "initial"}
    for d in doc.decls:
        if d.prop == "--ac-shadow-popover":
            continue
        if d.prop in ("box-shadow", "-webkit-box-shadow"):
            v = d.value.strip().lower()
            if v in allowed or "var(--ac-shadow-popover)" in v.replace(" ", ""):
                continue
            rep.add("fehler", "box-shadow", doc.line(d.offset),
                    "`box-shadow` außerhalb des Popover-Tokens — Hierarchie kommt aus Flächen und Haarlinien",
                    doc.snippet(d.offset),
                    "Fläche stufen (paper-0/1/2) oder eine Haarlinie setzen; schwebende Menüs: var(--ac-shadow-popover)")
        elif d.prop == "text-shadow" and d.value.strip().lower() not in ("none", "inherit"):
            rep.add("fehler", "box-shadow", doc.line(d.offset),
                    "`text-shadow` — im System gibt es keine Schatten",
                    doc.snippet(d.offset))
        elif d.prop == "filter" and "drop-shadow" in d.value.lower():
            rep.add("fehler", "box-shadow", doc.line(d.offset),
                    "`filter: drop-shadow(...)` ist ein Schatten mit anderem Namen",
                    doc.snippet(d.offset))


def check_hex_off_token(doc, tokens, rep):
    """Jede Farbe muss im Tokensatz vorkommen."""
    seen = set()
    for d in doc.decls:
        if d.rule.is_font_face():
            continue
        if d.prop not in COLOR_PROPS and not d.prop.startswith("--") \
                and d.prop not in ("background-image", "box-shadow", "text-decoration",
                                   "outline", "border-image", "scrollbar-color"):
            # Farben tauchen praktisch nur in diesen Eigenschaften auf
            if not find_colors(d.value):
                continue
        for rgba, literal, rel in find_colors(d.value):
            rgb = rgba[:3]
            if rgb in tokens.colors or rgb in ((0, 0, 0), (255, 255, 255)):
                continue  # reines S/W meldet die eigene Prüfung
            key = (rgb, d.prop)
            if key in seen:
                continue
            seen.add(key)
            near = nearest_token_color(rgb, tokens)
            rep.add("fehler", "farbe-ausserhalb-tokensatz", doc.line(d.offset),
                    f"`{literal}` in `{d.prop}` steht nicht im Tokensatz",
                    doc.snippet(d.offset),
                    f"nächstliegendes Token: {near}" if near else "")


def nearest_token_color(rgb, tokens):
    best, best_d = None, None
    for trgb, name in tokens.color_names.items():
        dist = sum((rgb[i] - trgb[i]) ** 2 for i in range(3))
        if best_d is None or dist < best_d:
            best, best_d = name, dist
    if best is None:
        return None
    return f"{best} (Abstand {int(best_d ** 0.5)})"


def check_token_overrides(doc, tokens, rep):
    """`--ac-*` mit abweichendem Wert neu definiert, oder eigene Palette erfunden."""
    for d in doc.decls:
        if not d.prop.startswith("--"):
            continue
        if d.rule.is_print_context():
            mode, scope = "druck", tokens.print_
        elif d.rule.is_dark_context():
            mode, scope = "dark", tokens.dark
        else:
            mode, scope = "light", tokens.light
        if d.prop.startswith("--ac-"):
            if d.prop not in scope:
                rep.add("warnung", "token-erfunden", doc.line(d.offset),
                        f"`{d.prop}` sieht wie ein Systemtoken aus, steht aber nicht in tokens.css",
                        doc.snippet(d.offset))
                continue
            want = scope[d.prop].strip()
            got = d.value.strip()
            # Im Druckbereich sind zwei Fassungen richtig: die deklarierte
            # Papierfassung (volle Ersetzung) und der helle Wert (nur den Modus
            # umschalten, nichts ersetzen). Letzteres ist die einzig korrekte
            # Wahl für ein Dokument, das die Farben selbst als Belegstück
            # zeigt — sonst nennt die Beschriftung gedruckt einen anderen Wert
            # als die Fläche daneben. Alles Dritte bleibt ein Fehler.
            allowed = [want]
            if mode == "druck" and d.prop in tokens.light:
                allowed.append(tokens.light[d.prop].strip())
            if any(a.lower() == got.lower() for a in allowed):
                continue
            got_c = find_colors(got)
            if got_c and any(ac and ac[0][0][:3] == got_c[0][0][:3]
                             for ac in (find_colors(a) for a in allowed)):
                continue
            want_c = find_colors(want)
            if d.prop.startswith("--ac-font-"):
                # Bei Schriftstapeln zählt die erste Familie; ein gekürzter
                # Fallback-Stapel ist eine Entscheidung, kein Systembruch.
                first = lambda s: s.split(",")[0].strip().strip("'\"").lower()
                if first(want) == first(got):
                    continue
            if not want_c and not got_c and re.sub(r"\s+", "", want.lower()) == re.sub(r"\s+", "", got.lower()):
                continue
            if mode == "druck":
                choices = " oder ".join(f"`{a}`" for a in dict.fromkeys(allowed))
                rep.add("fehler", "token-abweichend", doc.line(d.offset),
                        f"`{d.prop}` (druck) ist `{got}`, im Druckbereich zulässig ist {choices}",
                        doc.snippet(d.offset),
                        "tokens.css deklariert den Druckbereich — Papierfassung übernehmen "
                        "oder den hellen Wert stehen lassen, aber nichts Drittes erfinden")
            else:
                rep.add("fehler", "token-abweichend", doc.line(d.offset),
                        f"`{d.prop}` ({mode}) ist `{got}`, tokens.css sagt `{want}`",
                        doc.snippet(d.offset),
                        "tokens.css ist die Quelle der Wahrheit — Wert übernehmen statt lokal abweichen")
        else:
            if find_colors(d.value):
                rep.add("warnung", "palette-erfunden", doc.line(d.offset),
                        f"`{d.prop}` definiert eine Farbe außerhalb des `--ac-*`-Satzes",
                        doc.snippet(d.offset),
                        "Kategoriefarben heißen --ac-cat-1..5 (+ -tint, -on-tint) und sind vollständig belegt")


def check_letter_spacing(doc, tokens, rep):
    """Positive Laufweite nur bei Mono-Mikrolabeln in Versalien (SKILL.md)."""
    for d in doc.decls:
        if d.prop != "letter-spacing" or d.rule.is_font_face():
            continue
        resolved = tokens.resolve(d.value, "light") if has_var(d.value) else d.value
        if resolved is None:
            continue
        m = NUM_RE.search(resolved)
        if not m:
            continue
        val = float(m.group(0))
        unit = resolved[m.end():].strip()[:2]
        if val <= 0:
            continue
        em = val if unit.startswith("em") else (val / 16.0 if unit.startswith("px") else val)
        rule = d.rule
        tt = rule.get("text-transform")
        upper_css = bool(tt and "uppercase" in tt.value.lower())
        text = (rule.element_text or "").strip()
        upper_markup = bool(text) and not any(c.islower() for c in text) and any(c.isalpha() for c in text)
        mono = rule_is_mono(rule, tokens)
        size = rule_font_size_px(rule, tokens)
        small = size is not None and size <= 12
        line = doc.line(d.offset)
        label_shape = mono and small
        if not (0.035 <= em <= 0.065):
            rep.add("fehler", "laufweite", line,
                    f"`{d.value.strip()}` liegt außerhalb der vertretbaren Bandbreite 0.04–0.06em",
                    doc.snippet(d.offset), "var(--ac-tracking-label) = 0.05em")
        elif not label_shape:
            missing = []
            if not mono:
                missing.append("kein Mono-Schnitt")
            if size is None:
                missing.append("keine Schriftgröße im Block")
            elif not small:
                missing.append(f"{size:g}px über --ac-text-caption")
            rep.add("fehler", "laufweite", line,
                    f"positive Laufweite `{d.value.strip()}` in `{rule.selector.strip()}` — "
                    f"{', '.join(missing)}; die Ausnahme gilt nur für Mono-Mikrolabel in Versalien",
                    doc.snippet(d.offset))
        elif not (upper_css or upper_markup):
            rep.add("warnung", "laufweite", line,
                    f"positive Laufweite in `{rule.selector.strip()}` — Mono-Mikrolabel, aber die "
                    "Versalien sind nicht belegt (kein `text-transform: uppercase`)",
                    doc.snippet(d.offset),
                    "Wenn der Text schon in Versalien gesetzt ist: text-transform ergänzen, "
                    "damit die Ausnahme prüfbar bleibt")
        elif not has_var(d.value):
            rep.add("warnung", "laufweite", line,
                    f"`{d.value.strip()}` als Rohwert — die Ausnahme ist ein Token, kein getippter Wert",
                    doc.snippet(d.offset), "var(--ac-tracking-label)")


def check_spacing_grid(doc, tokens, rep):
    """padding / margin / gap auf dem 4px-Raster."""
    for d in doc.decls:
        if d.prop not in SPACING_PROPS or d.rule.is_font_face():
            continue
        raw = strip_vars(d.value)
        for val, rel, literal in px_values(raw):
            a = abs(val)
            line = doc.line(d.offset)
            if a != int(a):
                rep.add("fehler", "raster", line,
                        f"`{literal}` in `{d.prop}` — Halbpixel gibt es in der Skala nicht",
                        doc.snippet(d.offset))
            elif a == 1 and d.prop.endswith("gap"):
                rep.add("warnung", "raster", line,
                        f"`{literal}` in `{d.prop}` — als Trennfuge in Haarlinienstärke vertretbar, sonst rasterwidrig",
                        doc.snippet(d.offset), "var(--ac-hairline)")
            elif int(a) % 4 != 0:
                rep.add("fehler", "raster", line,
                        f"`{literal}` in `{d.prop}` liegt nicht auf dem 4px-Raster",
                        doc.snippet(d.offset),
                        f"nächste Stufen: {nearest_grid(a)}")
            elif int(a) not in SPACE_SCALE:
                rep.add("warnung", "raster", line,
                        f"`{literal}` in `{d.prop}` ist zwar durch 4 teilbar, steht aber nicht in der Raumskala",
                        doc.snippet(d.offset),
                        "Skala: 4 8 12 16 20 24 32 40 56 72")


def nearest_grid(v):
    steps = sorted(SPACE_SCALE)
    below = max([s for s in steps if s <= v], default=steps[0])
    above = min([s for s in steps if s >= v], default=steps[-1])
    return f"{below}px / {above}px"


def check_font_size_scale(doc, tokens, rep):
    """font-size nur auf den elf Stufen."""
    for d in doc.decls:
        if d.prop != "font-size" or d.rule.is_font_face():
            continue
        raw = strip_vars(d.value)
        px = px_values(raw)
        line = doc.line(d.offset)
        if not px:
            if raw.strip() and not re.fullmatch(r"[\s;]*", raw) and not has_var(d.value):
                rep.add("hinweis", "typo-skala", line,
                        f"`font-size: {d.value.strip()}` ist keine Stufe der Skala (relative Einheit)",
                        doc.snippet(d.offset),
                        "Skala: 11 12 13 14 16 18 20 24 30 38 48")
            continue
        for val, rel, literal in px:
            if val in TYPE_SCALE:
                continue
            near = sorted(TYPE_SCALE, key=lambda s: abs(s - val))[0]
            rep.add("fehler", "typo-skala", line,
                    f"`font-size: {literal}` steht nicht in der Skala",
                    doc.snippet(d.offset),
                    f"nächste Stufe: {near}px = var({TYPE_SCALE[near]})")


TOKENISABLE = {
    "font-size": "--ac-text-*",
    "border-radius": "--ac-radius*",
    "letter-spacing": "--ac-tracking-*",
    "line-height": "--ac-leading-*",
    "font-weight": "--ac-weight-*",
    "font-family": "--ac-font-*",
    "transition-duration": "--ac-dur*",
    "animation-duration": "--ac-dur*",
}
for _p in SPACING_PROPS:
    TOKENISABLE[_p] = "--ac-space-*"
for _p in ("color", "background", "background-color", "border-color", "fill", "stroke",
           "outline-color", "border-top-color", "border-right-color", "border-bottom-color",
           "border-left-color", "stop-color", "caret-color", "accent-color"):
    TOKENISABLE[_p] = "Farbtoken"


def check_raw_values(doc, tokens, rep):
    """Regel 8: jeder Wert durch var(--ac-*), nicht als Rohzahl."""
    for d in doc.decls:
        if d.rule.is_font_face() or d.rule.is_keyframes() or d.prop.startswith("--"):
            continue
        group = TOKENISABLE.get(d.prop)
        if not group:
            continue
        if d.rule.is_token_home() and group == "Farbtoken":
            continue  # :root/[data-theme]/.ground-* dürfen Hex tragen
        raw = strip_vars(d.value)
        offenders = []
        if group == "Farbtoken":
            offenders = [lit for _, lit, _ in find_colors(raw)]
        elif group == "--ac-font-*":
            if re.search(r"(plex|serif|sans-serif|monospace|georgia|helvetica)", raw, re.I):
                offenders = [raw.strip()[:60]]
        elif group == "--ac-weight-*":
            if re.search(r"\d{3}|bold", raw, re.I):
                offenders = [raw.strip()]
        elif group == "--ac-leading-*":
            if NUM_RE.search(raw):
                offenders = [raw.strip()]
        elif group == "--ac-dur*":
            if re.search(r"\d+\s*m?s\b", raw):
                offenders = [raw.strip()]
        elif group == "--ac-tracking-*":
            # Positive Werte meldet die Laufweiten-Prüfung mit mehr Kontext.
            m = NUM_RE.search(raw)
            if m and float(m.group(0)) < 0:
                offenders = [raw.strip()]
        else:
            px = px_values(raw)
            if d.prop.startswith("border") and "1px" in raw:
                px = [p for p in px if p[0] != 1.0]  # 1px im border-Kurzformat ist erlaubt
            offenders = [lit for _, _, lit in px]
        if not offenders:
            continue
        if group == "Farbtoken":
            colors = find_colors(raw)
            exact = tokens.color_names.get(colors[0][0][:3]) if colors else None
        else:
            exact = tokens.token_for(d.value, group.rstrip("*"))
        rep.add("warnung", "rohwert-statt-token",
                doc.line(d.offset),
                f"`{d.prop}: {' '.join(offenders[:4])}` als Rohwert geschrieben",
                doc.snippet(d.offset),
                f"var({exact})" if exact else f"aus {group} nehmen")


def check_dark_mode(doc, tokens, rep):
    """Beide Schaltwege müssen da sein — außer bei druckbestimmten Dokumenten."""
    css = doc.css
    has_media = "prefers-color-scheme" in css
    has_attr = "[data-theme" in css.replace(" ", "")
    print_bound = "@page" in css
    if has_media and has_attr:
        return
    sev = "hinweis" if print_bound else "fehler"
    extra = (" — die Datei ist mit `@page` druckbestimmt, dann ist Hell-only die richtige Entscheidung "
             "(references/web-and-artifacts.md, Entscheidungsregel)") if print_bound else ""
    if not has_media and not has_attr:
        rep.add(sev, "dark-mode", 1,
                "kein Dunkelmodus: weder `prefers-color-scheme`-Block noch `[data-theme]`-Block" + extra,
                "", "" if print_bound else "Artefakte erben den Modus des Betrachters — hell-only ist für die Hälfte der Leser kaputt")
    elif not has_media:
        rep.add(sev, "dark-mode", 1,
                "`[data-theme]` vorhanden, aber kein `@media (prefers-color-scheme: dark)`" + extra,
                "", "" if print_bound else "ohne Media-Block startet die Seite für Dunkelmodus-Leser hell")
    else:
        rep.add(sev, "dark-mode", 1,
                "`prefers-color-scheme`-Block vorhanden, aber kein `[data-theme]`-Block" + extra,
                "", "" if print_bound else "ohne [data-theme] lässt sich der Modus nicht manuell umschalten")


def check_font_embedding(doc, tokens, rep):
    """Schriften als data-URI, nicht von außen geladen."""
    for host in ("fonts.googleapis.com", "fonts.gstatic.com", "use.typekit.net", "cdn.jsdelivr.net"):
        for m in re.finditer(re.escape(host), doc.masked, re.I):
            rep.add("fehler", "font-einbettung", doc.line(m.start()),
                    f"externer Schrifthost `{host}` — in Artefakten blockiert, die Seite fällt still auf die Systemschrift zurück",
                    doc.snippet(m.start()),
                    "assets/plex-embedded.css in den <style>-Block splicen")
    for m in re.finditer(r"@import\b[^;]*", doc.css, re.I):
        rep.add("fehler", "font-einbettung", doc.line(doc.style_spans[0][0] + m.start()),
                "`@import` im Stylesheet — externe Ressource, im Artefakt nicht garantiert",
                m.group(0)[:96])
    if not doc.faces:
        if re.search(r"IBM Plex", doc.masked, re.I):
            rep.add("fehler", "font-einbettung", 1,
                    "IBM Plex wird benutzt, aber kein `@font-face` mit data-URI im Dokument",
                    "", "ohne Einbettung rendert die Seite in der Systemschrift")
        return
    for face in doc.faces:
        if not face["blobs"]:
            rep.add("fehler", "font-einbettung", doc.line(face["offset"]),
                    f"`@font-face` für {face['family']} ohne base64-data-URI",
                    face["src"][:96])


def check_glyph_coverage(doc, tokens, rep):
    """Zeichen im sichtbaren Text gegen die tatsächlich eingebetteten cmaps."""
    if not doc.faces:
        return
    try:
        from fontTools.ttLib import TTFont
    except ImportError:
        rep.add("hinweis", "zeichensatz", 1,
                "Zeichensatzprüfung übersprungen: fontTools nicht installiert",
                "", "pip install fonttools brotli")
        return
    covered, failed = set(), []
    for face in doc.faces:
        for blob in face["blobs"]:
            try:
                font = TTFont(io.BytesIO(base64.b64decode(blob)), lazy=True)
                covered |= set(font.getBestCmap().keys())
                font.close()
            except Exception as exc:  # defekter Blob, fehlendes brotli
                failed.append(f"{face['family']} {face['weight']} {face['style']}: {exc}")
    if not covered:
        rep.add("hinweis", "zeichensatz", 1,
                "Zeichensatzprüfung übersprungen: keine cmap lesbar "
                + ("(" + failed[0] + ")" if failed else ""),
                "", "für woff2 wird brotli gebraucht: pip install brotli")
        return
    if failed:
        rep.add("hinweis", "zeichensatz", 1,
                f"{len(failed)} Schnitt(e) nicht lesbar, Prüfung lief gegen die übrigen",
                failed[0][:96])
    # Dokumentierte Ersatzzeichen: IBM Plex hat manche Zeichen schlicht nicht,
    # references/web-and-artifacts.md nennt den eingebetteten Ersatz.
    substitutes = {0x2717: "❌ (U+274C), der in Plex gezeichnete Ersatz — "
                           "references/web-and-artifacts.md",
                   0x2716: "❌ (U+274C), der in Plex gezeichnete Ersatz"}
    missing = {}
    for ch in doc.text:
        cp = ord(ch)
        if ch.isspace() or cp < 0x20 or cp in (0x200B, 0xFEFF, 0x00A0, 0x200A, 0x2009, 0x202F):
            continue
        if cp not in covered:
            missing[ch] = missing.get(ch, 0) + 1
    for ch, count in sorted(missing.items(), key=lambda kv: -kv[1]):
        pos = doc.raw.find(ch)
        rep.add("fehler", "zeichensatz", doc.line(pos) if pos >= 0 else 1,
                f"`{ch}` (U+{ord(ch):04X}, {count}×) fehlt im eingebetteten Subset — "
                "das Zeichen fällt auf die Systemschrift zurück",
                doc.snippet(pos) if pos >= 0 else "",
                substitutes.get(ord(ch),
                                "Subset erweitern (assets/plex-embedded.css) oder Zeichen ersetzen"))


def check_font_weight(doc, tokens, rep):
    """600 gehört der Wortmarke, mehr als 600 gibt es nicht."""
    six_hundred = []
    for d in doc.decls:
        if d.prop != "font-weight" or d.rule.is_font_face():
            continue
        resolved = tokens.resolve(d.value, "light") if has_var(d.value) else d.value
        resolved = (resolved or d.value).lower()
        if "bolder" in resolved or re.search(r"\bbold\b", resolved):
            rep.add("fehler", "gewicht", doc.line(d.offset),
                    f"`font-weight: {d.value.strip()}` entspricht 700 — das System hat drei Gewichte: 400, 500, 600",
                    doc.snippet(d.offset), "Überschriften sind 500")
            continue
        for m in NUM_RE.finditer(resolved):
            w = float(m.group(0))
            if w >= 700:
                rep.add("fehler", "gewicht", doc.line(d.offset),
                        f"`font-weight: {int(w)}` — über 600 gibt es im System nichts",
                        doc.snippet(d.offset))
            elif w == 600:
                six_hundred.append(d)
            elif w not in WEIGHT_SCALE:
                rep.add("fehler", "gewicht", doc.line(d.offset),
                        f"`font-weight: {int(w)}` steht nicht in der Skala 400 / 500 / 600",
                        doc.snippet(d.offset))
    if len(six_hundred) > 1:
        for d in six_hundred[1:]:
            rep.add("warnung", "gewicht", doc.line(d.offset),
                    f"`font-weight: 600` mehrfach ({len(six_hundred)}×) — 600 gehört allein der Wortmarke",
                    doc.snippet(d.offset), f"erste Verwendung: Zeile {doc.line(six_hundred[0].offset)}")
    if re.search(r"<(strong|b)\b", doc.masked, re.I):
        styled = any(re.search(r"\b(strong|b)\b", r.selector) and r.get("font-weight")
                     for r in doc.rules)
        if not styled:
            rep.add("hinweis", "gewicht", 1,
                    "`<strong>`/`<b>` im Markup ohne eigene Regel — der Browser setzt 700",
                    "", "strong { font-weight: var(--ac-weight-medium) }")


RADIO_MARK_SELECTOR = re.compile(r"\.radio-mark(?![\w-])")


def check_radius(doc, tokens, rep):
    """Radius nur 2 / 4 / 8px, keine Pillen, keine Kreise.

    Eine benannte Ausnahme: `.radio-mark`, der gefüllte Punkt in einem
    Optionsfeld — Rund/Eckig ist die universelle Kodierung für
    Einfachauswahl gegen Mehrfachauswahl, siehe SKILL.md Regel 6. Der
    Selektor muss exakt diese Klasse tragen (Wortgrenze, kein Teilstring wie
    `.radio-marker`); jeder andere Kreis bleibt ein Fehler.
    """
    for d in doc.decls:
        if not d.prop.startswith("border") or "radius" not in d.prop:
            continue
        resolved = tokens.resolve(d.value, "light") if has_var(d.value) else d.value
        resolved = resolved or d.value
        line = doc.line(d.offset)
        if "%" in resolved:
            if RADIO_MARK_SELECTOR.search(d.rule.selector):
                continue
            rep.add("fehler", "radius", line,
                    f"`{d.prop}: {d.value.strip()}` — prozentualer Radius ist ein Kreis bzw. eine Pille, Regel 6 schließt beides aus",
                    doc.snippet(d.offset),
                    "nummerierte Marker: 24px-Kasten mit var(--ac-radius-sm); "
                    "die eine erlaubte Stelle für einen Kreis ist .radio-mark")
            continue
        for val, rel, literal in px_values(resolved):
            if val in RADIUS_SCALE:
                continue
            if val > 8:
                rep.add("fehler", "radius", line,
                        f"`{d.prop}: {literal}` — ab 8px wird die Form weich, ≥ halbe Elementhöhe ist eine Pille",
                        doc.snippet(d.offset),
                        "2px Chips und Marker, 4px Standard, 8px nur über ~400px Fläche")
            else:
                rep.add("fehler", "radius", line,
                        f"`{d.prop}: {literal}` steht nicht im Radius-System (2 / 4 / 8px)",
                        doc.snippet(d.offset))
    for m in re.finditer(r'\brx\s*=\s*["\'](\d+(?:\.\d+)?)["\']', doc.masked):
        if float(m.group(1)) not in RADIUS_SCALE:
            rep.add("warnung", "radius", doc.line(m.start()),
                    f"SVG-`rx=\"{m.group(1)}\"` außerhalb des Radius-Systems",
                    doc.snippet(m.start()))


BORDER_WIDTH_PROPS = ("border", "border-top", "border-right", "border-bottom", "border-left",
                      "border-width", "border-top-width", "border-right-width",
                      "border-bottom-width", "border-left-width", "border-block",
                      "border-inline", "outline", "outline-width", "column-rule",
                      "column-rule-width")


def check_line_width(doc, tokens, rep):
    """Linien sind 1px. Die einzige 2px-Linie ist die Akzentregel über Zwischenüberschriften."""
    for d in doc.decls:
        if d.rule.is_font_face():
            continue
        if d.prop in BORDER_WIDTH_PROPS:
            for val, rel, literal in px_values(strip_vars(d.value)):
                if val in (0.0, 1.0, 2.0):
                    continue
                hint = ("var(--ac-hairline) = 1px, var(--ac-rule-accent) = 2px"
                        if val < 2 else "über 2px hat das System keine Linienstärke")
                rep.add("fehler", "linienstaerke", doc.line(d.offset),
                        f"`{d.prop}: {literal}` — Linien sind 1px, die einzige 2px-Linie ist die Akzentregel",
                        doc.snippet(d.offset), hint)
        elif d.prop == "stroke-width":
            m = NUM_RE.search(strip_vars(d.value))
            if m and float(m.group(0)) > 2:
                rep.add("warnung", "linienstaerke", doc.line(d.offset),
                        f"`stroke-width: {m.group(0)}` — Iconstrich ist 1.5 auf 24er-Raster, Linienwerk bleibt darunter",
                        doc.snippet(d.offset))
    for m in re.finditer(r'\bstroke-width\s*=\s*["\'](\d+(?:\.\d+)?)["\']', doc.masked):
        if float(m.group(1)) > 2:
            rep.add("warnung", "linienstaerke", doc.line(m.start()),
                    f"SVG-`stroke-width=\"{m.group(1)}\"` über der Systemstärke",
                    doc.snippet(m.start()))


def check_encoding(doc, tokens, rep):
    """Die Datei muss ihre Kodierung selbst deklarieren.

    Der Linter liest die Datei als UTF-8 und sieht deshalb sauberen Text — ein
    Browser tut das nicht. Ohne `<meta charset>` und ohne `charset` im
    Content-Type fällt er auf die Legacy-Kodierung seiner Locale zurück
    (windows-1252 im westlichen Raum), und jeder Umlaut zerfällt: aus `präzise`
    wird `prÃ¤zise`. Über `file://` rettet die UTF-8-Vermutung von Chromium die
    Seite noch, über HTTP ohne Header-charset nicht mehr. Die Deklaration ist
    das Einzige, was unter allen Auslieferungswegen trägt.
    """
    with open(doc.path, "rb") as fh:
        data = fh.read()

    if data.startswith(b"\xef\xbb\xbf"):
        return  # BOM schlägt jede Deklaration, dann ist die Datei eindeutig

    try:
        data.decode("utf-8")
    except UnicodeDecodeError as exc:
        rep.add("fehler", "zeichenkodierung", 1,
                f"Datei ist nicht als UTF-8 lesbar (Byte {exc.start}) — die Quelle ist bereits kaputt",
                "", "Datei als UTF-8 neu schreiben, nicht die Deklaration nachziehen")
        return

    # Bereits doppelt kodierter Text: das repariert keine Deklaration mehr.
    for bad, good in (("Ã¤", "ä"), ("Ã¶", "ö"), ("Ã¼", "ü"), ("ÃŸ", "ß"),
                      ("Ã„", "Ä"), ("Ã–", "Ö"), ("Ãœ", "Ü"), ("â€”", "—"),
                      ("â€™", "’"), ("â€œ", "“")):
        idx = doc.raw.find(bad)
        if idx != -1:
            rep.add("fehler", "zeichenkodierung", doc.line(idx),
                    f"`{bad}` im Text — doppelt kodiert, gemeint ist `{good}`",
                    doc.snippet(idx),
                    "Quelle als UTF-8 neu speichern; eine charset-Angabe heilt das nicht")

    m = META_CHARSET_RE.search(data)
    if not m:
        if any(ord(ch) > 127 for ch in doc.text):
            rep.add("fehler", "zeichenkodierung", 1,
                    "keine `<meta charset>`-Deklaration, aber Text jenseits von ASCII — "
                    "über HTTP ohne Header-charset rendert der Browser windows-1252 und alle Umlaute zerfallen",
                    "", '<meta charset="utf-8"> als erstes Element in den Kopf')
        return

    declared = m.group(1).decode("ascii", "replace").lower()
    if declared not in ("utf-8", "utf8"):
        rep.add("fehler", "zeichenkodierung", doc.line(m.start()),
                f"`charset={declared}` deklariert — die Datei ist UTF-8",
                "", '<meta charset="utf-8">')
        return

    # Die Reihenfolge entscheidet, nicht der Abstand. Findet der Parser die
    # Deklaration erst nach dem Vorabscan, startet er den Lauf neu — das trägt
    # in Chromium noch bei Byte 60000. Es trägt aber nicht mehr, sobald vorher
    # ein Nicht-ASCII-Byte lag: das ist dann bereits in der Legacy-Kodierung
    # gelesen, der Neustart entfällt, und der Text zerfällt trotz Deklaration.
    first_non_ascii = next((i for i, b in enumerate(data) if b > 0x7F), -1)
    if first_non_ascii != -1 and first_non_ascii < m.start():
        rep.add("fehler", "zeichenkodierung", doc.line(m.start()),
                f"`<meta charset>` steht bei Byte {m.start()}, das erste Nicht-ASCII-Zeichen schon "
                f"bei Byte {first_non_ascii} — der Parser hat es gelesen, bevor die Deklaration greift",
                "", "die Deklaration als erstes Element in den Kopf ziehen")
    elif m.start() >= 1024:
        rep.add("warnung", "zeichenkodierung", doc.line(m.start()),
                f"`<meta charset>` steht erst bei Byte {m.start()} — jenseits des 1024-Byte-Vorabscans. "
                "Chromium fängt das mit einem Neustart des Parselaufs ab, garantiert ist das nicht",
                "", "die Deklaration als erstes Element in den Kopf ziehen")


def check_lang(doc, tokens, rep):
    """Die Sprache muss am Wrapper stehen, nicht nur am `<html>`.

    Ohne `lang` trennt der Browser deutsche Prosa nach englischen Regeln, und ein
    Screenreader liest sie mit englischer Stimme. Zwei Stufen, weil zwei
    Auslieferungswege: eine eigenständige Datei mit `<html lang="de">` ist als
    Datei korrekt — im Artefakt wird das `<html>` aber erzeugt und nichts, was
    man schreibt, steuert es. Dann ist das Attribut still weg.
    """
    # <style>/<script> zusätzlich maskieren: ein `:lang()`-Selektor oder ein
    # JS-String darf nicht als Attribut durchgehen.
    text = mask(doc.masked, [(m.start(), m.end()) for m in STYLE_RE.finditer(doc.masked)])
    text = mask(text, [(m.start(), m.end()) for m in SCRIPT_RE.finditer(text)])

    hits = [(m.group(1).lower(), m.start()) for m in
            re.finditer(r"<(\w+)[^>]*\slang\s*=\s*[\"']([A-Za-z][\w-]*)[\"']", text, re.I)]
    if not hits:
        rep.add("fehler", "sprache", 1,
                "kein `lang`-Attribut im Dokument — deutsche Prosa wird nach englischen "
                "Regeln getrennt und mit englischer Stimme vorgelesen",
                "", '<div class="wrap" lang="de">')
        return

    if all(tag == "html" for tag, _ in hits):
        off = hits[0][1]
        rep.add("warnung", "sprache", doc.line(off),
                "`lang` steht nur am `<html>` — als eigenständige Datei richtig, im "
                "Artefakt aber verloren, weil das `<html>` dort erzeugt wird",
                doc.snippet(off),
                "zusätzlich am Wrapper setzen: <div class=\"wrap\" lang=\"de\">")


def check_focus(doc, tokens, rep):
    """Sichtbarer Fokus, sobald es etwas zu bedienen gibt."""
    interactive = re.search(r"<a\s[^>]*href|<button\b|<input\b|<select\b|<textarea\b|"
                            r'role\s*=\s*["\']button|tabindex\s*=', doc.masked, re.I)
    if not interactive:
        return
    # `:focus-visible`, nicht `:focus` — web-and-artifacts.md verlangt genau das,
    # damit der Ring für Tastaturbedienung erscheint, ohne jeden Mausklick zu rahmen.
    focus_rules = [r for r in doc.rules if ":focus-visible" in r.selector]
    visible = [r for r in focus_rules
               if any(d.prop in ("outline", "outline-color", "outline-width", "box-shadow",
                                 "outline-offset", "border-color", "background", "background-color")
                      and d.value.strip().lower() not in ("none", "0")
                      for d in r.decls)]

    # Blosses `:focus` markiert zwar, rahmt aber auch den Mausklick. Warnung statt
    # Fehler: der Ring ist schwächer, nicht abwesend.
    for r in doc.rules:
        sel = r.selector
        if ":focus" not in sel or ":focus-visible" in sel or ":focus-within" in sel:
            continue
        styled = [d for d in r.decls
                  if (d.prop.startswith("outline") or d.prop.startswith("box-shadow"))
                  and d.value.strip().lower() not in ("none", "0", "0px")]
        if styled:
            rep.add("warnung", "fokus", doc.line(styled[0].offset),
                    f"`{sel.strip()}` benutzt `:focus` statt `:focus-visible`",
                    doc.snippet(styled[0].offset),
                    "`:focus-visible` rahmt Tastaturbedienung, ohne jeden Mausklick zu markieren")

    if not visible:
        rep.add("fehler", "fokus", 1,
                "interaktive Elemente vorhanden, aber keine sichtbare `:focus-visible`-Regel",
                "", "outline: var(--ac-focus-ring) solid var(--ac-accent); outline-offset: 2px")
    for d in doc.decls:
        if d.prop == "outline" and d.value.strip().lower() in ("none", "0", "0px"):
            if ":focus" in d.rule.selector and not any(
                    x.prop.startswith("box-shadow") or x.prop.startswith("border")
                    for x in d.rule.decls):
                rep.add("fehler", "fokus", doc.line(d.offset),
                        f"`outline: none` in `{d.rule.selector.strip()}` ohne Ersatzmarkierung",
                        doc.snippet(d.offset))
            elif ":focus" not in d.rule.selector and not visible:
                rep.add("warnung", "fokus", doc.line(d.offset),
                        f"`outline: none` in `{d.rule.selector.strip()}`",
                        doc.snippet(d.offset))


def _resolved_color(value, tokens, doc_vars, mode):
    """Farbe eines Deklarationswerts in Hell/Dunkel auflösen."""
    v = value.strip()
    if not v or v.lower() in COLOR_KEYWORDS_OK:
        return None
    seen = 0
    while "var(" in v and seen < 12:
        m = re.search(r"var\(\s*(--[\w-]+)\s*(?:,([^()]*))?\)", v)
        if not m:
            break
        name, fallback = m.group(1), (m.group(2) or "").strip()
        repl = doc_vars.get(mode, {}).get(name)
        if repl is None:
            repl = {"dark": tokens.dark, "print": tokens.print_}.get(
                mode, tokens.light).get(name)
        if repl is None:
            repl = fallback
        if repl is None or repl == "":
            return None
        v = v[:m.start()] + repl + v[m.end():]
        seen += 1
    colors = find_colors(v)
    return colors[0][0] if colors else None


def collect_doc_vars(doc):
    """Tokenwerte, wie das Dokument selbst sie setzt — hell, dunkel, Druck.

    Der Druckbereich braucht einen eigenen Topf: sonst landen die Überschreibungen
    aus `@media print` im hellen Modus und der Kontrast am Bildschirm würde gegen
    Papierwerte gerechnet — ein weißer Grund, den es dort nie gibt."""
    light, dark, printed = {}, {}, {}
    for rule in doc.rules:
        if rule.is_font_face():
            continue
        if rule.is_print_context():
            target = printed
        elif rule.is_dark_context():
            target = dark
        else:
            target = light
        for d in rule.decls:
            if d.prop.startswith("--"):
                target[d.prop] = d.value.strip()
    merged_dark = dict(light)
    merged_dark.update(dark)
    merged_print = dict(light)
    merged_print.update(printed)
    return {"light": light, "dark": merged_dark, "print": merged_print}


def check_contrast(doc, tokens, rep):
    """Kontrast der tatsächlich kombinierten Paare, hell und dunkel."""
    doc_vars = collect_doc_vars(doc)
    # Dunkel nur prüfen, wenn das Dokument überhaupt einen Dunkelmodus hat —
    # sonst würde ein bewusst helles Druckdokument gegen fremde Werte geprüft.
    modes = ["light"]
    if "prefers-color-scheme" in doc.css or "[data-theme" in doc.css.replace(" ", ""):
        modes.append("dark")
    # Druck ist ein eigener Modus, kein Sonderfall von hell: Regeln im
    # `@media print`-Block gelten nur dort und müssen gegen den Druckgrund
    # gemessen werden, nicht gegen den Bildschirmgrund.
    has_print = any(r.is_print_context() for r in doc.rules)
    if has_print:
        modes.append("print")
    page_bg = {}
    for mode in modes:
        bg = None
        for rule in doc.rules:
            sel = rule.selector.replace(" ", "").lower()
            if rule.is_print_context() and mode != "print":
                continue  # der Druckgrund ist nicht der Bildschirmgrund
            if sel.startswith("body") or sel in ("html", ":root") or ".wrap" in sel or ".sheet" in sel:
                if (mode == "dark") != rule.is_dark_context() and not (mode == "light" and not rule.is_dark_context()):
                    continue
                for prop in ("background", "background-color"):
                    d = rule.get(prop)
                    if d:
                        c = _resolved_color(d.value, tokens, doc_vars, mode)
                        if c:
                            bg = c
        if bg is None:
            fallback = {"dark": tokens.dark, "print": tokens.print_}.get(
                mode, tokens.light).get("--ac-paper-1")
            bg = find_colors(fallback)[0][0] if fallback and find_colors(fallback) else (255, 255, 255, 1.0)
        page_bg[mode] = bg

    # Der Seitengrund selbst kann halbtransparent sein; darunter liegt nur noch
    # die Leinwand des Browsers, und die ist weiß. Einmal opak gerechnet dient
    # er als Grund für alles Halbtransparente darüber — im Dunkelmodus ist das
    # ein dunkler Grund, nicht Weiß.
    page_bg_opaque = {m: (blend(c, (255, 255, 255)) if len(c) > 3 and c[3] < 1 else c[:3])
                      for m, c in page_bg.items()}

    seen = set()
    for rule in doc.rules:
        if rule.is_font_face() or rule.is_keyframes():
            continue
        cd = rule.get("color")
        if not cd:
            continue
        bgd = rule.get("background-color") or rule.get("background")
        size = rule_font_size_px(rule, tokens)
        weight = rule_font_weight(rule, tokens) or 400
        for mode in modes:
            if rule.is_dark_context() and mode == "light":
                continue
            # Druckregeln gelten nur im Druck; Bildschirmregeln gelten dort mit,
            # aber mit den Werten des Druckbereichs aufgelöst.
            if rule.is_print_context() and mode != "print":
                continue
            if rule.is_dark_context() and mode == "print":
                continue
            fg = _resolved_color(cd.value, tokens, doc_vars, mode)
            if not fg:
                continue
            bg = _resolved_color(bgd.value, tokens, doc_vars, mode) if bgd else None
            inherited = bg is None
            if inherited:
                bg_rgb = page_bg_opaque[mode]
            elif len(bg) > 3 and bg[3] < 1:
                bg_rgb = blend(bg, page_bg_opaque[mode])
            else:
                bg_rgb = bg[:3]
            fg_rgb = blend(fg, bg_rgb)
            ratio = contrast_ratio(fg_rgb, bg_rgb)
            key = (rule.selector.strip(), mode, round(ratio, 2))
            if key in seen:
                continue
            seen.add(key)
            large = (size is not None and (size >= 24 or (size >= 18.66 and weight >= 700)))
            floor = 3.0 if large else 4.5
            if ratio >= floor:
                continue
            label = {"light": "hell", "dark": "dunkel", "print": "druck"}[mode]
            where = f"{rule.selector.strip()} ({label})"
            detail = (f"{ratio:.2f}:1 gegen {floor}:1 — "
                      f"#{fg_rgb[0]:02X}{fg_rgb[1]:02X}{fg_rgb[2]:02X} auf "
                      f"#{bg_rgb[0]:02X}{bg_rgb[1]:02X}{bg_rgb[2]:02X}"
                      + (f", Schriftgröße {size:g}px" if size else ""))
            sev = "fehler" if not inherited else "warnung"
            hint = ("Hintergrund ist nicht im selben Block gesetzt, geprüft gegen den Seitengrund"
                    if inherited else "references/tokens.md, Abschnitt „Measured contrast“")
            rep.add(sev, "kontrast", doc.line(cd.offset),
                    f"{where}: {detail}", doc.snippet(cd.offset), hint)


CHECKS = [
    ("reines-schwarz-weiss", check_pure_black_white),
    ("box-shadow", check_box_shadow),
    ("farbe-ausserhalb-tokensatz", check_hex_off_token),
    ("token-abweichend", check_token_overrides),
    ("laufweite", check_letter_spacing),
    ("raster", check_spacing_grid),
    ("typo-skala", check_font_size_scale),
    ("rohwert-statt-token", check_raw_values),
    ("dark-mode", check_dark_mode),
    ("font-einbettung", check_font_embedding),
    ("zeichensatz", check_glyph_coverage),
    ("kontrast", check_contrast),
    ("gewicht", check_font_weight),
    ("radius", check_radius),
    ("linienstaerke", check_line_width),
    ("fokus", check_focus),
    ("zeichenkodierung", check_encoding),
    ("sprache", check_lang),
]


# --------------------------------------------------------------------------
# Ausgabe
# --------------------------------------------------------------------------

def render_text(path, rep, out):
    counts = rep.counts()
    out.write(f"\n{path}\n")
    out.write("─" * min(78, max(20, len(path))) + "\n")
    if not rep.findings:
        out.write(f"  keine Funde — sauber gegen alle {len(CHECKS)} Prüfungen.\n")
        return
    for sev in SEVERITIES:
        group = [f for f in rep.findings if f.severity == sev]
        if not group:
            continue
        out.write(f"\n{SEVERITY_LABEL[sev]} ({len(group)})\n")
        by_check = {}
        for f in group:
            by_check.setdefault(f.check, []).append(f)
        for check, items in by_check.items():
            items.sort(key=lambda f: f.line)
            shown = items[:MAX_PER_CHECK_TEXT]
            for f in shown:
                out.write(f"  Zeile {f.line:>5}  [{check}] {f.message}\n")
                if f.snippet:
                    out.write(f"                 │ {f.snippet}\n")
                if f.hint:
                    out.write(f"                 └ {f.hint}\n")
            if len(items) > len(shown):
                out.write(f"  … {len(items) - len(shown)} weitere [{check}] "
                          f"(vollständig mit --json)\n")
    out.write("\nZusammenfassung: "
              + plural(counts["fehler"], "Fehler", "Fehler") + ", "
              + plural(counts["warnung"], "Warnung", "Warnungen") + ", "
              + plural(counts["hinweis"], "Hinweis", "Hinweise") + "\n")


def plural(n, one, many):
    return f"{n} {one if n == 1 else many}"


def main(argv=None):
    ap = argparse.ArgumentParser(
        description=f"Regelprüfer für die Design Identity (design-identity {VERSION}).")
    ap.add_argument("files", nargs="+", metavar="datei.html")
    ap.add_argument("--json", action="store_true", dest="as_json",
                    help="Funde maschinenlesbar auf stdout")
    ap.add_argument("--tokens", metavar="tokens.css",
                    help="Pfad zu tokens.css (Standard: ../assets/tokens.css neben diesem Skript)")
    args = ap.parse_args(argv)

    tokens_path = find_tokens_css(args.tokens)
    if not tokens_path:
        sys.stderr.write("tokens.css nicht gefunden — mit --tokens den Pfad angeben.\n")
        return 2
    tokens = Tokens(tokens_path)

    results, exit_code = [], 0
    for path in args.files:
        rep = Report()
        if not os.path.isfile(path):
            rep.add("fehler", "datei", 1, f"Datei nicht gefunden: {path}")
        else:
            doc = Document(path)
            for _name, fn in CHECKS:
                fn(doc, tokens, rep)
        counts = rep.counts()
        if counts["fehler"]:
            exit_code = 1
        results.append({
            "file": path,
            "tokens": tokens_path,
            "summary": counts,
            "findings": [f.as_dict() for f in sorted(rep.findings,
                                                     key=lambda f: (SEVERITIES.index(f.severity), f.line))],
        })
        if not args.as_json:
            render_text(path, rep, sys.stdout)

    if args.as_json:
        json.dump(results if len(results) > 1 else results[0], sys.stdout,
                  ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    return exit_code


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:  # z. B. `lint.py … | head`
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        sys.exit(1)

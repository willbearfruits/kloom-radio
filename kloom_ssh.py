#!/usr/bin/env python3
"""
kloom_ssh.py  ─  Teletext SSH radio  ─  Kloom Lo Kadosh
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Run:     python3 kloom_ssh.py [--port N]
  Connect: ssh -p 2222 localhost        (no auth required)
  Deploy:  long-lived process on a VPS, expose port 2222.
"""

import asyncio, asyncssh, json, os, sys, random, time, re
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote
from datetime import datetime

# ─── config ───────────────────────────────────────────────────────────────────
BASE_DIR  = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "shows.json"
HOST_KEY  = BASE_DIR / ".kloom_ssh_host_key"
W         = 80                            # full terminal width

PORT = 2222
if "--port" in sys.argv:
    PORT = int(sys.argv[sys.argv.index("--port") + 1])

# ─── ANSI (256 color + effects) ──────────────────────────────────────────────
class A:
    R   = "\033[0m"
    B   = "\033[1m"
    DIM = "\033[2m"
    IT  = "\033[3m"
    UL  = "\033[4m"
    BLK = "\033[5m"   # blink (terminal support varies)
    REV = "\033[7m"

    # standard colors
    RD = "\033[31m"; GR = "\033[32m"; YL = "\033[33m"
    BL = "\033[34m"; MG = "\033[35m"; CY = "\033[36m"; WH = "\033[37m"

    # bright colors
    BRD = "\033[91m"; BGR = "\033[92m"; BYL = "\033[93m"
    BBL = "\033[94m"; BMG = "\033[95m"; BCY = "\033[96m"; BWH = "\033[97m"

    # backgrounds
    bK  = "\033[40m"; bR  = "\033[41m"; bG  = "\033[42m"; bY  = "\033[43m"
    bB  = "\033[44m"; bM  = "\033[45m"; bC  = "\033[46m"; bW  = "\033[47m"

    # 256 color helpers
    @staticmethod
    def fg(n): return f"\033[38;5;{n}m"
    @staticmethod
    def bg(n): return f"\033[48;5;{n}m"

    # control
    CLR = "\033[2J\033[H"
    HID = "\033[?25l"; SHW = "\033[?25h"

    # cursor movement
    @staticmethod
    def goto(r, c): return f"\033[{r};{c}H"

    # OSC 8 hyperlinks (clickable in supporting terminals)
    @staticmethod
    def link(url, text): return f"\033]8;;{url}\033\\{text}\033]8;;\033\\"

# ─── glitch characters ───────────────────────────────────────────────────────
GLITCH_CHARS = "█▓▒░╔╗╚╝║═╬╣╠╩╦▀▄▌▐■□▪▫●○◘◙◄►▲▼←→↑↓↔↕∞≈≠±×÷ΩπΣ"
STATIC_CHARS = ".:;!|/\\-_=+*#@%&$?"

# ─── ASCII art logo ──────────────────────────────────────────────────────────
LOGO = r"""
██╗  ██╗██╗      ██████╗  ██████╗ ███╗   ███╗
██║ ██╔╝██║     ██╔═══██╗██╔═══██╗████╗ ████║
█████╔╝ ██║     ██║   ██║██║   ██║██╔████╔██║
██╔═██╗ ██║     ██║   ██║██║   ██║██║╚██╔╝██║
██║  ██╗███████╗╚██████╔╝╚██████╔╝██║ ╚═╝ ██║
╚═╝  ╚═╝╚══════╝ ╚═════╝  ╚═════╝ ╚═╝     ╚═╝
"""

SUBTITLE = "L O   K A D O S H   //   N O T H I N G   I S   H O L Y"

# mini logo for headers
MINI_LOGO = "◢◤ KLOOM ◥◣"

# ─── box drawing ─────────────────────────────────────────────────────────────
BOX = {
    'tl': '╔', 'tr': '╗', 'bl': '╚', 'br': '╝',
    'h': '═', 'v': '║',
    'lt': '╠', 'rt': '╣', 'tt': '╦', 'bt': '╩', 'x': '╬',
    # rounded
    'rtl': '╭', 'rtr': '╮', 'rbl': '╰', 'rbr': '╯',
    # single
    'stl': '┌', 'str': '┐', 'sbl': '└', 'sbr': '┘', 'sh': '─', 'sv': '│',
}

# ─── visualizer bars ─────────────────────────────────────────────────────────
VU_CHARS = " ▁▂▃▄▅▆▇█"

def vu_bar(level, width=8):
    """Generate a VU meter bar."""
    full = int(level * width)
    bars = ""
    for i in range(width):
        if i < full:
            if i < width * 0.5:
                bars += A.GR + "█"
            elif i < width * 0.75:
                bars += A.YL + "█"
            else:
                bars += A.RD + "█"
        else:
            bars += A.fg(236) + "░"
    return bars + A.R

def random_vu():
    """Generate random VU levels for fake visualizer."""
    return [random.random() * 0.3 + 0.1 + (0.5 if random.random() > 0.7 else 0) for _ in range(8)]

# ─── data ────────────────────────────────────────────────────────────────────
with open(DATA_FILE, encoding="utf-8") as _fh:
    SHOWS = sorted(json.load(_fh), key=lambda s: s["date"], reverse=True)

_SECTIONS = [
    ("KLOOM ORIGINALS",  lambda s: s["series"] in ("Kloom Lo Kadosh", "Radio Art 106")),
    ("NOTHING IS HOLY",  lambda s: s["series"] == "Nothing Is Holy"),
    ("KOL HAZUTI",       lambda s: s["series"] == "Kol Hazuti"),
]

FLAT: list = []
for _t, _p in _SECTIONS:
    _h = [s for s in SHOWS if _p(s)]
    if _h:
        FLAT.append(("h", _t))
        FLAT.extend(("s", s) for s in _h)

SHOW_IDXS  = [i for i, (k, _) in enumerate(FLAT) if k == "s"]
SHOW_COUNT = len(SHOW_IDXS)

_BADGE = {
    "local_audio": ("●", A.BGR),
    "embed":       ("◆", A.BMG),
    "youtube":     ("▶", A.BRD),
}

def _listen_url(show):
    if show["type"] == "local_audio":
        return f"https://willbearfruits.github.io/kloom-radio/shows/{show['id']}.html"
    if show["type"] == "embed":
        q = parse_qs(urlparse(show["embed_url"]).query)
        if "feed" in q:
            return "https://www.mixcloud.com" + unquote(q["feed"][0])
        return show["embed_url"]
    if show["type"] == "youtube":
        return "https://www.youtube.com/watch?v=" + show["embed_url"].rstrip("/").split("/")[-1]
    return None

# ─── shared state ────────────────────────────────────────────────────────────
_now_playing = None
_listeners   = 0
_start_time  = time.time()

# ─── teletext helpers ────────────────────────────────────────────────────────
def glitch_text(text, intensity=0.1):
    """Add random glitch characters to text."""
    result = ""
    for c in text:
        if random.random() < intensity:
            result += random.choice(GLITCH_CHARS)
        else:
            result += c
    return result

def static_line(width, intensity=0.3):
    """Generate a line of static."""
    return "".join(
        A.fg(random.randint(232, 255)) + random.choice(STATIC_CHARS)
        if random.random() < intensity else " "
        for _ in range(width)
    ) + A.R

def scanline():
    """Horizontal scanline effect."""
    return A.fg(236) + "─" * W + A.R

def box_top(title="", color=A.MG, width=W):
    """Draw box top with optional centered title."""
    if title:
        title = f" {title} "
        side = (width - len(title) - 2) // 2
        return color + BOX['tl'] + BOX['h'] * side + A.R + A.B + A.YL + title + A.R + color + BOX['h'] * (width - side - len(title) - 2) + BOX['tr'] + A.R
    return color + BOX['tl'] + BOX['h'] * (width - 2) + BOX['tr'] + A.R

def box_mid(content="", color=A.MG, width=W, align="left"):
    """Draw box middle row."""
    # strip ANSI for length calculation
    visible = re.sub(r'\033\[[0-9;]*m', '', content)
    padding = width - len(visible) - 2
    if align == "center":
        left_pad = padding // 2
        right_pad = padding - left_pad
        inner = " " * left_pad + content + " " * right_pad
    elif align == "right":
        inner = " " * (padding - 1) + content + " "
    else:
        inner = " " + content + " " * (padding - 1)
    return color + BOX['v'] + A.R + inner + color + BOX['v'] + A.R

def box_bot(color=A.MG, width=W):
    """Draw box bottom."""
    return color + BOX['bl'] + BOX['h'] * (width - 2) + BOX['br'] + A.R

def box_divider(color=A.MG, width=W):
    """Draw box divider."""
    return color + BOX['lt'] + BOX['h'] * (width - 2) + BOX['rt'] + A.R

def progress_bar(value, width=20, filled_color=A.BGR, empty_color=A.fg(236)):
    """Draw a progress bar."""
    filled = int(value * width)
    return (filled_color + "█" * filled + empty_color + "░" * (width - filled) + A.R)

def time_display():
    """Current time in retro format."""
    now = datetime.now()
    return f"{A.fg(208)}{now.strftime('%H:%M:%S')}{A.R}"

def uptime_display():
    """Server uptime."""
    elapsed = int(time.time() - _start_time)
    h, m, s = elapsed // 3600, (elapsed % 3600) // 60, elapsed % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

# ─── pages ───────────────────────────────────────────────────────────────────
def page_splash(frame=0):
    L = []

    # top border with glitch
    L.append(A.MG + "█" * W + A.R)

    # static line
    L.append(static_line(W, 0.15))

    # logo with color cycling
    colors = [A.BMG, A.BCY, A.BGR, A.BYL, A.BWH]
    for i, line in enumerate(LOGO.strip().split('\n')):
        color = colors[(i + frame) % len(colors)]
        padding = (W - len(line)) // 2
        L.append(" " * padding + color + line + A.R)

    # subtitle with flicker
    sub_color = A.YL if frame % 3 != 0 else A.fg(172)
    L.append((" " * ((W - len(SUBTITLE)) // 2)) + sub_color + A.B + SUBTITLE + A.R)

    # static line
    L.append(static_line(W, 0.15))
    L.append("")

    # now playing box
    if _now_playing:
        L.append(box_top("▶ NOW PLAYING", A.GR))
        L.append(box_mid(A.BWH + A.B + _now_playing["title"][:W-6] + A.R, A.GR))
        L.append(box_mid(A.CY + _now_playing["series"] + " // " + _now_playing["date"], A.GR))

        # fake VU meters
        vu_levels = random_vu()
        vu_display = "  ".join(vu_bar(l, 4) for l in vu_levels)
        L.append(box_mid(vu_display, A.GR, align="center"))

        url = _listen_url(_now_playing)
        if url:
            clickable = A.link(url, A.UL + A.BCY + url[:W-6] + A.R)
            L.append(box_mid(clickable, A.GR))
        L.append(box_bot(A.GR))
    else:
        L.append(box_top("◇ SILENCE", A.fg(240)))
        L.append(box_mid(A.fg(245) + "nothing playing...", A.fg(240)))
        L.append(box_mid(A.fg(240) + "browse the archive to tune in", A.fg(240)))
        L.append(box_bot(A.fg(240)))

    L.append("")

    # menu box
    L.append(box_top("MENU", A.MG))
    menu_bar = f"{A.fg(240)}{'━' * 35}"
    L.append(box_mid(f"{A.YL}[1]{A.R} {A.BWH}BROWSE ARCHIVE{A.R}   {menu_bar}", A.MG))
    L.append(box_mid(f"{A.CY}[2]{A.R} {A.WH}ABOUT{A.R}            {menu_bar}", A.MG))
    L.append(box_mid(f"{A.GR}[3]{A.R} {A.WH}HELP{A.R}             {menu_bar}", A.MG))
    L.append(box_bot(A.MG))

    L.append("")

    # status bar
    listeners_txt = f"{_listeners} listener{'s' if _listeners != 1 else ''}"
    status = f"{A.fg(240)}╾{'─' * (W - 2)}╼{A.R}"
    L.append(status)
    L.append(f"  {A.GR}●{A.R} {A.fg(245)}SYSTEM ONLINE{A.R}    {time_display()}    {A.CY}⚡{A.R} {A.fg(245)}{listeners_txt}{A.R}    {A.MG}↑{A.R} {A.fg(245)}{uptime_display()}{A.R}")

    # footer
    L.append(A.fg(240) + "─" * W + A.R)
    L.append(f"  {A.fg(245)}[Q] quit{A.R}")
    L.append(A.MG + "█" * W + A.R)

    return "\n".join(L)

def page_archive(sel, scroll_offset=0):
    L = []

    # header
    L.append(A.MG + "█" * W + A.R)
    L.append(box_mid(f"{A.BMG}{MINI_LOGO}{A.R}  {A.B}{A.YL}ARCHIVE{A.R}  {A.fg(245)}[{len(SHOWS)} shows]{A.R}", A.MG, align="center"))
    L.append(A.MG + "█" * W + A.R)
    L.append("")

    # calculate visible range (max ~15 items visible)
    max_visible = 15
    show_i = 0
    visible_items = []

    for kind, val in FLAT:
        if kind == "h":
            visible_items.append(("h", val, -1))
        else:
            visible_items.append(("s", val, show_i))
            show_i += 1

    # adjust scroll to keep selection visible
    sel_pos = next((i for i, (k, v, idx) in enumerate(visible_items) if k == "s" and idx == sel), 0)
    if sel_pos < scroll_offset:
        scroll_offset = sel_pos
    elif sel_pos >= scroll_offset + max_visible:
        scroll_offset = sel_pos - max_visible + 1

    # render visible items
    for i, (kind, val, idx) in enumerate(visible_items[scroll_offset:scroll_offset + max_visible]):
        if kind == "h":
            # section header
            L.append(f"  {A.MG}{A.B}┌{'─' * (len(val) + 2)}┐{A.R}")
            L.append(f"  {A.MG}{A.B}│ {A.YL}{val}{A.MG} │{A.R}")
            L.append(f"  {A.MG}{A.B}└{'─' * (len(val) + 2)}┘{A.R}")
        else:
            active = (idx == sel)
            badge_char, badge_color = _BADGE.get(val["type"], ("?", A.WH))

            if active:
                # selected item - full highlight
                L.append(f"  {A.BGR}▶{A.R} {A.bM}{A.BWH}{A.B} {val['title'][:W-14]} {A.R} {badge_color}{badge_char}{A.R}")
                L.append(f"    {A.CY}{val['series']}{A.R} {A.fg(240)}// {val['date']}{A.R}")
            else:
                L.append(f"    {A.YL}{val['title'][:W-12]}{A.R} {badge_color}{badge_char}{A.R}")

    # scroll indicators
    if scroll_offset > 0:
        L.insert(4, f"  {A.fg(245)}↑ more above{A.R}")
    if scroll_offset + max_visible < len(visible_items):
        L.append(f"  {A.fg(245)}↓ more below{A.R}")

    L.append("")
    L.append(A.fg(240) + "─" * W + A.R)
    L.append(f"  {A.fg(245)}[↑↓] navigate  [ENTER] select  [ESC] back  [Q] quit{A.R}")
    L.append(A.MG + "█" * W + A.R)

    return "\n".join(L), scroll_offset

def page_detail(show, frame=0, show_url_popup=False):
    L = []

    # URL popup overlay
    if show_url_popup:
        url = _listen_url(show)
        L.append("")
        L.append(A.MG + "█" * W + A.R)
        L.append(box_top("LISTEN URL", A.BGR))
        L.append(box_mid("", A.BGR))
        L.append(box_mid(f"{A.BWH}{A.B}Copy this URL to listen:{A.R}", A.BGR, align="center"))
        L.append(box_mid("", A.BGR))
        if url:
            # Show URL in a way that's easy to triple-click select
            clickable = A.link(url, A.UL + A.BCY + url + A.R)
            L.append(box_mid(clickable, A.BGR, align="center"))
            L.append(box_mid("", A.BGR))
            L.append(box_mid(f"{A.fg(245)}(triple-click to select, or Cmd/Ctrl+click to open){A.R}", A.BGR, align="center"))
        else:
            L.append(box_mid(f"{A.RD}No URL available{A.R}", A.BGR, align="center"))
        L.append(box_mid("", A.BGR))
        L.append(box_bot(A.BGR))
        L.append("")
        L.append(f"  {A.fg(245)}[O] close  [ESC] back{A.R}")
        L.append(A.MG + "█" * W + A.R)
        return "\n".join(L)

    # header
    L.append(A.MG + "█" * W + A.R)
    badge_char, badge_color = _BADGE.get(show["type"], ("?", A.WH))
    L.append(box_mid(f"{badge_color}{badge_char}{A.R}  {A.B}{A.YL}{show['title'][:W-10]}{A.R}", A.MG, align="center"))
    L.append(A.MG + "█" * W + A.R)
    L.append("")

    # metadata box
    L.append(box_top("INFO", A.CY))
    L.append(box_mid(f"{A.fg(245)}Series:{A.R}  {A.BWH}{show['series']}{A.R}", A.CY))
    L.append(box_mid(f"{A.fg(245)}Date:{A.R}    {A.WH}{show['date']}{A.R}", A.CY))

    if show.get("guest"):
        L.append(box_mid(f"{A.fg(245)}Guest:{A.R}   {A.BGR}{show['guest']}{A.R}", A.CY))
    if show.get("host"):
        L.append(box_mid(f"{A.fg(245)}Host:{A.R}    {A.BCY}{show['host']}{A.R}", A.CY))

    L.append(box_bot(A.CY))
    L.append("")

    # tags
    tags = show.get("tags", [])[:6]
    if tags:
        tag_line = "  ".join(f"{A.bg(236)}{A.BWH} #{t} {A.R}" for t in tags)
        L.append(f"  {tag_line}")
        L.append("")

    # description
    desc = (show.get("description") or "No description.").replace("\n", " ")
    words = desc.split()
    lines = []
    current = ""
    for word in words:
        test = (current + " " + word).strip()
        if len(test) <= W - 6:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)

    L.append(box_top("DESCRIPTION", A.fg(240)))
    for line in lines[:6]:  # max 6 lines
        L.append(box_mid(A.fg(250) + line, A.fg(240)))
    if len(lines) > 6:
        L.append(box_mid(A.fg(240) + "...", A.fg(240)))
    L.append(box_bot(A.fg(240)))
    L.append("")

    # listen URL - clickable!
    url = _listen_url(show)
    if url:
        L.append(f"  {A.fg(245)}Listen:{A.R}")
        clickable = A.link(url, A.UL + A.BCY + url[:W-4] + A.R)
        L.append(f"  {clickable}")
        L.append(f"  {A.fg(240)}(click link or Cmd/Ctrl+click in terminal){A.R}")
        L.append("")

    # tune-in button
    is_on = _now_playing and _now_playing["id"] == show["id"]
    if is_on:
        pulse = "▓" if frame % 2 == 0 else "█"
        L.append(f"  {A.bG}{A.B}{A.WH} {pulse} TUNED IN {pulse} {A.R}  {A.fg(245)}[T] to untune{A.R}")
    else:
        L.append(f"  {A.bM}{A.B}{A.BWH}   ▶ TUNE IN   {A.R}  {A.fg(245)}[T] to tune{A.R}")

    L.append("")
    L.append(A.fg(240) + "─" * W + A.R)
    L.append(f"  {A.fg(245)}[T] tune/untune  [O] copy URL  [ESC] back  [Q] quit{A.R}")
    L.append(A.MG + "█" * W + A.R)

    return "\n".join(L)

def page_about(frame=0):
    L = []

    L.append(A.MG + "█" * W + A.R)
    L.append(box_mid(f"{A.BMG}{MINI_LOGO}{A.R}  {A.B}{A.YL}ABOUT{A.R}", A.MG, align="center"))
    L.append(A.MG + "█" * W + A.R)
    L.append("")

    about_text = [
        (A.BWH, "KLOOM LO KADOSH is an underground"),
        (A.BWH, "radio archive."),
        ("", ""),
        (A.CY, "Experimental sound. Noise."),
        (A.CY, "Conversations."),
        ("", ""),
        (A.fg(245), "Hosted out of the void by"),
        (A.BGR, "Yaniv Schonfeld"),
        (A.fg(245), "and whoever else shows up."),
        ("", ""),
        (A.YL + A.B, "Nothing is Holy."),
        (A.MG, "The signal is the message."),
        ("", ""),
        (A.fg(240), "─" * 50),
        ("", ""),
        (A.fg(245), "This archive collects broadcasts,"),
        (A.fg(245), "mixtapes, and transmissions from"),
        (A.fg(245), "the edges — things that don't fit"),
        (A.fg(245), "anywhere else."),
        ("", ""),
        (A.GR, "All frequencies welcome."),
    ]

    for color, line in about_text:
        if line:
            L.append(f"  {color}{line}{A.R}")
        else:
            L.append("")

    L.append("")
    L.append(A.fg(240) + "─" * W + A.R)
    L.append(f"  {A.fg(245)}[ESC] back  [Q] quit{A.R}")
    L.append(A.MG + "█" * W + A.R)

    return "\n".join(L)

def page_help():
    L = []

    L.append(A.MG + "█" * W + A.R)
    L.append(box_mid(f"{A.BMG}{MINI_LOGO}{A.R}  {A.B}{A.YL}HELP{A.R}", A.MG, align="center"))
    L.append(A.MG + "█" * W + A.R)
    L.append("")

    L.append(box_top("NAVIGATION", A.CY))
    L.append(box_mid(f"{A.YL}↑ ↓{A.R}        Move up/down", A.CY))
    L.append(box_mid(f"{A.YL}ENTER{A.R}      Select item", A.CY))
    L.append(box_mid(f"{A.YL}ESC{A.R}        Go back", A.CY))
    L.append(box_mid(f"{A.YL}← →{A.R}        Also go back", A.CY))
    L.append(box_bot(A.CY))
    L.append("")

    L.append(box_top("PLAYBACK", A.GR))
    L.append(box_mid(f"{A.YL}T{A.R}          Tune in to show", A.GR))
    L.append(box_mid(f"{A.fg(245)}             (sets 'now playing' for all){A.R}", A.GR))
    L.append(box_bot(A.GR))
    L.append("")

    L.append(box_top("QUICK KEYS", A.MG))
    L.append(box_mid(f"{A.YL}1{A.R}          Archive", A.MG))
    L.append(box_mid(f"{A.YL}2{A.R}          About", A.MG))
    L.append(box_mid(f"{A.YL}3{A.R}          This help", A.MG))
    L.append(box_mid(f"{A.YL}Q{A.R}          Quit", A.MG))
    L.append(box_bot(A.MG))
    L.append("")

    L.append(box_top("SHOW TYPES", A.fg(245)))
    L.append(box_mid(f"{A.BGR}●{A.R}  Local audio (in-browser player)", A.fg(245)))
    L.append(box_mid(f"{A.BMG}◆{A.R}  Mixcloud embed", A.fg(245)))
    L.append(box_mid(f"{A.BRD}▶{A.R}  YouTube embed", A.fg(245)))
    L.append(box_bot(A.fg(245)))

    L.append("")
    L.append(A.fg(240) + "─" * W + A.R)
    L.append(f"  {A.fg(245)}[ESC] back  [Q] quit{A.R}")
    L.append(A.MG + "█" * W + A.R)

    return "\n".join(L)

def page_intro(frame):
    """Boot sequence animation."""
    L = []

    if frame < 3:
        # blank with static
        for _ in range(20):
            L.append(static_line(W, 0.8 - frame * 0.2))
    elif frame < 6:
        # logo fade in
        intensity = (frame - 3) / 3
        L.append("")
        for line in LOGO.strip().split('\n'):
            if random.random() < intensity:
                padding = (W - len(line)) // 2
                L.append(" " * padding + A.MG + line + A.R)
            else:
                L.append(static_line(W, 0.3))
    elif frame < 8:
        # full logo
        L.append("")
        for i, line in enumerate(LOGO.strip().split('\n')):
            padding = (W - len(line)) // 2
            L.append(" " * padding + A.BMG + line + A.R)
        L.append("")
        L.append((" " * ((W - len(SUBTITLE)) // 2)) + A.YL + A.B + SUBTITLE + A.R)
    else:
        return None  # done with intro

    L.append("")
    L.append(f"  {A.GR}{'█' * (frame * 4)}{A.fg(236)}{'░' * (32 - frame * 4)}{A.R}")
    L.append(f"  {A.fg(245)}INITIALIZING...{A.R}")

    return "\n".join(L)

# ─── input parsing ───────────────────────────────────────────────────────────
_ARROWS = {b"\x1b[A", b"\x1b[B", b"\x1b[C", b"\x1b[D"}

def _parse_all(raw: bytes) -> list:
    keys, i = [], 0
    while i < len(raw):
        if raw[i:i+1] == b"\x1b" and raw[i+1:i+2] == b"[" and raw[i+2:i+3].isalpha():
            seq = raw[i:i+3]
            keys.append(seq if seq in _ARROWS else b"\x1b")
            i += 3 if seq in _ARROWS else 1
        else:
            keys.append(raw[i:i+1])
            i += 1
    return keys

# ─── session ─────────────────────────────────────────────────────────────────
class Session:
    __slots__ = ("proc", "state", "sel", "detail", "frame", "scroll_offset", "intro_done", "show_url_popup")

    def __init__(self, proc):
        self.proc   = proc
        self.state  = "intro"
        self.sel    = 0
        self.detail = None
        self.frame  = 0
        self.scroll_offset = 0
        self.intro_done = False
        self.show_url_popup = False

    def _draw(self):
        if self.state == "intro":
            page = page_intro(self.frame)
            if page is None:
                self.state = "splash"
                self.intro_done = True
                page = page_splash(self.frame)
        elif self.state == "archive":
            page, self.scroll_offset = page_archive(self.sel, self.scroll_offset)
        elif self.state == "detail":
            page = page_detail(self.detail, self.frame, self.show_url_popup)
        elif self.state == "about":
            page = page_about(self.frame)
        elif self.state == "help":
            page = page_help()
        else:
            page = page_splash(self.frame)
        self.proc.stdout.write(A.CLR + A.bK + A.HID + page)
        self.frame += 1

    def _key(self, k: bytes) -> bool:
        if k in (b"q", b"Q"):
            return False

        if self.state == "intro":
            # skip intro
            self.state = "splash"
            self.intro_done = True

        elif self.state == "splash":
            if k in (b"1", b"\r", b"\n", b"\x1b[B", b"\x1b[C"):  # 1, enter, down, right
                self.state = "archive"
            elif k == b"2":
                self.state = "about"
            elif k == b"3":
                self.state = "help"
            elif k in (b"\x1b[A", b"\x1b[D"):  # up, left - cycle menu
                pass  # stay on splash

        elif self.state == "archive":
            if k == b"\x1b[A":
                self.sel = (self.sel - 1) % SHOW_COUNT
            elif k == b"\x1b[B":
                self.sel = (self.sel + 1) % SHOW_COUNT
            elif k in (b"\r", b"\n", b"\x1b[C"):  # enter or right arrow
                self.detail = FLAT[SHOW_IDXS[self.sel]][1]
                self.state  = "detail"
                self.show_url_popup = False
            elif k in (b"\x1b", b"\x1b[D"):  # esc or left arrow
                self.state = "splash"

        elif self.state == "detail":
            if k in (b"t", b"T"):
                global _now_playing
                if _now_playing and _now_playing["id"] == self.detail["id"]:
                    _now_playing = None
                else:
                    _now_playing = self.detail
            elif k in (b"o", b"O"):
                self.show_url_popup = not self.show_url_popup
            elif k in (b"\x1b", b"\x1b[D"):
                self.state = "archive"
                self.show_url_popup = False

        elif self.state == "about":
            if k in (b"\x1b", b"\x1b[D"):
                self.state = "splash"

        elif self.state == "help":
            if k in (b"\x1b", b"\x1b[D"):
                self.state = "splash"

        return True

    async def run(self):
        global _listeners
        _listeners += 1
        self._draw()
        try:
            while True:
                try:
                    raw = await asyncio.wait_for(
                        self.proc.stdin.read(16), timeout=0.5 if self.state in ("intro", "splash", "detail") else 5.0
                    )
                except asyncio.TimeoutError:
                    self._draw()
                    continue

                if not raw:
                    break

                if isinstance(raw, str):
                    raw = raw.encode()

                if raw == b"\x1b":
                    try:
                        more = await asyncio.wait_for(
                            self.proc.stdin.read(4), timeout=0.1
                        )
                        if more:
                            raw += more if isinstance(more, bytes) else more.encode()
                    except asyncio.TimeoutError:
                        pass

                alive = True
                for k in _parse_all(raw):
                    if not self._key(k):
                        alive = False
                        break
                if not alive:
                    break
                self._draw()

        except (asyncio.CancelledError, ConnectionError, OSError):
            pass
        finally:
            _listeners -= 1
            try:
                self.proc.stdout.write(A.SHW + A.CLR)
                self.proc.exit(0)
            except Exception:
                pass

# ─── SSH server ──────────────────────────────────────────────────────────────
class _Server(asyncssh.SSHServer):
    def connection_made(self, conn):
        peer = conn.get_extra_info("peername", ("?", 0))
        print(f"  {A.GR}+{A.R} {peer[0]}", flush=True)

    def connection_lost(self, exc):
        print(f"  {A.RD}-{A.R} disconnected", flush=True)

    def begin_auth(self, username):
        return False

async def _process(proc):
    chan = getattr(proc, '_chan', None)
    if chan:
        if hasattr(chan, 'set_echo'):
            chan.set_echo(False)
        if hasattr(chan, 'set_line_mode'):
            chan.set_line_mode(False)
    await Session(proc).run()

# ─── main ────────────────────────────────────────────────────────────────────
BANNER = f"""
{A.MG}╔══════════════════════════════════════════════════════════════════════════════╗
║{A.R}  {A.BMG}◢◤{A.R} {A.B}{A.YL}KLOOM LO KADOSH{A.R} {A.BMG}◥◣{A.R}  {A.fg(245)}SSH Radio Server{A.R}                                     {A.MG}║
╚══════════════════════════════════════════════════════════════════════════════╝{A.R}
"""

async def main():
    if not HOST_KEY.exists():
        print(f"{A.YL}Generating host key → {HOST_KEY}{A.R}")
        asyncssh.generate_private_key("ssh-ed25519").write_private_key(str(HOST_KEY))
        os.chmod(str(HOST_KEY), 0o600)

    print(BANNER)

    srv = await asyncssh.create_server(
        _Server, "", PORT,
        server_host_keys=[str(HOST_KEY)],
        process_factory=_process,
    )

    print(f"  {A.GR}●{A.R} Listening on port {A.BWH}{PORT}{A.R}")
    print(f"  {A.CY}→{A.R} ssh -o StrictHostKeyChecking=no -p {PORT} localhost")
    print(f"  {A.fg(245)}Press Ctrl+C to stop{A.R}")
    print()

    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, asyncio.CancelledError):
        print(f"\n  {A.YL}Shutting down...{A.R}")
        srv.close()
        await srv.wait_closed()
        print(f"  {A.fg(245)}Goodbye.{A.R}")

if __name__ == "__main__":
    asyncio.run(main())

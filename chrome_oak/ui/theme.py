"""Look and feel: colours, icons, decorations, and the CSS loaders.

CSS lives in files, not here:
  ui/styles/base.css    universal (every page)
  ui/styles/frame.css   sidebar + headings (every page except Welcome)
  ui/styles/pages/<page>.css   that page only, loaded by inject_page_css(__file__)
"""

from pathlib import Path

import streamlit as st

from chrome_oak.ui.mascots import MASCOT_CSS

INK, MUT, LINE, OAK, OAKD = "#2A2420", "#565B62", "#DDE0E4", "#8B5E3C", "#5E3B22"
HL = "#D9692B"  # highlighted bar colour (orange-oak)

LEAF = ('<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#8B5E3C" stroke-width="2" '
        'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M11 20A7 7 0 0 1 4 13c0-6 7-10 16-10-1 9-5 16-9 17z"/>'
        '<path d="M4 21c4-6 8-9 12-11"/></svg>')
DAISY = ('<svg class="daisy" width="{s}" height="{s}" viewBox="0 0 100 100" aria-hidden="true"><g fill="#FFFFFF">'
         '<ellipse cx="50" cy="20" rx="11" ry="20"/><ellipse cx="50" cy="80" rx="11" ry="20"/><ellipse cx="20" cy="50" rx="20" ry="11"/>'
         '<ellipse cx="80" cy="50" rx="20" ry="11"/><ellipse cx="29" cy="29" rx="11" ry="20" transform="rotate(-45 29 29)"/>'
         '<ellipse cx="71" cy="71" rx="11" ry="20" transform="rotate(-45 71 71)"/><ellipse cx="71" cy="29" rx="11" ry="20" transform="rotate(45 71 29)"/>'
         '<ellipse cx="29" cy="71" rx="11" ry="20" transform="rotate(45 29 71)"/></g><circle cx="50" cy="50" r="14" fill="#D4A84A"/></svg>')
SPARK = ('<svg class="sparkle" style="{pos}" width="{s}" height="{s}" viewBox="0 0 24 24" aria-hidden="true">'
         '<path d="M12 0 L14 10 L24 12 L14 14 L12 24 L10 14 L0 12 L10 10 Z" fill="#FFFFFF"/></svg>')


ICONS = {
    "home": '<path d="M3 11l9-8 9 8"/><path d="M5 10v10h14V10"/>',
    "chart": '<path d="M4 20V10"/><path d="M10 20V4"/><path d="M16 20v-7"/><path d="M22 20H2"/>',
    "data": '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v6c0 1.7 3.6 3 8 3s8-1.3 8-3V5"/><path d="M4 11v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6"/>',
    "bulb": '<path d="M9 18h6"/><path d="M10 22h4"/><path d="M12 2a7 7 0 0 0-4 12.7V16h8v-1.3A7 7 0 0 0 12 2z"/>',
    "bell": '<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10 21a2 2 0 0 0 4 0"/>',
    "log": '<path d="M8 6h13M8 12h13M8 18h13"/><path d="M3 6h.01M3 12h.01M3 18h.01"/>',
    "list": '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 10h18M9 4v16"/>',
    "check": '<path d="M20 6L9 17l-5-5"/>',
    "send": '<path d="M22 2L11 13"/><path d="M22 2l-7 20-4-9-9-4 20-7z"/>',
}


def icon(name, color=MUT, size=18, width=2):
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="{width}" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS[name]}</svg>')


STYLES = Path(__file__).parent / "styles"


def _style(path):
    st.markdown(f"<style>{path.read_text()}</style>", unsafe_allow_html=True)


def inject_theme():
    """Universal CSS + the mascots' animations. Called once by app.py."""
    _style(STYLES / "base.css")
    st.markdown(MASCOT_CSS, unsafe_allow_html=True)


def inject_frame():
    """Sidebar and page-heading CSS for the dashboard pages."""
    _style(STYLES / "frame.css")


def inject_page_css(page_file):
    """Load styles/pages/<page>.css for a page module (e.g. pages/alerts.py -> styles/pages/alerts.css), if it exists."""
    css = STYLES / "pages" / f"{Path(page_file).stem}.css"
    if css.exists():
        _style(css)

"""Look and feel: colours, CSS, icons and the little decorations (Chrome-led: light grey, silver, oak)."""

import streamlit as st

from chrome_oak.ui.mascots import MASCOT_CSS

INK, MUT, LINE, OAK, OAKD = "#2A2420", "#565B62", "#DDE0E4", "#8B5E3C", "#5E3B22"
HL = "#D9692B"  # highlighted bar colour (orange-oak)

# Base theme, used on every page (welcome included)
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Alfa+Slab+One&family=Nunito:wght@400;600;700;800&display=swap');
.stApp{background:#F4F5F7}
html, body, .stMarkdown, p, li, label, button, input{font-family:'Nunito',sans-serif;color:#2A2420}
h1, h2, h3{font-family:'Alfa Slab One',serif !important;font-weight:400 !important;color:#2A2420 !important}
.block-container{padding-top:1.4rem;padding-bottom:4rem;max-width:1180px}
header[data-testid="stHeader"]{background:transparent}

/* sidebar = brushed chrome */
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#F1F3F5 0%,#D9DCE0 55%,#C9CDD2 100%);border-right:1px solid #B9BFC6}
section[data-testid="stSidebar"] *{color:#2A2420}
.logo{display:flex;align-items:center;gap:8px;font-family:'Alfa Slab One',serif;font-size:21px;color:#5E3B22 !important;margin:4px 0 18px}
.navlbl{font-size:11px;font-weight:800;letter-spacing:1.5px;text-transform:uppercase;color:#565B62 !important;margin:4px 0 8px 14px}
.simnote{font-size:13px;color:#565B62 !important;line-height:1.45;padding:0 6px}
a.navi{text-decoration:none}
a.navi:hover{background:rgba(255,255,255,.6)}
.navi{display:flex;align-items:center;gap:10px;padding:10px 14px;border-radius:999px;font-weight:800;font-size:15px;margin-bottom:4px}
.navi.on{background:#FFFFFF;color:#5E3B22 !important;box-shadow:0 2px 6px rgba(42,36,32,.12)}
.navi .badge{margin-left:auto;background:#8B5E3C;color:#FFFFFF !important;font-size:12px;padding:1px 9px;border-radius:999px}
.duty{background:#FFFFFF;border:3px solid #E6CDAE;border-radius:24px;padding:14px;text-align:center;margin-top:24px}
.duty b{display:block;font-size:14px;margin-top:4px}
.duty span{font-size:13px;color:#565B62}

/* banner */
.banner{position:relative;overflow:hidden;background:#C9CDD2;border-radius:28px 28px 0 0;padding:30px 32px;display:flex;justify-content:space-between;align-items:center;gap:20px;flex-wrap:wrap}
.banner .ring{position:absolute;width:520px;height:520px;border-radius:50%;border:40px solid #D9DCE0;top:-330px;right:-100px}
.banner h1{position:relative;margin:0;font-size:44px;line-height:1.05;color:#5E3B22 !important;text-shadow:0 3px 0 #FFFFFF}
.banner p{position:relative;margin:8px 0 0;font-size:17px;font-weight:700}
.focus{position:relative;display:inline-block;background:#FFFFFF;border-radius:14px;padding:8px 14px;font-size:15px;font-weight:600;margin-top:10px}
.focus b{color:#8B5E3C}
.checked{position:relative;background:#FFFFFF;border-radius:999px;padding:8px 14px;font-size:14px;font-weight:800;color:#5E3B22;margin-right:90px}
.checker{height:26px;border-radius:0 0 28px 28px;margin-bottom:18px;background-image:repeating-conic-gradient(#DDE0E4 0 25%, #FFFFFF 0 50%);background-size:26px 26px}
.daisy{position:absolute;top:-14px;right:18px;animation:spin 14s linear infinite}
.sparkle{position:absolute;animation:twinkle 2.4s ease-in-out infinite}
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes twinkle{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.35;transform:scale(.75)}}

/* cards */
.card{background:#FFFFFF;border:3px solid #DDE0E4;border-radius:24px;padding:20px 22px;margin-bottom:16px}
.kpi .lab{font-size:14px;font-weight:600;color:#565B62}
.kpi .val{font-size:28px;font-weight:600;letter-spacing:-.3px;white-space:nowrap;margin-top:4px}
.kpi .del{font-size:13px;font-weight:600;color:#8B5E3C;white-space:nowrap}
.ttl{font-size:18px;font-weight:800}
.sub{font-size:14px;color:#565B62;margin-bottom:6px}
.slab{font-family:'Alfa Slab One',serif;font-size:22px}
.pill{display:inline-block;font-size:12px;font-weight:800;letter-spacing:1px;text-transform:uppercase;color:#FFFFFF;background:#8B5E3C;border-radius:999px;padding:3px 12px}
.lbl{font-size:12px;font-weight:800;color:#8B5E3C;text-transform:uppercase;letter-spacing:1px;margin-top:8px}
.card p{margin:2px 0 6px;font-size:15px;line-height:1.5;color:#565B62}

/* alerts: 3-step story */
.sev{font-size:13px;font-weight:800;border-radius:999px;padding:4px 12px;margin-right:8px}
.sev.High{color:#8B5E3C;background:#F5E9DA}.sev.Medium{color:#5E3B22;background:#EFE4D6}.sev.Low{color:#565B62;background:#EEF0F2}
.step3{background:#FFFFFF;border:3px solid #DDE0E4;border-radius:22px;padding:14px 16px;height:100%}
.step3.oak{border-color:#E6CDAE}
.step3 .who{display:flex;align-items:center;gap:10px}
.step3 .k{font-size:12px;font-weight:800;color:#565B62;text-transform:uppercase;letter-spacing:1px}
.step3.oak .k{color:#8B5E3C}
.step3 .h{font-size:16px;font-weight:800}
.step3 .done{font-size:15px;margin:4px 0}
[data-testid="stExpander"]{background:#FFFFFF;border:3px solid #DDE0E4 !important;border-radius:22px !important}
[data-testid="stExpander"] summary p{font-size:16px;font-weight:800}

/* buttons */
.stButton button, .stDownloadButton button{background:#8B5E3C;color:#FFFFFF;border:none;border-radius:999px;font-weight:800;min-height:46px;padding:0 22px;box-shadow:0 3px 0 #5E3B22}
.stButton button p, .stDownloadButton button p{color:#FFFFFF !important;font-weight:800}
.stButton button:hover{background:#9A6943;color:#FFFFFF}
.stButton button[kind="secondary"].ghost{background:#FFFFFF}

/* welcome */
.hero{position:relative;overflow:hidden;background:#C9CDD2;border-radius:28px 28px 0 0;padding:44px 40px;display:grid;grid-template-columns:1fr auto;gap:24px;align-items:center}
.hero .ring{position:absolute;width:700px;height:700px;border-radius:50%;border:50px solid #D9DCE0;top:-420px;right:-160px}
.hero .hi{position:relative;display:inline-block;background:#FFFFFF;border-radius:18px 18px 18px 4px;padding:10px 16px;font-size:16px;font-weight:700}
.hero h1{position:relative;margin:18px 0 10px;font-size:52px;line-height:1.05;color:#5E3B22 !important;text-shadow:0 3px 0 #FFFFFF}
.hero p{position:relative;margin:0;font-size:18px;font-weight:600;max-width:480px}
.stage{position:relative;background:radial-gradient(circle at 50% 40%,#FFFFFF,#EEF0F2 75%);border:5px solid #FFFFFF;border-radius:32px;padding:18px 18px 6px}
.topbar{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;background:linear-gradient(180deg,#F1F3F5,#D9DCE0);border:1px solid #B9BFC6;border-radius:999px;padding:8px 8px 8px 20px;margin-bottom:22px}
.topbar .t{font-size:14px;font-weight:700;color:#565B62;background:#FFFFFF;border-radius:999px;padding:8px 14px}
.tbl{background:#FFFFFF;border:3px solid #DDE0E4;border-radius:18px;overflow:hidden;overflow-x:auto;margin:14px 0 6px}
.tbl table{width:100%;border-collapse:collapse;font-size:15px}
.tbl th{text-align:left;background:#F4F5F7;color:#565B62;font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:1px;padding:10px 14px}
.tbl td{padding:11px 14px;border-top:2px solid #EEF0F2;color:#2A2420;white-space:nowrap}
.tbl td.num{text-align:right;font-variant-numeric:tabular-nums}
.tbl tr.hl td{background:#FBE7DA !important;font-weight:800;color:#5E3B22}
.tbl th a.sorth{color:#565B62 !important;text-decoration:none !important;display:inline-flex;gap:6px;align-items:center}
.tbl th a.sorth:hover{color:#8B5E3C !important}
.tbl th a.sorth span{color:#8B5E3C;font-size:13px}
.tbl tr:nth-child(even) td{background:#FBF8F4}
[data-testid="stElementToolbar"]{display:none !important}
.vega-embed details,.vega-actions{display:none !important}
[data-testid="stVegaLiteChart"]{background:#FFFFFF;border:3px solid #DDE0E4;border-radius:24px;overflow:hidden}
.tag{display:inline-block;background:#FFFFFF;border:2px dashed #B9BFC6;border-radius:999px;padding:5px 14px;font-weight:700;font-size:13px;color:#565B62;margin-bottom:12px}
</style>
"""

# Dashboard frame: fixed chrome sidebar on the left, page content on the right
FRAME_CSS = """<style>
section[data-testid="stSidebar"], [data-testid="collapsedControl"], [data-testid="stSidebarCollapsedControl"]{display:none !important}
.block-container{max-width:none !important;padding:22px 36px 140px 292px !important}
.side{position:fixed;top:0;left:0;bottom:0;width:256px;z-index:999990;padding:22px 16px;display:flex;flex-direction:column;gap:6px;
  background:linear-gradient(180deg,#F1F3F5 0%,#D9DCE0 55%,#C9CDD2 100%);border-right:1px solid #B9BFC6}
.side a{text-decoration:none !important}
.side .home{display:flex;align-items:center;gap:8px;font-family:'Alfa Slab One',serif;font-size:20px;color:#5E3B22 !important;padding:4px 10px 18px}
.side .navi{color:#2A2420 !important}
.side .navi.on{color:#5E3B22 !important}
.pagehead{display:flex;justify-content:space-between;align-items:flex-end;gap:16px;flex-wrap:wrap;margin-bottom:6px}
.pagehead h2{margin:0 !important;font-size:34px !important}
.pagehead p{margin:4px 0 0;color:#565B62;font-size:16px}
.section{margin:30px 0 10px;padding-top:18px;border-top:3px solid #DDE0E4}
.section h3{margin:0 !important;font-size:24px !important}
.section p{margin:6px 0 0;color:#565B62;font-size:16px;max-width:760px}
.chartbox{background:#FFFFFF;border:3px solid #DDE0E4;border-radius:24px;padding:14px 18px;margin-top:4px}
.chartbox svg{max-height:300px}
.duo-talk{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px;margin:16px 0 8px}
.duo-talk.stack{grid-template-columns:1fr;margin-top:0}
.talk{display:flex;align-items:flex-end;gap:10px}
.talk .av{flex:none}
.talk .bubble{position:relative;flex:1;background:#FFFFFF;border:3px solid #DDE0E4;border-radius:22px 22px 22px 6px;padding:14px 18px;font-size:15.5px;line-height:1.55;color:#2A2420}
.talk.oak .bubble{border-color:#E6CDAE;background:#FFFBF6}
.talk .bubble .k{font-size:12px;font-weight:800;letter-spacing:1px;text-transform:uppercase;color:#565B62;margin-bottom:4px}
.talk.oak .bubble .k{color:#8B5E3C}
.go{position:relative;display:inline-flex;align-items:center;gap:8px;margin-top:22px;background:#8B5E3C;color:#FFFFFF !important;text-decoration:none !important;
  font-weight:800;font-size:17px;border-radius:999px;padding:14px 28px;box-shadow:0 3px 0 #5E3B22}
div[data-baseweb="select"] > div{border-radius:999px !important;border:3px solid #DDE0E4 !important;background:#FFFFFF !important}
</style>"""

# Alerts and action log
EXTRA_CSS = """<style>
.simbar{display:flex;align-items:center;gap:14px;flex-wrap:wrap;background:#FFFFFF;border:3px solid #DDE0E4;border-radius:999px;padding:6px 20px;margin:4px 0 2px}
.impact{font-size:15px;color:#565B62;margin:4px 0 12px}
.impact b{color:#5E3B22}
.draft{background:#FFFFFF;border:3px solid #DDE0E4;border-radius:18px;padding:14px 16px;font-size:15px;line-height:1.5;margin-bottom:10px}
.draft .to{font-size:12px;font-weight:800;color:#565B62;text-transform:uppercase;letter-spacing:1px}
.draft .subj{font-size:16px;font-weight:800;margin:2px 0 6px}
.draft .note{margin-top:8px;font-size:13px;font-weight:800;color:#8B5E3C}
.sentok{display:flex;align-items:center;gap:8px;font-size:15px;font-weight:800;color:#5E3B22;margin-top:6px}
.cta{display:flex;justify-content:space-between;align-items:center;gap:14px;flex-wrap:wrap}
.cta a{color:#5E3B22 !important;font-weight:800}
.stButton button[kind="secondary"]{background:#FFFFFF;color:#2A2420;border:2px solid #DDE0E4;box-shadow:none}
.stButton button[kind="secondary"] p{color:#2A2420 !important}
</style>"""

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


def inject_theme():
    st.markdown(CSS + MASCOT_CSS, unsafe_allow_html=True)


def inject_frame():
    st.markdown(FRAME_CSS + EXTRA_CSS, unsafe_allow_html=True)

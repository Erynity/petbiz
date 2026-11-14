"""Renders the dashboard as ONE HTML page that matches the ChromeStudio mockup exactly.

app.py calls render_dashboard(...) and shows the result with
streamlit.components.v1.html(). Small bits of JavaScript inside the page make
the slider, filters and buttons work without needing Streamlit widgets.
"""

import html as _html
import json

from pet import MASCOT_CSS, mascot_svg

INK, MUT, LINE, OAK, OAKD, BG = "#2A2420", "#565B62", "#DDE0E4", "#8B5E3C", "#5E3B22", "#F4F5F7"
HL = "#D9692B"  # highlight bar colour (orange-oak)
SLAB = "font-family: 'Alfa Slab One', serif; font-weight: 400"
CARD = f"background: #FFFFFF; border: 3px solid {LINE}; border-radius: 24px"

ICON = {
    "home": '<path d="M3 11l9-8 9 8"/><path d="M5 10v10h14V10"/>',
    "chart": '<path d="M4 20V10"/><path d="M10 20V4"/><path d="M16 20v-7"/><path d="M22 20H2"/>',
    "bell": '<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10 21a2 2 0 0 0 4 0"/>',
    "data": '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v6c0 1.7 3.6 3 8 3s8-1.3 8-3V5"/><path d="M4 11v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6"/>',
    "log": '<path d="M8 6h13M8 12h13M8 18h13"/><path d="M3 6h.01M3 12h.01M3 18h.01"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/>',
    "cal": '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
    "down": '<path d="M12 3v12"/><path d="M7 10l5 5 5-5"/><path d="M5 21h14"/>',
    "check": '<path d="M20 6L9 17l-5-5"/>',
    "leaf": '<path d="M11 20A7 7 0 0 1 4 13c0-6 7-10 16-10-1 9-5 16-9 17z"/><path d="M4 21c4-6 8-9 12-11"/>',
    "send": '<path d="M22 2L11 13"/><path d="M22 2l-7 20-4-9-9-4 20-7z"/>',
    "gear": '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M4.9 19.1L7 17M17 7l2.1-2.1"/>',
    "arrow": '<path d="M5 12h14"/><path d="M13 6l6 6-6 6"/>',
    "back": '<path d="M19 12H5"/><path d="M11 6l-6 6 6 6"/>',
}


def I(name, s=18, c="currentColor", w=2):
    return (f'<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="{w}" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICON[name]}</svg>')


def esc(x):
    return _html.escape(str(x))


DAISY = ('<svg class="spin" width="{s}" height="{s}" viewBox="0 0 100 100" aria-hidden="true"><g fill="#FFFFFF">'
         '<ellipse cx="50" cy="20" rx="11" ry="20"/><ellipse cx="50" cy="80" rx="11" ry="20"/><ellipse cx="20" cy="50" rx="20" ry="11"/>'
         '<ellipse cx="80" cy="50" rx="20" ry="11"/><ellipse cx="29" cy="29" rx="11" ry="20" transform="rotate(-45 29 29)"/>'
         '<ellipse cx="71" cy="71" rx="11" ry="20" transform="rotate(-45 71 71)"/><ellipse cx="71" cy="29" rx="11" ry="20" transform="rotate(45 71 29)"/>'
         '<ellipse cx="29" cy="71" rx="11" ry="20" transform="rotate(45 29 71)"/></g><circle cx="50" cy="50" r="14" fill="#D4A84A"/></svg>')
SPARK = ('<svg class="tw" width="{s}" height="{s}" viewBox="0 0 24 24" aria-hidden="true">'
         '<path d="M12 0 L14 10 L24 12 L14 14 L12 24 L10 14 L0 12 L10 10 Z" fill="#FFFFFF"/></svg>')


def _fmt(v, fmt):
    if fmt == "percent":
        return f"{v * 100:.0f}%" if abs(v) <= 1.5 else f"{v:.0f}%"
    if fmt == "dollar":
        return f"${v / 1e6:.1f}M" if abs(v) >= 1e6 else f"${v / 1e3:.0f}K" if abs(v) >= 1e3 else f"${v:,.0f}"
    return f"{v:,.0f}"


def sparkline(values, color):
    if not values or len(values) < 2:
        return ""
    lo, hi = min(values), max(values)
    span = (hi - lo) or 1
    step = 120 / (len(values) - 1)
    pts = " ".join(f"{i * step:.1f},{28 - (v - lo) / span * 24:.1f}" for i, v in enumerate(values))
    return (f'<svg viewBox="0 0 120 30" width="100%" height="30" preserveAspectRatio="none" aria-hidden="true" style="display:block;margin-top:10px">'
            f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2.5" stroke-linecap="round" '
            f'stroke-linejoin="round" vector-effect="non-scaling-stroke"/></svg>')


def bar_chart_svg(chart):
    """Clean bar chart like the screenshot: % labels on top, one highlighted bar."""
    df = chart["data"]
    col = df.columns[0]
    s = df[col]
    if chart.get("sort"):
        s = s.sort_values(ascending=False)
    hl = chart.get("highlight") or []
    hl = {str(h) for h in ([hl] if isinstance(hl, str) else hl)}
    fmt = chart.get("format")
    W, H, left, bottom, top = 560, 300, 44, 46, 26
    import math
    raw = float(s.max()) or 1
    step = raw / 4
    mag = 10 ** math.floor(math.log10(step))
    step = next(m * mag for m in (1, 2, 2.5, 5, 10) if m * mag >= step)
    vmax = step * math.ceil(raw * 1.08 / step)
    n = len(s)
    slot = (W - left - 10) / n
    bw = slot * 0.68
    out = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="{esc(chart["title"])}" style="display:block">']
    ticks = int(round(vmax / step))
    for k in range(ticks + 1):  # gridlines + axis labels
        v = step * k
        y = H - bottom - (H - bottom - top) * k / ticks
        out.append(f'<line x1="{left}" y1="{y:.1f}" x2="{W - 6}" y2="{y:.1f}" stroke="#EEF0F2" stroke-width="1.5"/>')
        out.append(f'<text x="{left - 8}" y="{y + 4:.1f}" text-anchor="end" font-size="12" fill="{MUT}" font-weight="600">{_fmt(v, fmt)}</text>')
    for i, (label, v) in enumerate(s.items()):
        x = left + 5 + i * slot + (slot - bw) / 2
        h = (H - bottom - top) * float(v) / vmax
        y = H - bottom - h
        is_hl = str(label) in hl
        out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{h:.1f}" rx="3" fill="{HL if is_hl else "#C9CDD2"}"/>')
        out.append(f'<text x="{x + bw / 2:.1f}" y="{y - 7:.1f}" text-anchor="middle" font-size="12" font-weight="800" fill="{INK}">{_fmt(float(v), fmt)}</text>')
        out.append(f'<text x="{x + bw / 2:.1f}" y="{H - bottom + 18}" text-anchor="middle" font-size="12" font-weight="{800 if is_hl else 600}" fill="{OAKD if is_hl else MUT}">{esc(label)}</text>')
    if chart.get("x_title"):
        out.append(f'<text x="{(W + left) / 2}" y="{H - 6}" text-anchor="middle" font-size="12" font-weight="700" fill="#9AA0A8">{esc(chart["x_title"])}</text>')
    out.append("</svg>")
    return "".join(out)


def _table(df, row_attr_col=None):
    head = "".join(f"<th>{esc(c)}</th>" for c in df.columns)
    rows = []
    for _, r in df.iterrows():
        attrs = ""
        if row_attr_col:
            attrs += f' data-region="{esc(r.get("region", ""))}"'
            if "days_late" in df.columns:
                attrs += f' data-days="{r["days_late"]}"'
        rows.append(f"<tr{attrs}>" + "".join(f"<td>{esc(v)}</td>" for v in r.values) + "</tr>")
    return f'<div class="tbl"><table><thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'


CSS = """
body{margin:0;background:#F4F5F7;font-family:'Nunito',sans-serif;color:#2A2420}
*{box-sizing:border-box}
a{color:#5E3B22}
.checker{background-image:repeating-conic-gradient(#DDE0E4 0 25%, #FFFFFF 0 50%);background-size:26px 26px}
@keyframes twinkle{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.35;transform:scale(.75)}}
@keyframes spin{to{transform:rotate(360deg)}}
.tw{animation:twinkle 2.4s ease-in-out infinite}
.spin{animation:spin 14s linear infinite}
.navi{display:flex;align-items:center;gap:12px;padding:10px 14px;min-height:46px;border-radius:999px;text-decoration:none;font-size:15px;font-weight:800;color:#2A2420}
.navi:hover{background:rgba(255,255,255,.55)}
.navi.on{background:#FFFFFF;color:#5E3B22;box-shadow:0 2px 6px rgba(42,36,32,.12)}
.badge{margin-left:auto;background:#8B5E3C;color:#FFFFFF;font-size:12px;font-weight:800;padding:1px 9px;border-radius:999px}
.tbl{border:3px solid #DDE0E4;border-radius:18px;overflow:auto;margin:0 22px 18px;background:#FFFFFF}
.tbl table{width:100%;border-collapse:collapse;font-size:15px}
.tbl th{text-align:left;background:#F4F5F7;color:#565B62;font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:1px;padding:10px 14px}
.tbl td{padding:11px 14px;border-top:2px solid #EEF0F2}
.tbl tr:nth-child(even) td{background:#FBF8F4}
.pillf{font-family:inherit;font-size:14px;font-weight:700;background:#FFFFFF;color:#2A2420;border:2px solid #DDE0E4;border-radius:999px;padding:0 14px;min-height:38px;cursor:pointer}
.pillf.on{background:#2A2420;color:#FFFFFF;border-color:#2A2420}
.btn{font-family:inherit;font-size:15px;font-weight:800;border-radius:999px;min-height:44px;padding:0 18px;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;gap:8px}
.btn.oak{background:#8B5E3C;color:#FFFFFF;border:none;box-shadow:0 3px 0 #5E3B22}
.btn.ghost{background:#FFFFFF;color:#2A2420;border:2px solid #DDE0E4}
input[type=range]{accent-color:#8B5E3C}
#toast{position:fixed;left:50%;bottom:24px;transform:translateX(-50%) translateY(20px);opacity:0;background:#2A2420;color:#FFFFFF;font-weight:800;padding:12px 20px;border-radius:999px;transition:.3s;z-index:50}
#toast.show{opacity:1;transform:translateX(-50%)}
"""

JS = """
<script>
const toast = (msg) => { const t = document.getElementById('toast'); t.textContent = msg; t.classList.add('show'); setTimeout(() => t.classList.remove('show'), 2200); };
document.querySelectorAll('[data-toast]').forEach(b => b.addEventListener('click', () => toast(b.dataset.toast)));
document.querySelectorAll('[data-go]').forEach(a => a.addEventListener('click', (e) => {
  e.preventDefault();
  try { window.parent.location.search = '?page=' + a.dataset.go; } catch (err) { window.top.location.search = '?page=' + a.dataset.go; }
}));
document.querySelectorAll('a[href^="#"]').forEach(a => a.addEventListener('click', (e) => {
  e.preventDefault(); const el = document.querySelector(a.getAttribute('href')); if (el) el.scrollIntoView({behavior: 'smooth'});
  document.querySelectorAll('.navi').forEach(n => n.classList.remove('on')); a.classList.add('on');
}));
let region = 'All';
const rows = () => document.querySelectorAll('#flagtable tbody tr');
function refresh() {
  const days = +document.getElementById('days').value;
  document.getElementById('daysval').textContent = days + ' days late';
  let n = 0;
  rows().forEach(r => {
    const okDays = r.dataset.days === undefined || +r.dataset.days >= days;
    const okReg = region === 'All' || r.dataset.region === region;
    r.style.display = okDays && okReg ? '' : 'none';
    if (okDays && okReg) n++;
  });
  document.getElementById('flagcount').textContent = n;
}
const slider = document.getElementById('days'); if (slider) { slider.addEventListener('input', refresh); refresh(); }
document.querySelectorAll('.pillf').forEach(p => p.addEventListener('click', () => {
  document.querySelectorAll('.pillf').forEach(q => q.classList.remove('on')); p.classList.add('on'); region = p.dataset.region; refresh();
}));
</script>
"""


def render_dashboard(focus, kpis, charts, prep, insights, issues, placeholders=False, date_range="Jan 2025 – Sep 2026"):
    flagged = [i for i in issues if len(i["rows"]) > 0]

    nav = [("overview", "home", "Overview"), ("insights", "chart", "Insights"), ("alerts", "bell", "Alerts"),
           ("data", "data", "Data prep"), ("log", "log", "Action log")]
    navh = "".join(
        f'<a href="#{a}" class="navi{" on" if i == 0 else ""}">{I(ic, 18, OAK if i == 0 else MUT)}<span style="flex:1">{t}</span>'
        + (f'<span class="badge">{len(flagged)}</span>' if a == "alerts" else "") + "</a>"
        for i, (a, ic, t) in enumerate(nav)
    )

    kp = "".join(
        f'<div style="{CARD}; padding: 20px 22px 14px"><div style="font-size: 14px; font-weight: 600; color: {MUT}">{esc(k["label"])}</div>'
        f'<div style="font-size: 28px; font-weight: 600; letter-spacing: -0.3px; margin-top: 4px; white-space: nowrap; line-height: 1.15">{esc(k["value"])}</div>'
        f'<div style="font-size: 13px; font-weight: 600; color: {OAK if i % 2 == 0 else MUT}; margin: 2px 0 0; white-space: nowrap">{esc(k["delta"])}</div>'
        f'{sparkline(k.get("trend"), OAK if i % 2 == 0 else MUT)}</div>'
        for i, k in enumerate(kpis)
    )

    ch = "".join(
        f'<div style="{CARD}; padding: 20px 22px"><div style="font-size: 18px; font-weight: 800">{esc(c["title"])}</div>'
        f'<div style="font-size: 14px; color: {MUT}; margin-bottom: 8px">{esc(c.get("caption", ""))}</div>{bar_chart_svg(c)}</div>'
        for c in charts
    )

    ins = "".join(
        f'<div style="{CARD}; padding: 22px"><div style="display: inline-block; font-size: 12px; font-weight: 800; letter-spacing: 1px; text-transform: uppercase; color: #FFFFFF; background: {OAK}; border-radius: 999px; padding: 3px 12px">Insight {n}</div>'
        f'<div style="font-size: 20px; font-weight: 700; margin: 10px 0 8px">{esc(x["title"])}</div>'
        + "".join(f'<div style="font-size: 12px; font-weight: 800; color: {OAK}; text-transform: uppercase; letter-spacing: 1px">{lbl}</div>'
                  f'<p style="margin: 2px 0 8px; font-size: 15px; line-height: 1.5; color: {MUT}">{esc(x[key])}</p>'
                  for lbl, key in (("What happened", "what"), ("Why it matters", "why"), ("What to do", "todo")))
        + "</div>"
        for n, x in enumerate(insights, start=1)
    )

    preph = "".join(
        f'<div style="display: grid; grid-template-columns: 28px 1fr auto; gap: 12px; align-items: start; padding: 12px 0; border-top: 2px solid #EEF0F2">'
        f'<span style="width: 28px; height: 28px; border-radius: 50%; background: #F5E9DA; display: flex; align-items: center; justify-content: center">{I("check", 14, OAK, 3)}</span>'
        f'<div><div style="font-size: 15px; font-weight: 800">{esc(p["what"])}</div><div style="font-size: 14px; color: {MUT}; margin-top: 2px"><b style="color: {OAK}">Why:</b> {esc(p["why"])}</div></div>'
        f'<span style="font-size: 13px; font-weight: 700; color: {MUT}; background: #EEF0F2; border-radius: 999px; padding: 3px 10px; white-space: nowrap">{esc(p["rows"])}</span></div>'
        for p in prep
    )

    sev_style = {"High": (OAK, "#F5E9DA"), "Medium": (OAKD, "#EFE4D6"), "Low": (MUT, "#EEF0F2")}
    alerts_html = ""
    first = flagged[0] if flagged else None
    for issue in issues:
        c, bg = sev_style.get(issue["severity"], (MUT, "#EEF0F2"))
        is_first = issue is first
        count_html = f'<span id="flagcount">{len(issue["rows"])}</span>' if is_first else str(len(issue["rows"]))
        alerts_html += (
            f'<div style="display: grid; grid-template-columns: auto 1fr auto; gap: 14px; align-items: center; padding: 14px 22px; border-top: 2px solid #EEF0F2">'
            f'<span style="font-size: 13px; font-weight: 800; color: {c}; background: {bg}; border-radius: 999px; padding: 4px 12px">{esc(issue["severity"])}</span>'
            f'<div><div style="font-size: 16px; font-weight: 800">{count_html} {esc(issue["name"])}</div>'
            f'<div style="font-size: 14px; color: {MUT}; margin-top: 2px">{esc(" · ".join(issue["actions"][:2]))}</div></div>'
            f'<span style="font-size: 14px; font-weight: 800; color: {OAKD}; border: 2px solid #E6CDAE; border-radius: 999px; padding: 8px 16px">{"Open" if is_first else "Review"}</span></div>'
        )
        if is_first:
            done = "".join(f'<span style="display: flex; align-items: center; gap: 8px">{I("check", 16, OAK, 3)} {esc(a)}</span>' for a in issue["actions"])
            regions = sorted({str(r) for r in issue["rows"]["region"]}) if "region" in issue["rows"].columns else []
            filters = ""
            if regions:
                filters = ('<div style="display: flex; gap: 8px; flex-wrap: wrap; padding: 0 22px 14px">'
                           '<button class="pillf on" data-region="All">All regions</button>'
                           + "".join(f'<button class="pillf" data-region="{esc(r)}">{esc(r)}</button>' for r in regions) + "</div>")
            alerts_html += f'''<div style="background: #FBF8F4; border-top: 2px solid #EEF0F2; padding: 22px">
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 14px">
<div style="background: #FFFFFF; border: 3px solid {LINE}; border-radius: 22px; padding: 16px; display: flex; flex-direction: column; gap: 8px">
<div style="display: flex; align-items: center; gap: 10px"><span style="flex: none; width: 58px">{mascot_svg("chrome", "worried", 58)}</span><div><div style="font-size: 12px; font-weight: 800; color: {MUT}; text-transform: uppercase; letter-spacing: 1px">Step 1 · Chrome noticed</div><div style="font-size: 16px; font-weight: 800">{esc(issue["found"])}</div></div></div>
<p style="margin: 0; font-size: 15px; line-height: 1.5; color: {MUT}">Rule: {esc(issue["rule"])}.</p></div>
<div style="background: #FFFFFF; border: 3px solid #E6CDAE; border-radius: 22px; padding: 16px; display: flex; flex-direction: column; gap: 8px">
<div style="display: flex; align-items: center; gap: 10px"><span style="flex: none; width: 58px">{mascot_svg("oak", "happy", 58)}</span><div><div style="font-size: 12px; font-weight: 800; color: {OAK}; text-transform: uppercase; letter-spacing: 1px">Step 2 · Oak took care of it</div><div style="font-size: 16px; font-weight: 800">{len(issue["actions"])} things done</div></div></div>
<div style="display: flex; flex-direction: column; gap: 6px; font-size: 15px">{done}</div></div>
<div style="background: #FFFFFF; border: 3px solid {LINE}; border-radius: 22px; padding: 16px; display: flex; flex-direction: column; gap: 10px">
<div style="font-size: 12px; font-weight: 800; color: {MUT}; text-transform: uppercase; letter-spacing: 1px">Step 3 · Your turn</div>
<div style="font-size: 16px; font-weight: 800">Send the reminder?</div>
<button class="btn oak" data-toast="Sent ✓ {esc(issue["notify"])} notified">{I("send", 15, "#FFFFFF")} Preview &amp; send</button>
<button class="btn ghost" data-toast="Alert dismissed">Not a problem, dismiss</button></div>
</div>
<div style="margin-top: 14px; display: flex; align-items: center; gap: 14px; flex-wrap: wrap; background: #FFFFFF; border: 3px solid {LINE}; border-radius: 999px; padding: 10px 20px">
<span style="font-size: 14px; font-weight: 800; white-space: nowrap; display: inline-flex; align-items: center; gap: 6px">{I("gear", 15, OAK)} Flag after</span>
<input id="days" type="range" min="15" max="90" step="5" value="30" aria-label="Days late before flagging" style="flex: 1; min-width: 160px">
<span id="daysval" style="font-size: 15px; font-weight: 800; color: {OAKD}; white-space: nowrap">30 days late</span>
</div></div>{filters}<div id="flagtable">{_table(issue["rows"], row_attr_col=True)}</div>'''

    log_rows = [(i["name"], len(i["rows"]), a, i["notify"]) for i in flagged for a in i["actions"]]
    logh = "".join(
        f'<tr><td>{esc(c)}</td><td>{n}</td><td>{esc(a)}</td><td>{esc(w)}</td></tr>' for c, n, a, w in log_rows
    )
    log_csv = "condition,records,action,sent to\n" + "\n".join(f'"{c}",{n},"{a}","{w}"' for c, n, a, w in log_rows)

    tag = ('<span style="display:inline-block;background:#FFFFFF;border:2px dashed #B9BFC6;border-radius:999px;padding:5px 14px;'
           'font-weight:700;font-size:13px;color:#565B62">Placeholders · waiting for analysis.py</span>') if placeholders else ""

    body = f'''<div style="min-height: 100vh; display: grid; grid-template-columns: 256px 1fr; background: {BG}">
<aside style="background: linear-gradient(180deg, #F1F3F5 0%, #D9DCE0 55%, #C9CDD2 100%); border-right: 1px solid #B9BFC6; padding: 22px 16px; display: flex; flex-direction: column; gap: 6px">
<div style="position: sticky; top: 22px; display: flex; flex-direction: column; gap: 6px">
<div style="display: flex; align-items: center; gap: 8px; padding: 4px 10px 18px; {SLAB}; font-size: 20px; color: {OAKD}">{I("leaf", 22, OAK)} Chrome &amp; Oak</div>
<div style="font-size: 11px; font-weight: 800; letter-spacing: 1.5px; text-transform: uppercase; color: {MUT}; padding: 0 14px 6px">Workspace</div>
{navh}
<a href="#" data-go="welcome" class="navi" style="margin-top: 18px">{I("back", 18, MUT)}<span>Back to welcome</span></a>
</div></aside>
<main style="padding: 22px 32px 120px; min-width: 0; display: flex; flex-direction: column; gap: 18px">
<div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap">
<label style="flex: 1; min-width: 220px; display: flex; align-items: center; gap: 8px; background: #FFFFFF; border: 3px solid {LINE}; border-radius: 999px; padding: 0 16px; min-height: 46px; color: {MUT}">{I("search", 16, MUT)}<input placeholder="Search customers, invoices, reps" style="border: none; outline: none; font-family: inherit; font-size: 15px; flex: 1; background: transparent"></label>
<span style="display: inline-flex; align-items: center; gap: 8px; background: #FFFFFF; border: 3px solid {LINE}; border-radius: 999px; padding: 0 16px; min-height: 46px; font-size: 15px; font-weight: 700">{I("cal", 16, MUT)} {esc(date_range)}</span>
<a class="btn oak" style="text-decoration: none; min-height: 46px" download="action_log.csv" href="data:text/csv;charset=utf-8,{_html.escape(log_csv.replace(chr(10), "%0A").replace(" ", "%20"))}">{I("down", 16, "#FFFFFF")} Export</a>
</div>
{tag}
<div id="overview">
<div style="position: relative; overflow: hidden; background: #C9CDD2; border-radius: 28px 28px 0 0; padding: 30px 32px; display: flex; justify-content: space-between; align-items: center; gap: 20px; flex-wrap: wrap">
<div style="position: absolute; width: 520px; height: 520px; border-radius: 50%; border: 40px solid #D9DCE0; top: -330px; right: -100px"></div>
<span style="position: absolute; top: 22px; right: 34%">{SPARK.format(s=22)}</span><span style="position: absolute; bottom: 18px; left: 48%">{SPARK.format(s=16)}</span>
<span style="position: absolute; top: -14px; right: 18px">{DAISY.format(s=84)}</span>
<div style="position: relative"><h1 style="margin: 0; {SLAB}; font-size: 44px; line-height: 1.05; color: {OAKD}; text-shadow: 0 3px 0 #FFFFFF">How's business?</h1>
<p style="margin: 8px 0 0; font-size: 17px; font-weight: 700">Revenue is up, but cash is tight. Here's what's driving the gap.</p>
<p style="margin: 10px 0 0; display: inline-block; background: #FFFFFF; border-radius: 14px; padding: 8px 14px; font-size: 15px; font-weight: 600"><b style="color: {OAK}">Our focus:</b> {esc(focus)}</p></div>
<span style="position: relative; display: inline-flex; align-items: center; gap: 8px; font-size: 14px; font-weight: 800; color: {OAKD}; background: #FFFFFF; border-radius: 999px; padding: 8px 14px; margin-right: 90px">{I("check", 14, OAK, 3)} Data checked today</span>
</div>
<div class="checker" style="height: 26px; border-radius: 0 0 28px 28px"></div>
</div>
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 16px">{kp}</div>
<div id="insights" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(380px, 1fr)); gap: 16px">{ch}</div>
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px">{ins}</div>
<div id="data" style="{CARD}; padding: 20px 22px 8px"><div style="display: flex; align-items: center; gap: 10px">{I("data", 20, OAK)}<div style="{SLAB}; font-size: 22px">How we prepared the data</div></div><div style="font-size: 14px; color: {MUT}; margin: 4px 0 8px">Every change we made before trusting a number</div>{preph}</div>
<div id="alerts" style="{CARD}; overflow: hidden">
<div style="display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; padding: 18px 22px"><div><div style="{SLAB}; font-size: 22px">Alerts inbox</div><div style="font-size: 14px; color: {MUT}">Triggered automatically when a condition is met</div></div><a href="#log" style="font-size: 15px; font-weight: 800; text-decoration: none; color: {OAKD}; display: inline-flex; align-items: center; gap: 6px">View action log {I("arrow", 14, OAKD)}</a></div>
{alerts_html}
</div>
<div id="log" style="{CARD}; overflow: hidden; padding-top: 18px">
<div style="{SLAB}; font-size: 22px; padding: 0 22px 12px">Action log</div>
<div class="tbl"><table><thead><tr><th>Condition</th><th>Records</th><th>Action</th><th>Sent to</th></tr></thead><tbody>{logh}</tbody></table></div>
</div>
</main></div><div id="toast" role="status"></div>'''

    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Alfa+Slab+One&family=Nunito:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>{CSS}</style>{MASCOT_CSS}</head><body>{body}{JS}</body></html>'''

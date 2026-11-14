"""Hand-drawn SVG charts: the bar chart used on the Insights page and the KPI sparklines."""

import math

from chrome_oak.ui.components import esc
from chrome_oak.ui.theme import HL, INK, MUT, OAKD


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
    """Bar chart with value labels on top and highlighted bar(s).

    chart keys: "title", "data" (one-column DataFrame), optional "format" ("percent" | "dollar"),
    "sort" (biggest first), "highlight" (label or list of labels), "x_title".
    """
    df = chart["data"]
    s = df[df.columns[0]]
    if chart.get("sort"):
        s = s.sort_values(ascending=False)
    hl = chart.get("highlight") or []
    hl = {str(h) for h in ([hl] if isinstance(hl, str) else hl)}
    fmt = chart.get("format")
    W, H, left, bottom, top = 560, 300, 44, 46, 26
    raw = float(s.max()) or 1
    step = raw / 4
    mag = 10 ** math.floor(math.log10(step))
    step = next(m * mag for m in (1, 2, 2.5, 5, 10) if m * mag >= step)
    vmax = step * math.ceil(raw * 1.08 / step)
    slot = (W - left - 10) / max(len(s), 1)
    bw = slot * 0.68
    out = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="{esc(chart["title"])}" style="display:block">']
    ticks = int(round(vmax / step))
    for k in range(ticks + 1):  # gridlines + axis labels
        y = H - bottom - (H - bottom - top) * k / ticks
        out.append(f'<line x1="{left}" y1="{y:.1f}" x2="{W - 6}" y2="{y:.1f}" stroke="#EEF0F2" stroke-width="1.5"/>')
        out.append(f'<text x="{left - 8}" y="{y + 4:.1f}" text-anchor="end" font-size="12" fill="{MUT}" font-weight="600">{_fmt(step * k, fmt)}</text>')
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

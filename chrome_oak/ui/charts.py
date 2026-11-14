"""Hand-drawn SVG charts: the bar chart used on the Insights page and the KPI sparklines."""

import math

from chrome_oak.ui.components import esc
from chrome_oak.ui.theme import HL, INK, MUT, OAK, OAKD


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


def _nice_max(raw, n=4):
    raw = raw or 1
    step = raw / n
    mag = 10 ** math.floor(math.log10(step))
    step = next(m * mag for m in (1, 2, 2.5, 5, 10) if m * mag >= step)
    return step, step * math.ceil(raw * 1.08 / step)


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
    W, H = chart.get("width", 560), chart.get("height", 300)
    left, bottom, top = 54 if fmt == "dollar" else 44, 46, 26
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


def hbar_chart_svg(chart):
    """Horizontal bars: for long labels (e.g. product names). Biggest on top."""
    s = chart["data"][chart["data"].columns[0]].sort_values(ascending=False)
    hl = chart.get("highlight") or []
    hl = {str(h) for h in ([hl] if isinstance(hl, str) else hl)}
    fmt = chart.get("format")
    row, left, right = 30, 170, 70
    W, H = chart.get("width", 560), len(s) * row + 10
    vmax = float(s.max()) or 1
    out = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="{esc(chart["title"])}" style="display:block">']
    for i, (label, v) in enumerate(s.items()):
        y = 5 + i * row
        w = (W - left - right) * float(v) / vmax
        is_hl = str(label) in hl
        out.append(f'<text x="{left - 10}" y="{y + row / 2 + 4:.1f}" text-anchor="end" font-size="13" font-weight="{800 if is_hl else 600}" fill="{OAKD if is_hl else MUT}">{esc(label)}</text>')
        out.append(f'<rect x="{left}" y="{y + 5}" width="{max(w, 2):.1f}" height="{row - 10}" rx="3" fill="{HL if is_hl else "#C9CDD2"}"/>')
        out.append(f'<text x="{left + w + 8:.1f}" y="{y + row / 2 + 4:.1f}" font-size="12" font-weight="800" fill="{INK}">{_fmt(float(v), fmt)}</text>')
    out.append("</svg>")
    return "".join(out)


def line_chart_svg(chart):
    """Lines over an ordered x (e.g. quarters). One line per column, with a small legend."""
    df = chart["data"]
    fmt = chart.get("format")
    colors = [OAK, "#9AA0A8", "#D4A84A"]
    W, H = chart.get("width", 560), chart.get("height", 300)
    left, right, bottom, top = 60, 20, 40, 40
    step, vmax = _nice_max(float(df.max().max()))
    n = len(df)
    xs = [left + (W - left - right) * (i / max(n - 1, 1)) for i in range(n)]
    y = lambda v: H - bottom - (H - bottom - top) * float(v) / vmax  # noqa: E731
    out = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="{esc(chart["title"])}" style="display:block">']
    ticks = int(round(vmax / step))
    for k in range(ticks + 1):
        yy = y(step * k)
        out.append(f'<line x1="{left}" y1="{yy:.1f}" x2="{W - right}" y2="{yy:.1f}" stroke="#EEF0F2" stroke-width="1.5"/>')
        out.append(f'<text x="{left - 8}" y="{yy + 4:.1f}" text-anchor="end" font-size="12" fill="{MUT}" font-weight="600">{_fmt(step * k, fmt)}</text>')
    for x, label in zip(xs, df.index):
        out.append(f'<text x="{x:.1f}" y="{H - bottom + 20}" text-anchor="middle" font-size="12" fill="{MUT}" font-weight="600">{esc(label)}</text>')
    lx = left
    for c, col in zip(colors, df.columns):
        pts = " ".join(f"{x:.1f},{y(v):.1f}" for x, v in zip(xs, df[col]))
        out.append(f'<polyline points="{pts}" fill="none" stroke="{c}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>')
        out += [f'<circle cx="{x:.1f}" cy="{y(v):.1f}" r="5" fill="{c}" stroke="#FFFFFF" stroke-width="2"/>' for x, v in zip(xs, df[col])]
        last = df[col].iloc[-1]
        out.append(f'<text x="{xs[-1] - 8:.1f}" y="{y(last) - 12:.1f}" text-anchor="end" font-size="12" font-weight="800" fill="{INK}">{_fmt(float(last), fmt)}</text>')
        out.append(f'<rect x="{lx}" y="10" width="14" height="4" rx="2" fill="{c}"/><text x="{lx + 20}" y="16" font-size="13" font-weight="700" fill="{INK}">{esc(col)}</text>')
        lx += 30 + 8 * len(str(col))
    out.append("</svg>")
    return "".join(out)


def chart_svg(chart):
    """Pick the right drawing for a chart dict: kind "line", "hbar" or "bar" (default)."""
    return {"line": line_chart_svg, "hbar": hbar_chart_svg}.get(chart.get("kind"), bar_chart_svg)(chart)


def trend_svg(values, labels, color, fmt=None):
    """A larger sparkline for KPI cards: soft area, line, end dot, and first/last labels."""
    if not values or len(values) < 2:
        return ""
    W, H, pad = 320, 90, 6
    lo, hi = min(values), max(values)
    span = (hi - lo) or 1
    xs = [pad + (W - 2 * pad) * i / (len(values) - 1) for i in range(len(values))]
    ys = [H - 22 - (v - lo) / span * (H - 40) for v in values]
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
    area = f"{xs[0]:.1f},{H - 22} {pts} {xs[-1]:.1f},{H - 22}"
    return (f'<svg viewBox="0 0 {W} {H}" width="100%" aria-hidden="true" style="display:block;margin-top:14px">'
            f'<polygon points="{area}" fill="{color}" opacity=".10"/>'
            f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<circle cx="{xs[-1]:.1f}" cy="{ys[-1]:.1f}" r="4.5" fill="{color}" stroke="#FFFFFF" stroke-width="2"/>'
            f'<text x="{xs[-1]:.1f}" y="{ys[-1] - 9:.1f}" text-anchor="end" font-size="12" font-weight="700" fill="{INK}">{_fmt(values[-1], fmt)}</text>'
            f'<text x="{pad}" y="{H - 4}" font-size="11" font-weight="600" fill="{MUT}">{esc(labels[0])}</text>'
            f'<text x="{W - pad}" y="{H - 4}" text-anchor="end" font-size="11" font-weight="600" fill="{MUT}">{esc(labels[-1])}</text></svg>')

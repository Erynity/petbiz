"""Shared chart helpers (Altair) for the PetBiz test app.

Style: one muted base color with an orange highlight for single-series charts,
the reference categorical palette (in fixed order) for multi-series lines,
and a single-hue sequential scale for heatmaps.
"""

import altair as alt

BASE, HILITE, INK, MUTED, GRID = "#B9B3C6", "#EB6834", "#3A2350", "#6B5A80", "#EFE8F7"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]  # fixed order, never cycled
LINE = "#6C4BB4"
MAX_SERIES = len(SERIES)


def _finish(chart, height):
    return chart.properties(height=height).configure_view(strokeWidth=0).configure(background="transparent")


def _y_axis(fmt):
    return alt.Axis(format=fmt, grid=True, gridColor=GRID, domain=False, ticks=False, labelColor=MUTED)


def bar(df, x, y, highlight, fmt, title_x="", height=260, sort="-y"):
    """One-series bar chart: muted bars, highlighted entities in orange, value labels on bars."""
    d = df.copy()
    d["_hi"] = d[x].isin(highlight)
    color = alt.condition(alt.datum._hi, alt.value(HILITE), alt.value(BASE))
    base = alt.Chart(d).encode(
        x=alt.X(f"{x}:N", sort=sort, title=title_x, axis=alt.Axis(labelAngle=0, domain=False, ticks=False, labelColor=MUTED, labelLimit=140)),
        y=alt.Y(f"{y}:Q", title=None, axis=_y_axis(fmt)),
        tooltip=[alt.Tooltip(f"{x}:N"), alt.Tooltip(f"{y}:Q", format=fmt)],
    )
    bars = base.mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, size=34).encode(color=color)
    labels = base.mark_text(dy=-8, fontWeight="bold", color=INK).encode(text=alt.Text(f"{y}:Q", format=fmt))
    return _finish(bars + labels, height)


def line(df, x, y, fmt, color=None, height=320):
    """Line chart over an ordered x (e.g. month). `color` splits into up to 6 series."""
    enc = dict(
        x=alt.X(f"{x}:O", title=None, axis=alt.Axis(labelAngle=-45, domain=False, ticks=False, labelColor=MUTED, labelOverlap=True)),
        y=alt.Y(f"{y}:Q", title=None, axis=_y_axis(fmt), scale=alt.Scale(zero=True)),
    )
    tips = [alt.Tooltip(f"{x}:O"), alt.Tooltip(f"{y}:Q", format=fmt)]
    if color:
        order = list(dict.fromkeys(df[color]))
        enc["color"] = alt.Color(
            f"{color}:N",
            scale=alt.Scale(domain=order, range=SERIES[: len(order)]),
            legend=alt.Legend(title=None, orient="top", labelColor=INK),
        )
        tips.insert(0, alt.Tooltip(f"{color}:N"))
    else:
        enc["color"] = alt.value(LINE)
    chart = alt.Chart(df).mark_line(strokeWidth=2.5, point=alt.OverlayMarkDef(size=45, filled=True)).encode(**enc, tooltip=tips)
    return _finish(chart, height)


def heat(df, x, y, value, fmt, x_order=None, y_order=None, height=None, labels=True):
    """Heatmap: x by y, cell color = value (single-hue, light -> dark)."""
    n_rows = df[y].nunique()
    height = height or max(180, 34 * n_rows + 40)
    d = df.copy()
    midpoint = (d[value].min() + d[value].max()) / 2
    base = alt.Chart(d).encode(
        x=alt.X(f"{x}:N", sort=x_order, title=None, axis=alt.Axis(labelAngle=-30, orient="top", domain=False, ticks=False, labelColor=MUTED)),
        y=alt.Y(f"{y}:N", sort=y_order, title=None, axis=alt.Axis(domain=False, ticks=False, labelColor=MUTED, labelLimit=160)),
        tooltip=[alt.Tooltip(f"{y}:N"), alt.Tooltip(f"{x}:N"), alt.Tooltip(f"{value}:Q", format=fmt)],
    )
    rect = base.mark_rect(stroke="#FFF8F0", strokeWidth=2, cornerRadius=4).encode(
        color=alt.Color(f"{value}:Q", scale=alt.Scale(range=["#F1EBFA", "#6C4BB4"]), legend=None)
    )
    if not labels:
        return _finish(rect, height)
    text = base.mark_text(fontWeight="bold", fontSize=11).encode(
        text=alt.Text(f"{value}:Q", format=fmt),
        color=alt.condition(alt.datum[value] > midpoint, alt.value("white"), alt.value(INK)),
    )
    return _finish(rect + text, height)

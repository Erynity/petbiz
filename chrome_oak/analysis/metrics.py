"""Small calculation helpers shared by the analysis modules."""


def margin_pct(df):
    """Margin as a share of revenue, on orders where the cost is known."""
    known = df[df["cost"].notna()]
    return known["margin"].sum() / known["net"].sum()


def jan_sep(orders, year):
    return orders[(orders["order_date"].dt.year == year) & (orders["order_date"].dt.month <= 9)]


def money(x):
    return f"${x/1e6:,.2f}M" if abs(x) >= 1e6 else f"${x/1e3:,.0f}K"

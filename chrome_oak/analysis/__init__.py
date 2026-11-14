"""Everything the pages show comes from here. Pages never compute numbers themselves."""

from chrome_oak.analysis.detections import ALERT_RULES, DEFAULTS, detect_issues, run_rule
from chrome_oak.analysis.insights import get_charts, get_insight_charts, get_insights
from chrome_oak.analysis.overview import get_dashboard_charts, get_focus, get_kpis
from chrome_oak.data.loader import get_customers, get_data, get_orders, get_returns, load_data

__all__ = ["ALERT_RULES", "DEFAULTS", "detect_issues", "run_rule", "get_charts", "get_insight_charts", "get_insights", "get_focus",
           "get_kpis", "get_dashboard_charts", "get_data", "get_orders", "get_customers", "get_returns", "load_data"]

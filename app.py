"""PetBiz – UI prototype for Hack2theFuture (Business track, Option B: Chrome & Oak).

Everything below runs on SAMPLE DATA so the UI can be built before the real
dataset drops at 12:00. When the real data is ready, replace get_sample_data()
with functions from analysis.py.

Run with:  streamlit run app.py
"""

from datetime import date

import pandas as pd
import streamlit as st

from pet import pet_avatar, show_pet

st.set_page_config(page_title="PetBiz", page_icon="🐱", layout="wide")

TODAY = date(2026, 11, 14)

# ---------------------------------------------------------------------------
# Theme (lavender / cream Y2K)
# ---------------------------------------------------------------------------
THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Alfa+Slab+One&family=Nunito:wght@400;600;700;800&display=swap');
.stApp{background:#FFF8F0}
html, body, [class*="css"], .stMarkdown, p, li, label{font-family:'Nunito',sans-serif;color:#3A2350}
h1, h2, h3{font-family:'Alfa Slab One',serif !important;font-weight:400 !important;color:#3A2350 !important}
.block-container{padding-top:1.5rem;padding-bottom:10rem;max-width:1150px}
[data-testid="stMetric"]{background:#FFFFFF;border:3px solid #E4D6F5;border-radius:24px;padding:18px 20px}
[data-testid="stMetricLabel"] p{font-weight:700;color:#6B5A80}
[data-testid="stMetricValue"]{font-family:'Alfa Slab One',serif;color:#3A2350}
.banner{position:relative;overflow:hidden;background:#C9B6E4;border-radius:28px 28px 0 0;padding:34px 36px;display:flex;align-items:center;justify-content:space-between;gap:24px;flex-wrap:wrap}
.banner h1{margin:0;font-size:46px;line-height:1.05;color:#FFFFFF !important;text-shadow:0 3px 0 #8E6FC2}
.banner p{margin:8px 0 0;font-size:18px;font-weight:700}
.banner .ring{position:absolute;width:520px;height:520px;border-radius:50%;border:40px solid #D6C6EC;top:-330px;right:-120px}
.banner .avatar{position:relative;width:170px;height:170px;border-radius:50%;background:#F7C6D9;border:6px solid #FFFFFF;display:flex;align-items:center;justify-content:center}
.checker{height:28px;border-radius:0 0 28px 28px;margin-bottom:24px;background-image:repeating-conic-gradient(#E4D6F5 0 25%, #FFFFFF 0 50%);background-size:28px 28px}
.step{display:inline-block;background:#3A2350;color:#FFFFFF;font-weight:800;font-size:13px;letter-spacing:1px;padding:4px 12px;border-radius:999px;margin-bottom:6px}
.card{background:#FFFFFF;border:3px solid #E4D6F5;border-radius:24px;padding:20px 22px;height:100%}
.card h4{margin:0 0 10px;font-size:19px;font-weight:800;color:#3A2350}
.card .label{font-size:13px;font-weight:800;color:#8E6FC2;text-transform:uppercase;letter-spacing:1px;margin-top:10px}
.card p{margin:2px 0 0;font-size:16px;line-height:1.5}
.sample{background:#FDE3EC;border-radius:999px;padding:6px 14px;font-weight:800;font-size:13px;display:inline-block;margin-bottom:10px}
</style>
"""
st.markdown(THEME_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# DATA – sample only. Swap for analysis.py once the real CSV is in data/.
# ---------------------------------------------------------------------------
def get_sample_data():
    invoices = pd.DataFrame(
        {
            "invoice_id": ["INV-101", "INV-102", "INV-103", "INV-104", "INV-105", "INV-106", "INV-107", "INV-108"],
            "customer": ["Customer A", "Customer B", "Customer A", "Customer C", "Customer D", "Customer B", "Customer E", "Customer C"],
            "amount": [1200, 850, 2400, 600, 3100, 950, 400, 1800],
            "due_date": pd.to_datetime(
                ["2026-08-15", "2026-09-01", "2026-09-20", "2026-10-05", "2026-10-10", "2026-10-25", "2026-11-01", "2026-11-10"]
            ),
            "paid": [False, True, False, True, False, False, True, False],
        }
    )
    invoices["days_past_due"] = (pd.Timestamp(TODAY) - invoices["due_date"]).dt.days.clip(lower=0)

    monthly = pd.DataFrame(
        {
            "month": ["Jun", "Jul", "Aug", "Sep", "Oct", "Nov"],
            "Revenue": [10, 11, 12, 13, 14, 15],
            "Cash collected": [9, 9, 9, 8, 8, 7],
        }
    ).set_index("month")
    return invoices, monthly


invoices, monthly = get_sample_data()


# ---------------------------------------------------------------------------
# DETECT
# ---------------------------------------------------------------------------
def detect_overdue(df):
    # TODO (Eryne): this is the detection YOU write by hand (hackathon rule).
    # Placeholder rule so the UI works: unpaid AND more than 30 days past due.
    return df[(~df["paid"]) & (df["days_past_due"] > 30)]


def detect_slow_payers(df):
    # Customers whose unpaid invoices are, on average, more than 15 days late.
    unpaid = df[~df["paid"]]
    avg_late = unpaid.groupby("customer")["days_past_due"].mean()
    return avg_late[avg_late > 15].sort_values(ascending=False)


overdue = detect_overdue(invoices)
slow_payers = detect_slow_payers(invoices)

total_billed = invoices["amount"].sum()
unpaid_total = invoices.loc[~invoices["paid"], "amount"].sum()
overdue_total = overdue["amount"].sum()
overdue_share = overdue_total / total_billed if total_billed else 0

# Pet mood decided from the data
if overdue_share < 0.05:
    mood, pet_message = "happy", "Cash is coming in on time. Great job!"
elif overdue_share < 0.20:
    mood, pet_message = "worried", f"Hmm... {len(overdue)} invoices are over 30 days late. Want me to draft reminders?"
else:
    mood, pet_message = "sad", f"Oh no! ${overdue_total:,.0f} is stuck in overdue invoices. That's why cash feels tight!"


# ---------------------------------------------------------------------------
# PAGE
# ---------------------------------------------------------------------------
st.markdown(
    '<div class="banner"><div class="ring"></div>'
    '<div style="position:relative"><h1>How\'s cash at Chrome &amp; Oak?</h1>'
    "<p>Revenue is up, but cash is tight. Let's find out where it's stuck.</p></div>"
    f'<div class="avatar">{pet_avatar(mood, 120)}</div>'
    '</div><div class="checker"></div>',
    unsafe_allow_html=True,
)
st.markdown('<span class="sample">SAMPLE DATA – real data loads at 12:00</span>', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total billed", f"${total_billed:,.0f}")
c2.metric("Still unpaid", f"${unpaid_total:,.0f}")
c3.metric("Over 30 days late", f"${overdue_total:,.0f}")
c4.metric("Overdue invoices", len(overdue))

# --- Charts ---
st.markdown('<span class="step">STEP 1 · DATA</span>', unsafe_allow_html=True)
st.subheader("Revenue vs. cash collected")
left, right = st.columns(2)
with left:
    st.caption("Revenue keeps growing, but cash collected doesn't follow ($ thousands)")
    st.line_chart(monthly, color=["#9B7FCB", "#F08BB4"])
with right:
    st.caption("Unpaid money by customer ($)")
    by_customer = invoices[~invoices["paid"]].groupby("customer")["amount"].sum().sort_values(ascending=False)
    st.bar_chart(by_customer, color="#9B7FCB")

# --- Detect ---
st.markdown('<span class="step">STEP 2 · DETECT</span>', unsafe_allow_html=True)
st.subheader("What we found")
d1, d2 = st.columns(2)
with d1:
    st.markdown("**🚩 Detection 1: invoices over 30 days late**")
    st.dataframe(
        overdue[["invoice_id", "customer", "amount", "days_past_due"]],
        use_container_width=True,
        hide_index=True,
    )
with d2:
    st.markdown("**🐢 Detection 2: slow-paying customers**")
    st.dataframe(
        slow_payers.rename("avg days late").reset_index(),
        use_container_width=True,
        hide_index=True,
    )

# --- Decide ---
st.markdown('<span class="step">STEP 3 · DECIDE</span>', unsafe_allow_html=True)
st.subheader("Insights")
i1, i2 = st.columns(2)
with i1:
    st.markdown(
        '<div class="card"><h4>Cash is stuck in late invoices</h4>'
        '<div class="label">What happened</div><p>[Insight from real data]</p>'
        '<div class="label">Why it matters</div><p>[Impact on cash]</p>'
        '<div class="label">What to do</div><p>[Action]</p></div>',
        unsafe_allow_html=True,
    )
with i2:
    st.markdown(
        '<div class="card"><h4>A few customers cause most delays</h4>'
        '<div class="label">What happened</div><p>[Insight from real data]</p>'
        '<div class="label">Why it matters</div><p>[Impact on cash]</p>'
        '<div class="label">What to do</div><p>[Action]</p></div>',
        unsafe_allow_html=True,
    )

# --- Act (automation) ---
st.markdown('<span class="step">STEP 4 · ACT</span>', unsafe_allow_html=True)
st.subheader("Automation: payment reminders")
st.write("Every overdue invoice automatically gets a reminder draft, ready to send.")

reminders = []
for _, row in overdue.iterrows():
    text = (
        f"Hi {row['customer']},\n\n"
        f"This is a friendly reminder that invoice {row['invoice_id']} for "
        f"${row['amount']:,.0f} is {row['days_past_due']} days past due. "
        "Could you let us know when we can expect payment?\n\nThank you!\nChrome & Oak"
    )
    reminders.append({"invoice_id": row["invoice_id"], "customer": row["customer"], "message": text})
    with st.expander(f"✉️ {row['invoice_id']} · {row['customer']} · {row['days_past_due']} days late"):
        st.text(text)

if reminders:
    st.download_button(
        "Download all reminders (CSV)",
        pd.DataFrame(reminders).to_csv(index=False),
        file_name="payment_reminders.csv",
        mime="text/csv",
    )

# --- Floating pet (always last, so it sits on top) ---
show_pet(mood, pet_message)
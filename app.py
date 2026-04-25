import streamlit as st
import pandas as pd
import plotly.express as px
from data_fetcher import fetch_congress_trades, get_totals, get_totals_numeric, get_ticker_prices, price_return, get_financial_services_members, get_earnings_dates

st.set_page_config(
    page_title="MarketWatch — Congress Trades",
    page_icon="📈",
    layout="wide",
)

st.markdown("""
<style>
/* ─────────────────────────────────────────
   MarketWatch — Dark Theme
───────────────────────────────────────── */

.block-container { padding-top: 1rem !important; padding-bottom: 3rem !important; }

/* Page background — slate-900, not black */
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
.main { background: #0f172a !important; }

/* Global typography */
h2, h3 {
    color: #f1f5f9 !important;
    font-weight: 700 !important;
    letter-spacing: -0.3px !important;
    padding-bottom: 0.45rem !important;
    border-bottom: 1px solid #334155 !important;
    margin-bottom: 0.8rem !important;
}
hr { border-color: #1e293b !important; margin: 1.5rem 0 !important; }

/* Main content text */
[data-testid="stMain"] p,
[data-testid="stMain"] span,
[data-testid="stMain"] label,
[data-testid="stMain"] li,
.stMarkdown p { color: #cbd5e1 !important; }

/* Expander header text */
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary p,
[data-testid="stExpander"] summary span { color: #e2e8f0 !important; }

/* Selectbox / radio / widget text */
[data-testid="stSelectbox"] span,
[data-testid="stRadio"] span,
[data-testid="stSlider"] span { color: #94a3b8 !important; }

/* Caption text */
[data-testid="stCaptionContainer"] p { color: #64748b !important; }

/* Hero */
.hero {
    background: linear-gradient(135deg, #1e3a5f 0%, #1a3353 50%, #162c47 100%);
    border: 1px solid rgba(56, 189, 248, 0.25);
    border-radius: 18px;
    padding: 2.2rem 2.8rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.4);
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: '';
    position: absolute;
    right: 0; top: 0; bottom: 0; width: 45%;
    background: radial-gradient(ellipse at right center, rgba(56,189,248,0.1) 0%, transparent 70%);
    pointer-events: none;
}
.hero h1 {
    color: #fff;
    font-size: 2.5rem;
    margin: 0;
    font-weight: 900;
    letter-spacing: -1.5px;
}
.hero p { color: #bae6fd; margin: 0.5rem 0 0; font-size: 1rem; }
.accent { color: #38bdf8; }
.live-badge {
    display: inline-block;
    background: rgba(34, 197, 94, 0.15);
    border: 1px solid rgba(34, 197, 94, 0.35);
    color: #86efac;
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 0.2rem 0.7rem;
    border-radius: 20px;
    margin-top: 0.85rem;
}

/* Metric cards */
[data-testid="metric-container"] {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    border-radius: 14px !important;
    padding: 1.2rem 1.5rem !important;
    box-shadow: 0 2px 12px rgba(0,0,0,0.3) !important;
}
[data-testid="stMetricLabel"] p,
[data-testid="stMetricLabel"] label,
[data-testid="stMetricLabel"] span {
    color: #7dd3fc !important;
    font-size: 0.7rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
    font-weight: 700 !important;
}
[data-testid="stMetricValue"],
[data-testid="stMetricValue"] * {
    color: #f8fafc !important;
    font-size: 2rem !important;
    font-weight: 800 !important;
    line-height: 1.15 !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #0f172a !important;
    border-right: 1px solid #1e293b !important;
}
[data-testid="stSidebar"] h2 {
    color: #38bdf8 !important;
    font-size: 0.85rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.12em !important;
    border-bottom: 1px solid #1e293b !important;
    padding-bottom: 0.4rem !important;
}
[data-testid="stSidebar"] label {
    color: #64748b !important;
    font-size: 0.7rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    font-weight: 600 !important;
}

/* Expanders — modern + legacy selectors */
[data-testid="stExpander"] {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    border-radius: 12px !important;
    margin-bottom: 6px !important;
    overflow: hidden !important;
}
.streamlit-expanderHeader {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    border-radius: 10px !important;
    font-size: 0.88rem !important;
    color: #e2e8f0 !important;
}
.streamlit-expanderContent {
    background: #162032 !important;
    border: 1px solid #334155 !important;
    border-top: none !important;
    border-radius: 0 0 10px 10px !important;
}

/* Alert / info boxes */
[data-testid="stAlert"] {
    background: #1e293b !important;
    border-color: #334155 !important;
    border-radius: 10px !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <h1>📈 Market<span class="accent">Watch</span></h1>
    <p>Real-time tracking of stock trades by members of the US Congress</p>
    <span class="live-badge">● Live Data</span>
</div>
""", unsafe_allow_html=True)

PLOT_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(30,41,59,0.5)",
    font=dict(color="#94a3b8", size=11),
    margin=dict(l=10, r=10, t=40, b=10),
)

BUY_SELL_COLORS = {
    "Purchase": "#4ade80",
    "Buy": "#4ade80",
    "Sale": "#f87171",
    "Sale (Full)": "#ef4444",
    "Sale (Partial)": "#fb923c",
    "Exchange": "#c084fc",
}

PARTY_BADGE = {"D": "🔵", "R": "🔴", "I": "🟢", "L": "🟡"}

with st.spinner("Fetching congressional trade data..."):
    df = fetch_congress_trades()
    fin_services_members = get_financial_services_members()

if df.empty:
    st.warning("No data available.")
    st.stop()

if "ReportDate" in df.columns and "TransactionDate" in df.columns:
    df["ReportingLag"] = (df["ReportDate"] - df["TransactionDate"]).dt.days
    df["ReportingLag"] = df["ReportingLag"].apply(lambda x: max(0, x) if pd.notna(x) else None)

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.markdown("## Filters")

min_date = df["TransactionDate"].min().date()
max_date = df["TransactionDate"].max().date()
default_start = max((pd.to_datetime(max_date) - pd.DateOffset(months=2)).date(), min_date)

st.sidebar.markdown("**Date Range**")
d_col1, d_col2 = st.sidebar.columns(2)
start_str = d_col1.text_input("Start", value=default_start.strftime("%m/%d/%y"), help="MM/DD/YY")
end_str   = d_col2.text_input("End",   value=max_date.strftime("%m/%d/%y"),     help="MM/DD/YY")

try:
    start_date = pd.to_datetime(start_str).date()
    end_date   = pd.to_datetime(end_str).date()
except Exception:
    st.sidebar.error("Invalid date — using defaults")
    start_date, end_date = default_start, max_date

st.sidebar.markdown("---")
selected_chamber = st.sidebar.selectbox("Chamber", ["All"] + sorted(df["House"].dropna().unique()))
selected_party   = st.sidebar.selectbox("Party",   ["All"] + sorted(df["Party"].dropna().unique()))
search_ticker    = st.sidebar.text_input("Ticker",         placeholder="e.g. AAPL").upper()
search_name      = st.sidebar.text_input("Representative", placeholder="e.g. Pelosi")

# ── Filter ────────────────────────────────────────────────────────────────────
mask = (df["TransactionDate"].dt.date >= start_date) & (df["TransactionDate"].dt.date <= end_date)
if selected_chamber != "All":
    mask &= df["House"] == selected_chamber
if selected_party != "All":
    mask &= df["Party"] == selected_party
if search_ticker:
    mask &= df["Ticker"].str.contains(search_ticker, case=False, na=False)
if search_name:
    mask &= df["Representative"].str.contains(search_name, case=False, na=False)

filtered_df = df[mask].sort_values("TransactionDate", ascending=False).copy()

# ── Metrics ───────────────────────────────────────────────────────────────────
st.markdown("---")
m1, m2, m3, m4 = st.columns(4)
avg_lag = filtered_df["ReportingLag"].mean() if not filtered_df["ReportingLag"].isna().all() else 0
m1.metric("Total Transactions",      f"{len(filtered_df):,}")
m2.metric("Representatives",         filtered_df["Representative"].nunique())
m3.metric("Unique Tickers",          filtered_df["Ticker"].nunique())
m4.metric("Avg Reporting Lag",       f"{avg_lag:.1f} days")
st.markdown("---")

# ── Main layout ───────────────────────────────────────────────────────────────
col1, col2 = st.columns((2, 1))

with col1:
    st.subheader("Recent Transactions")
    display_cols = ["TransactionDate", "ReportDate", "ReportingLag", "Representative", "House", "Party", "Ticker", "Transaction", "Range"]
    display_df = filtered_df[[c for c in display_cols if c in filtered_df.columns]].copy()

    if not display_df.empty:
        display_df["TransactionDate"] = display_df["TransactionDate"].dt.strftime("%m/%d/%y")
        if "ReportDate" in display_df.columns:
            display_df["ReportDate"] = display_df["ReportDate"].dt.strftime("%m/%d/%y")
        display_df = display_df.rename(columns={
            "TransactionDate": "Trans Date",
            "ReportDate": "Reported",
            "ReportingLag": "Lag (days)",
            "Representative": "Rep",
        })

        def fmt_label_amt(amt):
            s = amt.replace("$", "").strip()
            return "—" if s == "0" else s

        for rep, rep_data in display_df.groupby("Rep", sort=False):
            buy_amt, sell_amt = get_totals(rep_data)
            house  = rep_data["House"].dropna().iloc[0]  if "House"  in rep_data and not rep_data["House"].dropna().empty  else ""
            party  = rep_data["Party"].dropna().iloc[0] if "Party"  in rep_data and not rep_data["Party"].dropna().empty else ""
            badge  = PARTY_BADGE.get(party[:1] if party else "", "⚪")
            count  = len(rep_data)
            last_name = rep.split()[-1].lower() if rep else ""
            fin_badge = "  🏦 Finance Cmte" if last_name in fin_services_members else ""
            label  = f"{badge} {rep} [{party}{'-' + house if house else ''}]{fin_badge}  ·  🟢 {fmt_label_amt(buy_amt)}  🔴 {fmt_label_amt(sell_amt)}  ·  {count} trade{'s' if count != 1 else ''}"

            with st.expander(label):
                st.dataframe(
                    rep_data.drop(columns=["Rep", "House", "Party"], errors="ignore").reset_index(drop=True),
                    use_container_width=True,
                )
    else:
        st.info("No transactions match the current filters.")

with col2:
    st.subheader("Top Traded Tickers")
    if not filtered_df.empty:
        top_tickers = filtered_df["Ticker"].value_counts().head(10).index
        chart_df = filtered_df[filtered_df["Ticker"].isin(top_tickers)].copy()
        chart_df["Transaction"] = chart_df["Transaction"].apply(
            lambda x: "Purchase" if "purchase" in str(x).lower() or "buy" in str(x).lower() else "Sale"
        )
        top_grouped = chart_df.groupby(["Ticker", "Transaction"]).size().reset_index(name="Count")
        fig_bar = px.bar(
            top_grouped, x="Count", y="Ticker", color="Transaction", orientation="h",
            color_discrete_map=BUY_SELL_COLORS,
            labels={"Count": "# Trades", "Ticker": ""},
        )
        fig_bar.update_layout(**PLOT_LAYOUT, height=320, yaxis={"categoryorder": "total ascending"}, legend_title_text="")
        st.plotly_chart(fig_bar, use_container_width=True)

        selected_ticker = st.selectbox(
            "Drill into a ticker",
            options=["—"] + list(top_tickers),
            index=0,
        )

        if selected_ticker != "—":
            st.markdown(f"**{selected_ticker} — Who Traded It**")
            ticker_trades = filtered_df[filtered_df["Ticker"] == selected_ticker].copy()

            rows = []
            for rep, group in ticker_trades.groupby("Representative"):
                party = group["Party"].dropna().iloc[0] if not group["Party"].dropna().empty else ""
                house = group["House"].dropna().iloc[0] if not group["House"].dropna().empty else ""
                buy_amt, sell_amt = get_totals(group)
                buy_num, sell_num = get_totals_numeric(group)
                rows.append({
                    "Rep": rep,
                    "Party": party,
                    "Chamber": house,
                    "Bought": fmt_label_amt(buy_amt),
                    "Sold": fmt_label_amt(sell_amt),
                    "Trades": len(group),
                    "_vol": buy_num + sell_num,
                })

            summary_df = (
                pd.DataFrame(rows)
                .sort_values("_vol", ascending=False)
                .drop(columns=["_vol"])
                .reset_index(drop=True)
            )
            summary_df.index += 1
            st.dataframe(summary_df, use_container_width=True)

# ── Bottom charts ─────────────────────────────────────────────────────────────
col3, col4, col5 = st.columns(3)

with col3:
    st.subheader("Daily Volume")
    if not filtered_df.empty:
        daily = filtered_df.groupby("TransactionDate").size().reset_index(name="Trades")
        fig_line = px.line(daily, x="TransactionDate", y="Trades", markers=True)
        fig_line.update_traces(line_color="#38bdf8", marker_color="#38bdf8")
        fig_line.update_layout(**PLOT_LAYOUT)
        fig_line.update_xaxes(tickformat="%m/%d/%y")
        st.plotly_chart(fig_line, use_container_width=True)

with col4:
    st.subheader("Reporting Lag")
    if not filtered_df.empty and "ReportingLag" in filtered_df.columns:
        fig_hist = px.histogram(
            filtered_df, x="ReportingLag", nbins=20,
            labels={"ReportingLag": "Days to Report"},
            color_discrete_sequence=["#a78bfa"],
        )
        fig_hist.update_layout(**PLOT_LAYOUT, height=300)
        st.plotly_chart(fig_hist, use_container_width=True)

with col5:
    st.subheader("Transaction Mix")
    if not filtered_df.empty and "Transaction" in filtered_df.columns:
        simplified = filtered_df["Transaction"].apply(
            lambda x: "Purchase" if "purchase" in str(x).lower() or "buy" in str(x).lower() else "Sale"
        )
        trans_types = simplified.value_counts().reset_index()
        trans_types.columns = ["Type", "Count"]
        fig_pie = px.pie(
            trans_types, names="Type", values="Count", hole=0.45,
            color="Type", color_discrete_map=BUY_SELL_COLORS,
        )
        fig_pie.update_traces(textfont_color="white")
        fig_pie.update_layout(**PLOT_LAYOUT, height=300, showlegend=True)
        st.plotly_chart(fig_pie, use_container_width=True)

# ── Trade Performance ─────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("Trade Performance — Did They Buy Before It Popped?")
st.caption("Shows purchase transactions ranked by how much the stock moved after the trade.")

buy_df = filtered_df[filtered_df["Transaction"].str.contains("purchase|buy", case=False, na=False)].copy()

if buy_df.empty:
    st.info("No purchase transactions in the current filter.")
else:
    days_choice = st.radio("Return window", [30, 60, 90], horizontal=True, key="perf_window")

    with st.spinner("Fetching price data — this may take a moment on first load..."):
        overall_start = str((buy_df["TransactionDate"].min() - pd.Timedelta(days=5)).date())
        overall_end   = str((pd.Timestamp.now() + pd.Timedelta(days=100)).date())

        perf_rows = []
        for ticker, ticker_df in buy_df.groupby("Ticker"):
            if not ticker or str(ticker).upper() in ("N/A", "NONE", "NAN", ""):
                continue
            prices = get_ticker_prices(str(ticker), overall_start, overall_end)
            if prices.empty:
                continue
            for _, row in ticker_df.iterrows():
                ret = price_return(prices, row["TransactionDate"], days_choice)
                perf_rows.append({
                    "Rep":        row.get("Representative", ""),
                    "Party":      row.get("Party", ""),
                    "Ticker":     ticker,
                    "Trade Date": row["TransactionDate"].strftime("%m/%d/%y"),
                    "Amount":     row.get("Range", ""),
                    f"{days_choice}d Return": f"{ret:+.1f}%" if ret is not None else "—",
                    "_ret":       ret if ret is not None else float("-inf"),
                })

    if perf_rows:
        perf_df = (
            pd.DataFrame(perf_rows)
            .sort_values("_ret", ascending=False)
            .drop(columns=["_ret"])
            .reset_index(drop=True)
        )
        perf_df.index += 1
        st.dataframe(perf_df, use_container_width=True)
    else:
        st.info("Could not retrieve price data for any tickers in this filter.")

# ── Pre-Earnings Flag ─────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("Pre-Earnings Purchases")
st.caption("Purchases made shortly before an earnings report — one of the most common insider trading windows.")

buy_df_e = filtered_df[filtered_df["Transaction"].str.contains("purchase|buy", case=False, na=False)].copy()

if not buy_df_e.empty:
    days_threshold = st.slider("Flag trades within N days of earnings", 7, 60, 30, key="earnings_window")

    with st.spinner("Checking earnings dates..."):
        flagged = []
        for ticker, group in buy_df_e.groupby("Ticker"):
            if not ticker or str(ticker).upper() in ("N/A", "NONE", "NAN", ""):
                continue
            earnings = get_earnings_dates(str(ticker))
            for _, row in group.iterrows():
                trade_date = pd.Timestamp(row["TransactionDate"]).normalize()
                future = [d for d in earnings if d > trade_date]
                if not future:
                    continue
                next_earnings = min(future)
                days_before = (next_earnings - trade_date).days
                if days_before <= days_threshold:
                    flagged.append({
                        "Rep":           row.get("Representative", ""),
                        "Party":         row.get("Party", ""),
                        "Ticker":        ticker,
                        "Trade Date":    trade_date.strftime("%m/%d/%y"),
                        "Earnings Date": next_earnings.strftime("%m/%d/%y"),
                        "Days Before":   days_before,
                        "Amount":        row.get("Range", ""),
                    })

    if flagged:
        flagged_df = (
            pd.DataFrame(flagged)
            .sort_values("Days Before")
            .reset_index(drop=True)
        )
        flagged_df.index += 1
        st.dataframe(flagged_df, use_container_width=True)
        st.caption(f"{len(flagged_df)} trade(s) flagged within {days_threshold} days of an earnings report.")
    else:
        st.success(f"No purchases found within {days_threshold} days of earnings in the current filter.")

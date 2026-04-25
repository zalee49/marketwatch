import re
import requests
import pandas as pd
import streamlit as st
import yfinance as yf
from bs4 import BeautifulSoup

_HEADERS = {"User-Agent": "Mozilla/5.0"}

_QQ_HEADERS = {
    "accept": "application/json",
    "X-CSRFToken": "TyTJwjuEC7VV7mOqZ622haRaaUr0x0Ng4nrwSRFKQs7vdoBcJlK9qjAS69ghzhFu",
    "Authorization": "Token ",
}


@st.cache_data(ttl=3600)
def fetch_congress_trades():
    try:
        r = requests.get(
            "https://api.quiverquant.com/beta/live/congresstrading",
            headers=_QQ_HEADERS,
            timeout=30,
        )
        r.raise_for_status()
        df = pd.DataFrame(r.json())
        df["ReportDate"] = pd.to_datetime(df["ReportDate"])
        df["TransactionDate"] = pd.to_datetime(df["TransactionDate"])
        df["House"] = df["House"].replace("Representatives", "House")
        return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()


def get_totals(df_sub):
    buy_min, buy_max, sell_min, sell_max = 0, 0, 0, 0
    for _, row in df_sub.iterrows():
        tx = str(row.get('Transaction', ''))
        r = str(row.get('Range', ''))
        s = r.replace('$', '').replace(',', '')
        if '-' in s:
            parts = s.split('-')
            try:
                mn, mx = float(parts[0].strip()), float(parts[1].strip())
                if 'Purchase' in tx or 'Buy' in tx:
                    buy_min += mn
                    buy_max += mx
                elif 'Sale' in tx or 'Sell' in tx:
                    sell_min += mn
                    sell_max += mx
            except Exception:
                pass

    def fmt(v):
        if v >= 1_000_000:
            return f"${v / 1_000_000:.1f}M"
        elif v >= 1_000:
            return f"${v / 1_000:.0f}K"
        return f"${v:.0f}"

    buy_str = f"{fmt(buy_min)} - {fmt(buy_max)}" if buy_max > 0 else "$0"
    sell_str = f"{fmt(sell_min)} - {fmt(sell_max)}" if sell_max > 0 else "$0"
    return buy_str, sell_str


def get_totals_numeric(df_sub):
    buy_max, sell_max = 0, 0
    for _, row in df_sub.iterrows():
        tx = str(row.get('Transaction', ''))
        r = str(row.get('Range', ''))
        s = r.replace('$', '').replace(',', '')
        if '-' in s:
            parts = s.split('-')
            try:
                mx = float(parts[1].strip())
                if 'Purchase' in tx or 'Buy' in tx:
                    buy_max += mx
                elif 'Sale' in tx or 'Sell' in tx:
                    sell_max += mx
            except Exception:
                pass
    return buy_max, sell_max


@st.cache_data(ttl=3600)
def get_ticker_prices(ticker, start_str, end_str):
    try:
        data = yf.download(ticker, start=start_str, end=end_str, progress=False, auto_adjust=True)
        if data.empty:
            return pd.Series(dtype=float)
        close = data["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
        close.index = pd.to_datetime(close.index).tz_localize(None)
        return close
    except Exception:
        return pd.Series(dtype=float)


@st.cache_data(ttl=86400)
def get_earnings_dates(ticker):
    try:
        t = yf.Ticker(ticker)
        df = t.earnings_dates
        if df is None or df.empty:
            return []
        idx = df.index
        if hasattr(idx, 'tz') and idx.tz is not None:
            idx = idx.tz_convert(None)
        return sorted(pd.Timestamp(d).normalize() for d in idx)
    except Exception:
        return []


def price_return(prices, trade_date, days):
    try:
        trade_date = pd.Timestamp(trade_date).normalize()
        future_date = trade_date + pd.Timedelta(days=days)
        p0 = prices[prices.index >= trade_date]
        p1 = prices[prices.index >= future_date]
        if p0.empty or p1.empty:
            return None
        return round((float(p1.iloc[0]) - float(p0.iloc[0])) / float(p0.iloc[0]) * 100, 1)
    except Exception:
        return None


_STATES = {
    "Alabama","Alaska","Arizona","Arkansas","California","Colorado","Connecticut",
    "Delaware","Florida","Georgia","Hawaii","Idaho","Illinois","Indiana","Iowa",
    "Kansas","Kentucky","Louisiana","Maine","Maryland","Massachusetts","Michigan",
    "Minnesota","Mississippi","Missouri","Montana","Nebraska","Nevada","New Hampshire",
    "New Jersey","New Mexico","New York","North Carolina","North Dakota","Ohio",
    "Oklahoma","Oregon","Pennsylvania","Rhode Island","South Carolina","South Dakota",
    "Tennessee","Texas","Utah","Vermont","Virginia","Washington","West Virginia",
    "Wisconsin","Wyoming",
}
_ROLES = re.compile(r'Chairman|Chairwoman|Ranking Member|Vice Chair|Member', re.IGNORECASE)


def _parse_member_names(soup):
    members = set()
    for a in soup.select("a[href]"):
        href = a.get("href", "")
        if not re.match(r'https://[\w-]+\.house\.gov/?$', href):
            continue
        if any(x in href for x in ["financialservices", "democrats"]):
            continue
        text = a.get_text(strip=True)
        for state in _STATES:
            text = text.replace(state, "")
        text = _ROLES.sub("", text).strip()
        parts = text.split()
        if len(parts) >= 2:
            members.add(parts[-1].lower().rstrip(",."))
    return members


@st.cache_data(ttl=86400)
def get_financial_services_members():
    headers = {"User-Agent": "Mozilla/5.0"}
    members = set()
    try:
        r = requests.get("https://financialservices.house.gov/about/members.htm", timeout=10, headers=headers)
        members |= _parse_member_names(BeautifulSoup(r.text, "html.parser"))
    except Exception:
        pass
    try:
        r = requests.get("https://www.banking.senate.gov/about/membership", timeout=10, headers=headers)
        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text()
        for match in re.finditer(r'([A-Z][a-záéíóúüñ]+(?: [A-Z][a-záéíóúüñ]+)+)\s*\([RD]\s*[-–]\s*\w', text):
            name = match.group(1).strip()
            parts = name.split()
            if len(parts) >= 2:
                members.add(parts[-1].lower())
    except Exception:
        pass
    try:
        r = requests.get("https://democrats-financialservices.house.gov/about/Committee-membership.htm", timeout=10, headers=headers)
        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text()
        start = text.find("Ranking Member")
        if start != -1:
            section = text[start:start + 2000]
            for line in section.splitlines():
                line = line.strip()
                if "," in line and not any(c.isdigit() for c in line):
                    name_part = line.split(",")[0].strip()
                    parts = name_part.split()
                    if len(parts) >= 2:
                        last = parts[-1].lower().rstrip(",.")
                        if len(last) > 2:
                            members.add(last)
    except Exception:
        pass
    return members

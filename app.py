# --- ส่วนแก้บั๊ก Cache ---
import appdirs as ad
ad.user_cache_dir = lambda *args: "/tmp"

import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import plotly.graph_objects as go

# --- 1. ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Sniper Portfolio & Watchlist", page_icon="🔭", layout="wide")

# CSS ปรับแต่ง (ขยายตัวหนังสือให้ชัดเจน)
st.markdown("""
<style>
    [data-testid="stMetricValue"] { font-size: 2rem !important; font-weight: 700; }
    div[data-testid="stDataFrame"] { font-size: 1.05rem !important; }
    h3 { padding-top: 1rem; border-bottom: 2px solid #333; padding-bottom: 0.5rem;}
</style>
""", unsafe_allow_html=True)

# ปุ่ม Refresh
if st.button('🔄 Refresh Data (Real-time)'):
    st.rerun()

# --- 2. ข้อมูลพอร์ต (16 Dec 2025) ---
start_date_str = "02/10/2025" 
cash_balance_usd = 400.00 # เงินสดกระสุนดินดำ

# เวลาไทย
now = datetime.utcnow() + timedelta(hours=7) 
target_date_str = now.strftime("%d %B %Y %H:%M:%S")

try:
    start_date = datetime.strptime(start_date_str, "%d/%m/%Y")
    invest_days = (now - datetime.combine(start_date, datetime.min.time()) - timedelta(hours=7)).days
except:
    invest_days = 0

# 2.1 พอร์ตหลัก (Main Holdings)
my_portfolio_data = [
    {"Ticker": "AAPL", "Company": "Apple Inc.",            "Avg Cost": 240.2191, "Qty": 0.6695555},
    {"Ticker": "PLTR", "Company": "Palantir Technologies", "Avg Cost": 170.1280, "Qty": 0.5868523},
    {"Ticker": "TSM",  "Company": "Taiwan Semiconductor",  "Avg Cost": 281.3780, "Qty": 0.3548252},
    {"Ticker": "LLY",  "Company": "Eli Lilly and Company", "Avg Cost": 908.8900, "Qty": 0.0856869},
]

# 2.2 Watchlist (หุ้นเก่าที่ย้ายออกไปเฝ้าระวัง)
my_watchlist_tickers = ["AMZN", "NVDA", "V", "VOO"]

# --- 3. ฟังก์ชันดึงราคา (รวมทั้ง Port และ Watchlist) ---
@st.cache_data(ttl=60, show_spinner="Fetching Market Data...") 
def get_all_data(portfolio_data, watchlist_tickers):
    # รวม Ticker ทั้งหมดเพื่อดึงทีเดียว
    port_tickers = [item['Ticker'] for item in portfolio_data]
    all_tickers = list(set(port_tickers + watchlist_tickers))
    
    try:
        usd_thb_data = yf.Ticker("THB=X").history(period="1d")
        usd_thb = usd_thb_data['Close'].iloc[-1] if not usd_thb_data.empty else 31.50
    except:
        usd_thb = 31.50
        
    live_prices = {}
    prev_closes = {}
    
    for t in all_tickers:
        try:
            hist = yf.Ticker(t).history(period="5d")
            if not hist.empty:
                live_prices[t] = hist['Close'].iloc[-1]
                if len(hist) >= 2:
                    prev_closes[t] = hist['Close'].iloc[-2]
                else:
                    prev_closes[t] = live_prices[t]
            else:
                live_prices[t] = 0
                prev_closes[t] = 0
        except:
            live_prices[t] = 0
            prev_closes[t] = 0
            
    return live_prices, prev_closes, usd_thb

# --- 4. ประมวลผล ---
fetched_prices, prev_closes, exchange_rate = get_all_data(my_portfolio_data, my_watchlist_tickers)

# 4.1 คำนวณพอร์ตหลัก
df = pd.DataFrame(my_portfolio_data)
df['Current Price'] = df['Ticker'].map(fetched_prices)
df['Prev Close'] = df['Ticker'].map(prev_closes)
df['Value USD'] = df['Qty'] * df['Current Price']
df['Cost USD'] = df['Qty'] * df['Avg Cost']
df['Total Gain USD'] = df['Value USD'] - df['Cost USD']
df['%G/L'] = ((df['Current Price'] - df['Avg Cost']) / df['Avg Cost']) 
df['Day Change USD'] = (df['Current Price'] - df['Prev Close']) * df['Qty']
df['%Day Change'] = ((df['Current Price'] - df['Prev Close']) / df['Prev Close'])

total_invested_usd = df['Value USD'].sum()
total_equity_usd = total_invested_usd + cash_balance_usd # รวมเงินสด
total_equity_thb = total_equity_usd * exchange_rate

total_gain_usd = df['Total Gain USD'].sum()
total_day_change_usd = df['Day Change USD'].sum()

# 4.2 เตรียมข้อมูล Watchlist
watchlist_data = []
for t in my_watchlist_tickers:
    price = fetched_prices.get(t, 0)
    prev = prev_closes.get(t, 0)
    change = price - prev
    pct_change = (change / prev) if prev > 0 else 0
    watchlist_data.append({
        "Ticker": t,
        "Price": price,
        "Change": change,
        "% Change": pct_change
    })
df_watch = pd.DataFrame(watchlist_data)

# --- 5. แสดงผล (UI) ---
st.title("🔭 Sniper Portfolio & Watchlist")
st.caption(f"Last Update (BKK Time): {target_date_str}")

# Scorecard (รวมเงินสด)
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
col_m1.metric("💰 Total Equity (THB)", f"฿{total_equity_thb:,.0f}", f"Cash: ${cash_balance_usd:,.0f}")
col_m2.metric("📈 Unrealized Gain", f"${total_gain_usd:,.2f}", f"Invested: ${total_invested_usd:,.0f}")
col_m3.metric("📅 Day Change", f"${total_day_change_usd:+.2f}", f"{(total_day_change_usd/total_invested_usd*100):+.2f}%")
col_m4.metric("💱 THB/USD", f"{exchange_rate:.2f}", "Real-time")

st.markdown("---")

col_main, col_side = st.columns([2.5, 1])

# --- ส่วนซ้าย: Main Portfolio ---
with col_main:
    st.subheader(f"🛡️ Main Holdings (Invested + Cash)")
    
    # Format Functions
    def color_text(val):
        if isinstance(val, (int, float)):
            return 'color: #28a745' if val >= 0 else 'color: #dc3545'
        return ''
    
    def format_arrow(val):
        symbol = "⬆️" if val > 0 else "⬇️" if val < 0 else "➖"
        return f"{val:+.2%} {symbol}"

    # ตารางหุ้นหลัก
    display_df = df[['Ticker', 'Qty', 'Avg Cost', 'Current Price', '%Day Change', '%G/L', 'Total Gain USD', 'Value USD']].copy()
    display_df.columns = ['Ticker', 'Qty', 'Avg Cost', 'Price', '% Day', '% Total', 'Gain ($)', 'Value ($)']
    
    st.dataframe(
        display_df.style.format({
            "Qty": "{:.4f}", "Avg Cost": "${:.2f}", "Price": "${:.2f}",
            "% Day": format_arrow, "% Total": format_arrow, "Gain ($)": "${:+.2f}", "Value ($)": "${:.2f}"
        }).map(color_text, subset=['% Day', '% Total', 'Gain ($)']),
        hide_index=True, use_container_width=True
    )
    
    # กราฟวงกลม (โชว์ Cash ชัดๆ)
    st.caption("Asset Allocation (Including Cash)")
    labels = list(df['Ticker']) + ['CASH 💵']
    values = list(df['Value USD']) + [cash_balance_usd]
    # สี: AAPL(เทาเข้ม), PLTR(ส้ม), TSM(แดง), LLY(น้ำเงิน), Cash(เขียวเหนี่ยวทรัพย์)
    colors = ['#333333', '#ff7f0e', '#d62728', '#1f77b4', '#2ca02c'] 
    
    fig_pie = go.Figure(data=[go.Pie(
        labels=labels, values=values, hole=.5,
        marker_colors=colors, textinfo='label+percent'
    )])
    fig_pie.add_annotation(x=0.5, y=0.5, text=f"Total<br>${total_equity_usd:,.0f}", showarrow=False, font=dict(size=14, color="white"))
    fig_pie.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=350, showlegend=True)
    st.plotly_chart(fig_pie, use_container_width=True)

# --- ส่วนขวา: Watchlist ---
with col_side:
    st.subheader("👀 Watchlist")
    
    if not df_watch.empty:
        # แสดงเป็นการ์ดเล็กๆ หรือตารางย่อ
        for index, row in df_watch.iterrows():
            ticker = row['Ticker']
            price = row['Price']
            change = row['Change']
            pct = row['% Change']
            color = "green" if change >= 0 else "red"
            
            st.metric(label=ticker, value=f"${price:.2f}", delta=f"{pct:+.2%} (${change:+.2f})")
            st.markdown("---")

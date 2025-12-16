# --- ส่วนแก้บั๊ก Cache และ Imports ---
import appdirs as ad
ad.user_cache_dir = lambda *args: "/tmp"

import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import plotly.graph_objects as go

# --- 1. ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Sniper Portfolio & Watchlist", page_icon="🔭", layout="wide")

# CSS ปรับแต่ง
st.markdown("""
<style>
    [data-testid="stMetricValue"] { font-size: 2rem !important; font-weight: 700; }
    div[data-testid="stDataFrame"] { font-size: 1.05rem !important; }
    h3 { padding-top: 1rem; border-bottom: 2px solid #333; padding-bottom: 0.5rem;}
    .stAlert { margin-top: 1rem; }
</style>
""", unsafe_allow_html=True)

# ปุ่ม Refresh
if st.button('🔄 Refresh Data (Real-time)'):
    st.rerun()

# --- 2. ข้อมูลพอร์ต (16 Dec 2025) ---
start_date_str = "02/10/2025" 
cash_balance_usd = 400.00 

# เวลาไทย
now = datetime.utcnow() + timedelta(hours=7) 
target_date_str = now.strftime("%d %B %Y %H:%M:%S")

try:
    start_date = datetime.strptime(start_date_str, "%d/%m/%Y")
    invest_days = (now - datetime.combine(start_date, datetime.min.time()) - timedelta(hours=7)).days
except:
    invest_days = 0

# 2.1 พอร์ตหลัก
my_portfolio_data = [
    {"Ticker": "AAPL", "Company": "Apple Inc.",            "Avg Cost": 240.2191, "Qty": 0.6695555},
    {"Ticker": "PLTR", "Company": "Palantir Technologies", "Avg Cost": 170.1280, "Qty": 0.5868523},
    {"Ticker": "TSM",  "Company": "Taiwan Semiconductor",  "Avg Cost": 281.3780, "Qty": 0.3548252},
    {"Ticker": "LLY",  "Company": "Eli Lilly and Company", "Avg Cost": 908.8900, "Qty": 0.0856869},
]

# 2.2 Watchlist Tickers
my_watchlist_tickers = ["AMZN", "NVDA", "V", "VOO", "GOOGL", "META", "MSFT", "TSLA", "PLTR", "AAPL", "TSM", "LLY", "WBD", "AMD", "AVGO"] 

# 2.3 แนวรับ-แนวต้านทางเทคนิค
tech_levels = {
    # Ticker: [ต้าน1, ต้าน2, รับ1, รับ2]
    "AMZN": [230, 244, 216, 212], 
    "AAPL": [280, 288, 268, 260], 
    "GOOGL": [320, 330, 300, 288], 
    "NVDA": [182, 196, 173, 167], 
    "META": [675, 700, 640, 632], 
    "MSFT": [490, 505, 468, 457], 
    "TSLA": [480, 500, 460, 445],
    "PLTR": [195, 205, 180, 175],
    "AMD": [224, 238, 205, 199],
    "AVGO": [350, 370, 335, 316],
    "TSM": [300, 310, 275, 268], 
    "LLY": [1100, 1150, 1000, 980],
    "WBD": [31, 33, 28, 27],
    "V": [355, 365, 340, 330], 
    "VOO": [635, 650, 615, 600]
}

# --- 3. ฟังก์ชันดึงราคา ---
@st.cache_data(ttl=60, show_spinner="Fetching Market Data...") 
def get_all_data(portfolio_data, watchlist_tickers):
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
total_equity_usd = total_invested_usd + cash_balance_usd 
total_equity_thb = total_equity_usd * exchange_rate
total_gain_usd = df['Total Gain USD'].sum()
total_day_change_usd = df['Day Change USD'].sum()

# --- 5. แสดงผล (UI) ---
st.title("🔭 Sniper Portfolio & Watchlist")
st.caption(f"Last Update (BKK Time): {target_date_str}")

# Scorecard
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
col_m1.metric("💰 Total Equity (THB)", f"฿{total_equity_thb:,.0f}", f"Cash: ${cash_balance_usd:,.0f}")
col_m2.metric("📈 Unrealized Gain", f"${total_gain_usd:,.2f}", f"Invested: ${total_invested_usd:,.0f}")
col_m3.metric("📅 Day Change", f"${total_day_change_usd:+.2f}", f"{(total_day_change_usd/total_invested_usd*100):+.2f}%")
col_m4.metric("💱 THB/USD", f"{exchange_rate:.2f}", "Real-time")

# [NEW] AI Strategy Note (แสดงบทวิเคราะห์)
with st.expander("📝 AI Strategy Note (16 Dec 2025) - คลิกเพื่ออ่าน", expanded=True):
    st.markdown("""
    ### 🛡️ X-Ray Portfolio & Sniper Strategy
    * **Core Strength:** **AAPL (38%)** และ **LLY (10%)** คือเสาหลักที่ช่วยแบกพอร์ตในวันที่ตลาดผันผวน ทั้งสองตัวชนะตลาดได้ด้วยปัจจัยพื้นฐานที่แข็งแกร่ง
    * **The Opportunity:** **PLTR ($183)** กำลังย่อตัวลงมาใกล้ **Buy Zone ($180)** มากที่สุด เป็นเป้าหมายหลักในการใช้เงินสด
    * **Cash Management ($400):** * ⚠️ เงินสดมีจำกัด ไม่พอสำหรับซื้อหุ้นใหญ่ที่แจ้งเตือนอย่าง **META ($647)** หรือ **VOO ($625)**
        * ✅ **คำแนะนำ:** โฟกัสกระสุนไปที่ **PLTR** หรือรอเก็บ **NVDA** ที่แนวรับ **$173** ซึ่งอยู่ในวิสัยที่ซื้อได้
    """)

st.markdown("---")

col_main, col_side = st.columns([1.5, 2.5]) 

# --- ส่วนซ้าย: Main Portfolio ---
with col_main:
    st.subheader(f"🛡️ Main Holdings")
    
    def color_text(val):
        if isinstance(val, (int, float)):
            return 'color: #28a745' if val >= 0 else 'color: #dc3545'
        return ''
    
    def format_arrow(val):
        symbol = "⬆️" if val > 0 else "⬇️" if val < 0 else "➖"
        return f"{val:+.2%} {symbol}"

    display_df = df[['Ticker', 'Qty', 'Avg Cost', 'Current Price', '%Day Change', '%G/L', 'Value USD']].copy()
    display_df.columns = ['Ticker', 'Qty', 'Avg Cost', 'Price', '% Day', '% Total', 'Value ($)']
    
    st.dataframe(
        display_df.style.format({
            "Qty": "{:.4f}", "Avg Cost": "${:.2f}", "Price": "${:.2f}",
            "% Day": format_arrow, "% Total": format_arrow, "Value ($)": "${:,.2f}"
        }).map(color_text, subset=['% Day', '% Total']),
        hide_index=True, use_container_width=True
    )
    
    st.caption("Asset Allocation (Including Cash)")
    labels = list(df['Ticker']) + ['CASH 💵']
    values = list(df['Value USD']) + [cash_balance_usd]
    colors = ['#333333', '#ff7f0e', '#d62728', '#1f77b4', '#2ca02c'] 
    
    fig_pie = go.Figure(data=[go.Pie(
        labels=labels, values=values, hole=.5,
        marker_colors=colors, textinfo='label+percent'
    )])
    fig_pie.add_annotation(x=0.5, y=0.5, text=f"Total<br>${total_equity_usd:,.0f}", showarrow=False, font=dict(size=14, color="white"))
    fig_pie.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=350, showlegend=True)
    st.plotly_chart(fig_pie, use_container_width=True)

# --- ส่วนขวา: Watchlist (Sorted & Reordered) ---
with col_side:
    st.subheader("🎯 Sniper Watchlist (Sorted by Action)")
    
    watchlist_data = []
    for t in sorted(list(set(my_watchlist_tickers))): 
        price = fetched_prices.get(t, 0)
        prev = prev_closes.get(t, 0)
        change = price - prev
        pct_change = (change / prev) if prev > 0 else 0
        
        levels = tech_levels.get(t, [0, 0, 0, 0]) 
        s1 = levels[2]
        r1 = levels[0]
        
        # Sniper Logic
        signal = "4. Wait" 
        dist_to_s1 = 999.9
        
        if s1 > 0:
            dist_to_s1 = (price - s1) / s1 * 100 
            
            if price <= s1:
                signal = "1. ✅ IN ZONE"
            elif 0 < dist_to_s1 <= 2.0:
                signal = "2. 🟢 ALERT"
            elif price >= r1:
                signal = "5. 🔴 PROFIT"
            else:
                signal = "3. ➖ Wait"
        
        # Check Affordability
        affordable = price <= cash_balance_usd
        note = "" if affordable else " (🔒 Over Budget)"
        
        watchlist_data.append({
            "Ticker": t,
            "Price": price,
            "% Day": pct_change,
            "Signal": signal, 
            "Dist S1": dist_to_s1/100,
            "รับ 1": levels[2],
            "ต้าน 1": levels[0],
            "Affordable": affordable,
            "Display Signal": signal.split(". ")[1] + note
        })
    
    df_watch = pd.DataFrame(watchlist_data)
    
    # Sort
    df_watch = df_watch.sort_values(by=["Signal", "Dist S1"], ascending=[True, True])

    # Highlight Functions
    def highlight_row(s):
        styles = []
        if not s['Affordable']:
            return ['background-color: rgba(128, 128, 128, 0.1); color: #aaaaaa;'] * len(s)

        if "IN ZONE" in s['Signal']:
            return ['background-color: rgba(40, 167, 69, 0.4)'] * len(s)
        elif "ALERT" in s['Signal']:
            return ['background-color: rgba(40, 167, 69, 0.2)'] * len(s)
        elif "PROFIT" in s['Signal']:
            return ['background-color: rgba(220, 53, 69, 0.2)'] * len(s)
        return [''] * len(s)
    
    def color_dist_s1(val):
        if val < 0: return 'color: #dc3545; font-weight: bold;'
        elif 0 <= val <= 0.02: return 'color: #28a745; font-weight: bold;'
        return ''

    st.dataframe(
        df_watch.style
        .format({
            "Price": "${:.2f}",
            "% Day": format_arrow,
            "Dist S1": "{:+.1%}",
            "รับ 1": "${:.0f}",
            "ต้าน 1": "${:.0f}"
        })
        .apply(highlight_row, axis=1)
        .map(color_dist_s1, subset=['Dist S1']),
        column_config={
            "Display Signal": st.column_config.Column("Status", width="medium"),
            "Ticker": st.column_config.Column("Symbol", width="small"),
            "Price": st.column_config.Column("Price", width="small"),
            "% Day": st.column_config.Column("% Day", width="small"),
            "Signal": None,
            "Affordable": None,
            "Dist S1": st.column_config.Column("Diff S1", help="ระยะห่างจากแนวรับไม้แรก"),
            "รับ 1": st.column_config.Column("Buy Lv.1"),
            "ต้าน 1": st.column_config.Column("Sell Lv.1"),
        },
        column_order=["Display Signal", "Ticker", "Price", "% Day", "Dist S1", "รับ 1", "ต้าน 1"],
        hide_index=True, use_container_width=True
    )

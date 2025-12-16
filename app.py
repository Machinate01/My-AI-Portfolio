# --- ส่วนแก้บั๊ก Cache ---
import appdirs as ad
ad.user_cache_dir = lambda *args: "/tmp"

import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import plotly.graph_objects as go

# --- 1. ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="My Portfolio Tracker", page_icon="🚀", layout="wide")

# CSS ปรับแต่ง
st.markdown("""
<style>
    [data-testid="stMetricValue"] { font-size: 1.8rem; }
    div[data-testid="stMetricLabel"] > label { font-size: 1rem; }
</style>
""", unsafe_allow_html=True)

# ปุ่ม Refresh
if st.button('🔄 Refresh Data (Real-time)'):
    st.rerun()

# --- 2. ข้อมูลพอร์ต (Update: 16 Dec 2025) ---
start_date_str = "02/10/2025" 

# ปรับเวลาเป็นไทย (UTC+7)
now = datetime.utcnow() + timedelta(hours=7) 
target_date_str = now.strftime("%d %B %Y %H:%M:%S")

try:
    start_date = datetime.strptime(start_date_str, "%d/%m/%Y")
    invest_days = (now - datetime.combine(start_date, datetime.min.time()) - timedelta(hours=7)).days
except:
    invest_days = 0

# ข้อมูลหุ้น
my_portfolio_data = [
    # Core & Foundation
    {"Ticker": "VOO",  "Theme": "Core",   "Company": "Vanguard S&P 500 ETF", "Avg Cost": 628.1220, "Qty": 0.0614849, "Change": "New Entry 🛡️"},
    {"Ticker": "V",    "Theme": "Core",   "Company": "Visa Inc",             "Avg Cost": 330.2129, "Qty": 0.2419045, "Change": ""},
    {"Ticker": "AMZN", "Theme": "Core",   "Company": "Amazon.com Inc",       "Avg Cost": 228.0932, "Qty": 0.4157950, "Change": ""},
    # Growth & Innovation
    {"Ticker": "NVDA", "Theme": "Growth", "Company": "NVIDIA Corp",          "Avg Cost": 178.7260, "Qty": 0.3351499, "Change": ""},
    {"Ticker": "TSM",  "Theme": "Growth", "Company": "Taiwan Semiconductor", "Avg Cost": 274.9960, "Qty": 0.1118198, "Change": ""},
    {"Ticker": "LLY",  "Theme": "Growth", "Company": "Eli Lilly and Company", "Avg Cost": 961.8167, "Qty": 0.0707723, "Change": "Moonshot 🚀"},
]

# --- 3. ฟังก์ชันดึงราคา (ดึงย้อนหลัง 2 วันเพื่อเทียบราคาเมื่อวาน) ---
@st.cache_data(ttl=60, show_spinner="Fetching Data...") 
def get_live_data(stock_data):
    ticker_list = [item['Ticker'] for item in stock_data]
    try:
        usd_thb_data = yf.Ticker("THB=X").history(period="1d")
        usd_thb = usd_thb_data['Close'].iloc[-1] if not usd_thb_data.empty else 31.47
    except:
        usd_thb = 31.47
        
    live_prices = {}
    prev_closes = {} # เก็บราคาปิดเมื่อวาน
    
    for t in ticker_list:
        try:
            # ดึงข้อมูล 5 วันย้อนหลังเผื่อติดวันหยุด
            hist = yf.Ticker(t).history(period="5d")
            if not hist.empty:
                live_prices[t] = hist['Close'].iloc[-1]
                # ราคาปิดวันก่อนหน้า (รองสุดท้าย)
                if len(hist) >= 2:
                    prev_closes[t] = hist['Close'].iloc[-2]
                else:
                    prev_closes[t] = live_prices[t] # กรณีข้อมูลไม่พอก็ให้เท่ากันไปเลย
            else:
                live_prices[t] = 0
                prev_closes[t] = 0
        except:
            live_prices[t] = 0
            prev_closes[t] = 0
            
    return live_prices, prev_closes, usd_thb

# --- 4. ประมวลผล ---
fetched_prices, prev_closes, exchange_rate = get_live_data(my_portfolio_data)
df = pd.DataFrame(my_portfolio_data)

df['Current Price'] = df['Ticker'].map(fetched_prices)
df['Prev Close'] = df['Ticker'].map(prev_closes)

# คำนวณมูลค่า
df['Value USD'] = df['Qty'] * df['Current Price']
df['Cost USD'] = df['Qty'] * df['Avg Cost']
df['Total Gain USD'] = df['Value USD'] - df['Cost USD']
df['%G/L'] = ((df['Current Price'] - df['Avg Cost']) / df['Avg Cost']) 

# [NEW] คำนวณ Day Change (กำไร/ขาดทุนวันนี้)
df['Day Change USD'] = (df['Current Price'] - df['Prev Close']) * df['Qty']
df['%Day Change'] = ((df['Current Price'] - df['Prev Close']) / df['Prev Close'])

total_value_usd = df['Value USD'].sum()
df['%Port'] = (df['Value USD'] / total_value_usd) * 100 if total_value_usd > 0 else 0

# ยอดรวม
total_value_thb = total_value_usd * exchange_rate
total_cost_thb = df['Cost USD'].sum() * exchange_rate
total_unrealized_thb = total_value_thb - total_cost_thb
total_pct_gain = (total_unrealized_thb / total_cost_thb) * 100 if total_cost_thb > 0 else 0

# [NEW] ยอดรวม Day Change
total_day_change_usd = df['Day Change USD'].sum()
total_day_change_thb = total_day_change_usd * exchange_rate

# --- 5. แสดงผล (UI) ---
st.title("🚀 My Portfolio Tracker (Live)")
st.caption(f"Last Update (BKK Time): {target_date_str}")

# Scorecard: เพิ่ม Day Change
col_m1, col_m2, col_m3, col_m4 = st.columns(4)

# Net Worth
col_m1.metric("💰 Net Worth (THB)", f"฿{total_value_thb:,.0f}", f"Day {invest_days}")

# [NEW] แสดง Total Gain และ Day Change ในช่องเดียวกัน (หรือแยกก็ได้)
col_m2.metric("📈 Total Gain", f"฿{total_unrealized_thb:,.0f}", f"{total_pct_gain:+.2f}%")

# [NEW] Day Change (ไฮไลท์ของวันนี้)
col_m3.metric("📅 Day Change (THB)", f"฿{total_day_change_thb:,.0f}", f"${total_day_change_usd:+.2f}")

col_m4.metric("💱 THB/USD", f"{exchange_rate:.2f}", "Real-time")

st.markdown("---")

# ฟังก์ชันตาราง (เพิ่มคอลัมน์ Day Change)
def display_styled_table(sub_df, title):
    if sub_df.empty: return
    
    # เลือกคอลัมน์
    display_df = sub_df[[
        'Ticker', 'Qty', 'Avg Cost', 'Current Price', 
        '%Day Change', '%G/L', 'Total Gain USD', 'Value USD', '%Port'
    ]].copy()
    
    display_df.columns = [
        'Ticker', 'Qty', 'Avg Cost', 'Price', 
        '% Day', '% Total', 'Total Gain ($)', 'Value ($)', '%Port'
    ]
    
    def color_text(val):
        if isinstance(val, (int, float)):
            return 'color: #28a745' if val >= 0 else 'color: #dc3545'
        return ''

    st.subheader(title)
    st.dataframe(
        display_df.style.format({
            "Qty": "{:.4f}", "Avg Cost": "${:.2f}", "Price": "${:.2f}",
            "% Day": "{:+.2%}", "% Total": "{:+.2%}", 
            "Total Gain ($)": "${:+.2f}", "Value ($)": "${:.2f}", "%Port": "{:.2f}"
        }).map(color_text, subset=['% Day', '% Total', 'Total Gain ($)']),
        column_config={"%Port": st.column_config.ProgressColumn("%Port", format="%.2f%%", min_value=0, max_value=100)},
        hide_index=True, use_container_width=True
    )

core_df = df[df['Theme'] == "Core"]
growth_df = df[df['Theme'] == "Growth"]
display_styled_table(core_df, "🏛️ Core & Foundation")
display_styled_table(growth_df, "💎 Growth & Innovation")

st.markdown("---")

# Charts
col_c1, col_c2 = st.columns([1, 2])
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b'] 
ticker_colors = {ticker: colors[i % len(colors)] for i, ticker in enumerate(df['Ticker'])}

with col_c1:
    st.subheader("🍰 Allocation")
    # [NEW] Donut Chart with Center Text
    fig_pie = go.Figure(data=[go.Pie(
        labels=df['Ticker'], 
        values=df['Value USD'], 
        hole=.5, # รูใหญ่ขึ้น
        marker_colors=[ticker_colors[t] for t in df['Ticker']],
        textinfo='label+percent'
    )])
    
    # ใส่ข้อความตรงกลาง
    fig_pie.add_annotation(
        x=0.5, y=0.5,
        text=f"Total<br>${total_value_usd:,.0f}",
        showarrow=False,
        font=dict(size=14, color="white")
    )
    
    fig_pie.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=300, showlegend=False)
    st.plotly_chart(fig_pie, use_container_width=True)

with col_c2:
    st.subheader("📊 Total Gain/Loss by Ticker")
    bar_colors = ['#28a745' if gain >= 0 else '#dc3545' for gain in df['Total Gain USD']]
    fig_bar = go.Figure(data=[go.Bar(
        x=df['Ticker'], y=df['Total Gain USD'], 
        marker_color=bar_colors, text=df['Total Gain USD'].apply(lambda x: f"${x:+.2f}"),
        textposition='auto' # แสดงตัวเลขบนแท่ง
    )]) 
    fig_bar.add_hline(y=0, line_width=1, line_dash="dash", line_color="gray") 
    fig_bar.update_layout(
        margin=dict(t=0, b=0, l=0, r=0), height=300,
        yaxis_title="Gain/Loss (USD)"
    )
    st.plotly_chart(fig_bar, use_container_width=True)

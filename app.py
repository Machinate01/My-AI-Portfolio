# --- ส่วนแก้บั๊ก Cache ของ yfinance บน Streamlit Cloud ---
import appdirs as ad
ad.user_cache_dir = lambda *args: "/tmp"

import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import plotly.graph_objects as go

# --- 1. ตั้งค่าหน้าเว็บ ---
st.set_page_config(
    page_title="My Portfolio Tracker",
    page_icon="🚀",
    layout="wide"
)

# ปุ่ม Refresh
if st.button('🔄 Refresh Data (Real-time)'):
    st.rerun()

# --- 2. ข้อมูลพอร์ตล่าสุด (Update: 16 Dec 2025) ---
start_date_str = "02/10/2025" # วันเริ่มลงทุน
now = datetime.now()
target_date_str = now.strftime("%d %B %Y %H:%M:%S")

try:
    start_date = datetime.strptime(start_date_str, "%d/%m/%Y")
    invest_days = (now - start_date).days
except:
    invest_days = 0

# อัปเดตรายชื่อหุ้น จำนวน และต้นทุน ตามข้อมูลล่าสุด
# จัดกลุ่ม: VOO, V, AMZN = Core (ฐาน) | NVDA, TSM, LLY = Growth (เติบโตสูง)
my_portfolio_data = [
    # --- Core & Defensive (ฐานพอร์ต) ---
    {"Ticker": "VOO",  "Theme": "Core",   "Company": "Vanguard S&P 500 ETF", "Avg Cost": 628.1220, "Qty": 0.0614849, "Change": "New Entry 🛡️"},
    {"Ticker": "V",    "Theme": "Core",   "Company": "Visa Inc",             "Avg Cost": 330.2129, "Qty": 0.2419045, "Change": ""},
    {"Ticker": "AMZN", "Theme": "Core",   "Company": "Amazon.com Inc",       "Avg Cost": 228.0932, "Qty": 0.4157950, "Change": ""},
    
    # --- Growth & Innovation (เติบโต) ---
    {"Ticker": "NVDA", "Theme": "Growth", "Company": "NVIDIA Corp",          "Avg Cost": 178.7260, "Qty": 0.3351499, "Change": ""},
    {"Ticker": "TSM",  "Theme": "Growth", "Company": "Taiwan Semiconductor", "Avg Cost": 274.9960, "Qty": 0.1118198, "Change": ""},
    {"Ticker": "LLY",  "Theme": "Growth", "Company": "Eli Lilly and Company", "Avg Cost": 961.8167, "Qty": 0.0707723, "Change": "Moonshot 🚀"},
]

# --- 3. ฟังก์ชันดึงราคา Real-time ---
@st.cache_data(ttl=60, show_spinner="กำลังดึงราคาตลาดล่าสุด...") 
def get_live_data(stock_data):
    ticker_list = [item['Ticker'] for item in stock_data]
    
    # 1. ดึงค่าเงินบาท (USD/THB)
    try:
        usd_thb_data = yf.Ticker("THB=X").history(period="1d")
        if not usd_thb_data.empty:
            usd_thb = usd_thb_data['Close'].iloc[-1]
        else:
            usd_thb = 31.47 # Fallback ตามข้อมูลล่าสุดของคุณ
    except:
        usd_thb = 31.47
        
    # 2. ดึงราคาหุ้น
    live_prices = {}
    for t in ticker_list:
        try:
            hist = yf.Ticker(t).history(period="1d")
            if not hist.empty:
                price = hist['Close'].iloc[-1]
            else:
                price = 0
            live_prices[t] = price
        except:
            live_prices[t] = 0
            
    return live_prices, usd_thb

# --- 4. ประมวลผลข้อมูล ---
fetched_prices, exchange_rate = get_live_data(my_portfolio_data)
df = pd.DataFrame(my_portfolio_data)

# ใส่ราคาปัจจุบัน
df['Current Price'] = df['Ticker'].map(fetched_prices)

# คำนวณกำไร/ขาดทุน
df['Value USD'] = df['Qty'] * df['Current Price']
df['Cost USD'] = df['Qty'] * df['Avg Cost']
df['Total Gain USD'] = df['Value USD'] - df['Cost USD']
df['%G/L'] = ((df['Current Price'] - df['Avg Cost']) / df['Avg Cost']) 

# คำนวณ %Port
total_value_usd = df['Value USD'].sum()
if total_value_usd > 0:
    df['%Port'] = (df['Value USD'] / total_value_usd) * 100 
else:
    df['%Port'] = 0

# --- 5. แสดงผลตาราง (UI Style) ---
def display_styled_table(sub_df, title):
    if sub_df.empty:
        return

    # เลือกคอลัมน์
    display_df = sub_df[[
        'Ticker', 'Company', 'Qty', 'Avg Cost', '%G/L', 'Total Gain USD', 'Value USD', '%Port', 'Change'
    ]].copy()

    # เปลี่ยนชื่อหัวตาราง
    display_df.columns = [
        'Ticker', 'Company', 'Qty', 'Avg Cost', '%G/L', 'Total Gain', 'Value', '%Port', 'Note'
    ]

    # ใส่สีเขียว/แดง
    def color_text(val):
        if isinstance(val, (int, float)):
            color = '#28a745' if val >= 0 else '#dc3545' 
            return f'color: {color}'
        return ''

    styler = display_df.style.format({
        "Qty": "{:.4f}",
        "Avg Cost": "${:.2f}",
        "%G/L": "{:+.2%}",
        "Total Gain": "${:+.2f}",
        "Value": "${:.2f}",
        "%Port": "{:.2f}"
    }).map(color_text, subset=['%G/L', 'Total Gain']) 

    st.subheader(title)
    st.dataframe(
        styler,
        column_config={
            "%Port": st.column_config.ProgressColumn(
                "%Port", format="%.2f%%", min_value=0, max_value=100
            ),
        },
        hide_index=True,
        use_container_width=True
    )

# --- 6. ส่วนหัว ---
st.title("🚀 My Portfolio Tracker (Live)")
st.caption(f"Last Update: {target_date_str}")

# แยกกลุ่มแสดงผล
core_df = df[df['Theme'] == "Core"]
growth_df = df[df['Theme'] == "Growth"]

display_styled_table(core_df, "🏛️ Core & Foundation (VOO, V, AMZN)")
display_styled_table(growth_df, "💎 Growth & Innovation (NVDA, TSM, LLY)")

# --- 7. สรุปยอดรวม (Total Balance) ---
total_value_thb = total_value_usd * exchange_rate
total_cost_thb = df['Cost USD'].sum() * exchange_rate
total_unrealized_thb = total_value_thb - total_cost_thb
total_pct_gain = (total_unrealized_thb / total_cost_thb) * 100 if total_cost_thb > 0 else 0

st.markdown("---")
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 📊 Portfolio Summary")
    st.info(f"Exchange Rate: **{exchange_rate:.2f} THB/USD**")
    
    summary_data = {
        "รายการ (Item)": [
            "🟢 ต้นทุนรวม (Total Cost)", 
            "📈 กำไร/ขาดทุน (Unrealized G/L)", 
            "💰 มูลค่าพอร์ต (Market Value)", 
            "⏳ ระยะเวลาลงทุน"
        ],
        "มูลค่า (Value)": [
            f"฿{total_cost_thb:,.0f} (${df['Cost USD'].sum():,.2f})",
            f"฿{total_unrealized_thb:,.0f} ({total_pct_gain:+.2f}%)",
            f"฿{total_value_thb:,.0f} (${total_value_usd:,.2f})",
            f"{invest_days} วัน" 
        ]
    }
    st.table(pd.DataFrame(summary_data))

with col2:
    # กราฟวงกลม
    fig = go.Figure(data=[go.Pie(
        labels=df['Ticker'], 
        values=df['Value USD'], 
        hole=.4,
        textinfo='label+percent'
    )])
    fig.update_layout(
        title_text="Allocation",
        showlegend=False,
        margin=dict(t=30, b=0, l=0, r=0),
        height=300
    )
    st.plotly_chart(fig, use_container_width=True)

# --- ส่วนแก้บั๊ก Cache ของ yfinance บน Streamlit Cloud (ต้องอยู่บรรทัดแรกๆ) ---
import appdirs as ad
ad.user_cache_dir = lambda *args: "/tmp"

# --- เริ่มโค้ดของคุณ ---
import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime

# --- 1. ตั้งค่าพื้นฐาน ---
st.set_page_config(page_title="Growth Portfolio Holding", layout="wide")

# ปุ่ม Refresh
if st.button('🔄 Refresh Data (Real-time)'):
    st.rerun()

# --- 2. ตั้งค่าข้อมูลพอร์ต ---
# วันที่เริ่มต้นลงทุน (คงเดิม)
start_date_str = "02/10/2025"

# วันที่ปัจจุบัน (Update Today)
now = datetime.now()
target_date_str = now.strftime("%d %B %Y %H:%M:%S")

try:
    start_date = datetime.strptime(start_date_str, "%d/%m/%Y")
    invest_days = (now - start_date).days
except:
    invest_days = 0

# ตั้งค่า Realized Gain (กำไรที่ขายแล้ว)
realized_gain_thb = 0  

# ข้อมูลหุ้น
data = [
    # Core Stock
    {"Ticker": "AMZN", "Theme": "Core",   "Company": "Amazon.com Inc",       "Avg Cost": 228.09, "Qty": 0.4157950, "Change": "Add 6%"},
    {"Ticker": "V",    "Theme": "Core",   "Company": "Visa Inc",             "Avg Cost": 330.21, "Qty": 0.2419045, "Change": ""},
    {"Ticker": "NVDA", "Theme": "Core",   "Company": "NVIDIA Corp",          "Avg Cost": 178.73, "Qty": 0.3351499, "Change": ""},
    {"Ticker": "TSM",  "Theme": "Core",   "Company": "Taiwan Semiconductor", "Avg Cost": 275.00, "Qty": 0.1118198, "Change": "Add 7%"},
    
    # Growth Stock
    {"Ticker": "LLY",  "Theme": "Growth", "Company": "Eli Lilly and Company", "Avg Cost": 961.82, "Qty": 0.0707723, "Change": "Buy"},
    {"Ticker": "WBD",  "Theme": "Growth", "Company": "Warner Bros. Discovery", "Avg Cost": 24.00,  "Qty": 1.2980248, "Change": "Reduce 10%"},
]

# --- 3. ฟังก์ชันดึงราคา Real-time (Live Fetching) ---
@st.cache_data(ttl=60, show_spinner="กำลังดึงราคาตลาดปัจจุบัน...") 
def get_live_data(stock_data):
    ticker_list = [item['Ticker'] for item in stock_data]
    
    # 1. ดึงค่าเงินบาท (USD/THB)
    try:
        # ใช้ yfinance ดึงค่าเงิน
        usd_thb_data = yf.Ticker("THB=X").history(period="1d")
        if not usd_thb_data.empty:
            usd_thb = usd_thb_data['Close'].iloc[-1]
        else:
            usd_thb = 34.5 # ค่าสำรองกรณีดึงไม่ได้
    except:
        usd_thb = 34.5 
        
    # 2. ดึงราคาหุ้น
    live_prices = {}
    for t in ticker_list:
        try:
            # ดึงราคาล่าสุด
            hist = yf.Ticker(t).history(period="1d")
            if not hist.empty:
                price = hist['Close'].iloc[-1]
            else:
                price = 0
            live_prices[t] = price
        except:
            live_prices[t] = 0 # กรณี Error ให้เป็น 0
            
    return live_prices, usd_thb

# --- 4. ประมวลผลข้อมูล (Processing) ---
# เรียกใช้ฟังก์ชันดึงราคา
fetched_prices, exchange_rate = get_live_data(data)

df = pd.DataFrame(data)

# Map ราคาที่ดึงมาใส่ใน DataFrame
df['Current Price'] = df['Ticker'].map(fetched_prices)

# คำนวณตัวเลข
df['Value USD'] = df['Qty'] * df['Current Price']
df['Cost USD'] = df['Qty'] * df['Avg Cost']
df['Total Gain USD'] = df['Value USD'] - df['Cost USD']
df['%G/L'] = ((df['Current Price'] - df['Avg Cost']) / df['Avg Cost']) 

# คำนวณ %Port (คูณ 100 เพื่อให้กราฟเต็มหลอด)
total_value_usd = df['Value USD'].sum()
if total_value_usd > 0:
    df['%Port'] = (df['Value USD'] / total_value_usd) * 100 
else:
    df['%Port'] = 0

# --- 5. ฟังก์ชันแสดงตาราง (UI) ---
def display_styled_table(sub_df, title):
    if sub_df.empty:
        return

    display_df = sub_df[[
        'Ticker', 'Company', 'Qty', 'Avg Cost', '%G/L', 'Total Gain USD', 'Value USD', '%Port', 'Change'
    ]].copy()

    display_df.columns = [
        'Ticker', 'Company', 'จำนวนหุ้น', 'Avg Cost basis', '%G/L', 'Total Gain', 'Value', '%Port', 'การเปลี่ยนแปลง'
    ]

    def color_text(val):
        if isinstance(val, (int, float)):
            color = '#28a745' if val >= 0 else '#dc3545' 
            return f'color: {color}'
        return ''

    styler = display_df.style.format({
        "จำนวนหุ้น": "{:.4f}",
        "Avg Cost basis": "${:.2f}",
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

# --- 6. แสดงผลหน้าจอ ---
st.title("Growth Portfolio Holding (Live)")
st.caption(f"Last Update: {target_date_str}")

core_df = df[df['Theme'] == "Core"]
growth_df = df[df['Theme'] == "Growth"]

display_styled_table(core_df, "🌳 Core Stock")
display_styled_table(growth_df, "💎 Growth Stock")

# --- 7. ส่วนสรุปยอด (Total Balance) ---
total_value_thb = total_value_usd * exchange_rate
total_cost_thb = df['Cost USD'].sum() * exchange_rate
total_unrealized_thb = total_value_thb - total_cost_thb
total_pct_gain = (total_unrealized_thb / total_cost_thb) * 100 if total_cost_thb > 0 else 0

st.markdown("<br>", unsafe_allow_html=True)
_, col_summary, _ = st.columns([1, 2, 1])

with col_summary:
    st.markdown("### 📊 Total Balance")
    st.caption(f"Exchange Rate: {exchange_rate:.2f} THB/USD")
    
    summary_data = {
        "Item": [
            "🟢 ต้นทุน", 
            "📈 Unrealized G/L", 
            "💰 มูลค่าปัจจุบัน", 
            "🌊 Cash Flow", 
            "💎 มูลค่ารวมทั้งหมด", 
            "💵 Realized G/L", 
            "⏳ จำนวนวันที่ลงทุน"
        ],
        "Value": [
            f"฿{total_cost_thb:,.0f}",
            f"฿{total_unrealized_thb:,.0f} ({total_pct_gain:+.2f}%)",
            f"฿{total_value_thb:,.0f} (${total_value_usd:,.2f})",
            f"0",
            f"฿{total_value_thb:,.0f}",
            f"฿{realized_gain_thb:,.0f}",
            f"{invest_days} วัน" 
        ]
    }
    
    st.dataframe(
        pd.DataFrame(summary_data),
        column_config={
            "Item": st.column_config.TextColumn("รายการ"),
            "Value": st.column_config.TextColumn("มูลค่า"),
        },
        hide_index=True,
        use_container_width=True
    )

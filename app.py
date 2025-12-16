# ... (ส่วนต้นของไฟล์เหมือนเดิม) ...

# 2.3 แนวรับ-แนวต้านทางเทคนิค (เพิ่ม V และ VOO ให้แล้ว)
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
    # [NEW] เพิ่มข้อมูล V และ VOO (ตัวเลขสมมติอิงกราฟปัจจุบัน)
    "V": [355, 365, 340, 330], 
    "VOO": [635, 650, 615, 600]
}

# ... (ข้ามมาส่วนแสดงผล Watchlist ด้านล่างสุด) ...

# --- ส่วนขวา: Watchlist (พร้อมระบบเรียงลำดับความสำคัญ) ---
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
        
        signal = "4. Wait" # ใส่ตัวเลขนำหน้าเพื่อให้ Sort ได้ง่าย
        dist_to_s1 = 999.9 # ค่า Default ไกลๆ
        
        if s1 > 0:
            dist_to_s1 = (price - s1) / s1 * 100 
            
            if price <= s1:
                signal = "1. ✅ IN ZONE" # Priority สูงสุด
            elif 0 < dist_to_s1 <= 2.0:
                signal = "2. 🟢 ALERT"   # Priority รองลงมา
            elif price >= r1:
                signal = "5. 🔴 PROFIT"  # อยู่ล่างสุด
            else:
                signal = "3. ➖ Wait"    # รอ
        
        watchlist_data.append({
            "Ticker": t,
            "Price": price,
            "% Day": pct_change,
            "Signal": signal, 
            "Dist S1": dist_to_s1/100,
            "รับ 1": levels[2],
            "ต้าน 1": levels[0]
        })
    
    df_watch = pd.DataFrame(watchlist_data)
    
    # [NEW] เรียงลำดับข้อมูล: ให้ตัวที่มีสัญญาณ (เลขน้อย) ขึ้นก่อน
    df_watch = df_watch.sort_values(by=["Signal", "Dist S1"], ascending=[True, True])

    # ตัดตัวเลขนำหน้า Signal ออกตอนแสดงผล (เพื่อความสวยงาม)
    df_watch['Display Signal'] = df_watch['Signal'].apply(lambda x: x.split(". ")[1])

    def highlight_signal(s):
        # ใช้คอลัมน์เดิมในการเช็คเงื่อนไข
        if "IN ZONE" in s['Signal']:
            return ['background-color: rgba(40, 167, 69, 0.4)'] * len(s)
        elif "ALERT" in s['Signal']:
            return ['background-color: rgba(40, 167, 69, 0.2)'] * len(s)
        elif "PROFIT" in s['Signal']:
            return ['background-color: rgba(220, 53, 69, 0.2)'] * len(s)
        return [''] * len(s)

    st.dataframe(
        df_watch.style
        .format({
            "Price": "${:.2f}",
            "% Day": format_arrow,
            "Dist S1": "{:+.1%}",
            "รับ 1": "${:.0f}",
            "ต้าน 1": "${:.0f}"
        })
        .apply(highlight_signal, axis=1),
        column_config={
            "Ticker": st.column_config.Column("Symbol", width="small"),
            "Price": st.column_config.Column("Price", width="small"),
            "% Day": st.column_config.Column("% Day", width="small"),
            "Display Signal": st.column_config.Column("Action", width="small"), # โชว์ตัวที่ตัดเลขแล้ว
            "Signal": None, # ซ่อนคอลัมน์ที่ใช้ Sort
            "Dist S1": st.column_config.Column("Diff S1", help="ระยะห่างจากแนวรับไม้แรก"),
            "รับ 1": st.column_config.Column("Buy Lv.1"),
            "ต้าน 1": st.column_config.Column("Sell Lv.1"),
        },
        hide_index=True, use_container_width=True
    )

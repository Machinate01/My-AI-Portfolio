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
    
    # Sort: เอา Action ขึ้นก่อน
    df_watch = df_watch.sort_values(by=["Signal", "Dist S1"], ascending=[True, True])
    df_watch['Action'] = df_watch['Signal'].apply(lambda x: x.split(". ")[1]) # สร้างคอลัมน์ชื่อ Action

    # [NEW] จัดลำดับคอลัมน์ใหม่ (Action มาก่อน)
    df_watch = df_watch[['Action', 'Ticker', 'Price', '% Day', 'Dist S1', 'รับ 1', 'ต้าน 1', 'Signal']]

    # Highlight Functions
    def highlight_signal(s):
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
        .apply(highlight_signal, axis=1)
        .map(color_dist_s1, subset=['Dist S1']),
        column_config={
            "Action": st.column_config.Column("Status", width="small"), # ย้ายมาซ้ายสุด
            "Ticker": st.column_config.Column("Symbol", width="small"),
            "Price": st.column_config.Column("Price", width="small"),
            "% Day": st.column_config.Column("% Day", width="small"),
            "Signal": None, # ซ่อนคอลัมน์ที่ใช้ Sort
            "Dist S1": st.column_config.Column("Diff S1", help="ระยะห่างจากแนวรับไม้แรก"),
            "รับ 1": st.column_config.Column("Buy Lv.1"),
            "ต้าน 1": st.column_config.Column("Sell Lv.1"),
        },
        hide_index=True, use_container_width=True
    )

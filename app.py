# --- ส่วนขวา: Watchlist (พร้อมระบบ Sniper Signal) ---
with col_side:
    st.subheader("🎯 Sniper Watchlist (Signals)")
    
    # เตรียมข้อมูล Watchlist พร้อม Logic ใหม่
    watchlist_data = []
    for t in sorted(list(set(my_watchlist_tickers))): 
        price = fetched_prices.get(t, 0)
        prev = prev_closes.get(t, 0)
        change = price - prev
        pct_change = (change / prev) if prev > 0 else 0
        
        levels = tech_levels.get(t, [0, 0, 0, 0]) # [R1, R2, S1, S2]
        s1 = levels[2]
        r1 = levels[0]
        
        # Sniper Logic: คำนวณสัญญาณ
        signal = "➖ Wait"
        dist_to_s1 = 0
        
        if s1 > 0:
            dist_to_s1 = (price - s1) / s1 * 100 # ระยะห่างเป็น %
            
            if price <= s1:
                signal = "✅ IN ZONE" # ราคาต่ำกว่าหรือเท่ากับแนวรับ
            elif 0 < dist_to_s1 <= 2.0: # ราคาอยู่เหนือแนวรับไม่เกิน 2%
                signal = "🟢 ALERT" 
            elif price >= r1:
                signal = "🔴 PROFIT" # ชนแนวต้าน
        
        watchlist_data.append({
            "Ticker": t,
            "Price": price,
            "% Day": pct_change,
            "Signal": signal,  # คอลัมน์ใหม่
            "Dist S1": dist_to_s1/100, # ระยะห่าง
            "รับ 1": levels[2], # S1 (แก้ index ให้ตรงกับ tech_levels: R1, R2, S1, S2)
            "ต้าน 1": levels[0]  # R1
        })
    
    df_watch = pd.DataFrame(watchlist_data)

    # ฟังก์ชันไฮไลท์สีทั้งแถวเมื่อมีสัญญาณ
    def highlight_signal(s):
        if "IN ZONE" in s['Signal']:
            return ['background-color: rgba(40, 167, 69, 0.4)'] * len(s) # เขียวเข้ม
        elif "ALERT" in s['Signal']:
            return ['background-color: rgba(40, 167, 69, 0.2)'] * len(s) # เขียวอ่อน
        elif "PROFIT" in s['Signal']:
            return ['background-color: rgba(220, 53, 69, 0.2)'] * len(s) # แดงอ่อน
        return [''] * len(s)

    st.dataframe(
        df_watch.style
        .format({
            "Price": "${:.2f}",
            "% Day": format_arrow,
            "Dist S1": "{:+.1%}", # แสดงระยะห่างเป็น %
            "รับ 1": "${:.0f}",
            "ต้าน 1": "${:.0f}"
        })
        .apply(highlight_signal, axis=1),
        column_config={
            "Ticker": st.column_config.Column("Symbol", width="small"),
            "Price": st.column_config.Column("Price", width="small"),
            "% Day": st.column_config.Column("% Day", width="small"),
            "Signal": st.column_config.Column("Action", width="small"), # ช่องนี้สำคัญสุด
            "Dist S1": st.column_config.Column("Diff S1", help="ระยะห่างจากแนวรับไม้แรก"),
            "รับ 1": st.column_config.Column("Buy Lv.1"),
            "ต้าน 1": st.column_config.Column("Sell Lv.1"),
        },
        hide_index=True, use_container_width=True
    )

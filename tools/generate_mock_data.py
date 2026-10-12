import os
import sqlite3
import random
from datetime import datetime, timedelta

def inject_mock_data():
    # Demo database lang ang ginagalaw (hindi ang totoong bakesync.db)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    db_path = os.path.join(base_dir, "data", "bakesync_demo.db")

    if not os.path.exists(db_path):
        print(f"❌ Error: Hindi mahanap ang database sa {db_path}")
        print("Paki-run muna ang main app para magawa ang 'db' folder at database.")
        return

    # 3. Kumonekta gamit ang tamang path
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    today = datetime.now()

    # I-check kung may laman na ang Products table
    cursor.execute("SELECT id FROM products LIMIT 5")
    products = [row[0] for row in cursor.fetchall()]
    
    if not products:
        print("❌ Walang nakitang products sa database. Paki-run muna ang main app mo para ma-initialize ang demo products.")
        return

    print("⏳ Injecting 30 days of mock historical data... Please wait.")

    # Burahin muna ang lumang test data para malinis ang charts
    cursor.execute("DELETE FROM reconciliation")
    cursor.execute("DELETE FROM waste_logs")
    cursor.execute("DELETE FROM production_schedule")

    # Mag-loop pabalik mula 30 days ago hanggang ngayon
    for i in range(30, -1, -1):
        target_date = today - timedelta(days=i)
        date_str = target_date.strftime("%Y-%m-%d")
        time_str = target_date.strftime("%Y-%m-%d 18:00:00") # 6:00 PM EOD closing time

        # ==========================================
        # 1. RECONCILIATION DATA (UPWARD TREND)
        # ==========================================
        # Base sales is 3000, tumataas ng ~150 per day para maging "GROWING" sa ML
        trend_multiplier = (30 - i) * 150
        actual_cash = 3000 + trend_multiplier + random.randint(-500, 800)
        system_sales = actual_cash + random.randint(-50, 50) # May konting variance
        variance = actual_cash - system_sales

        cursor.execute("""
            INSERT INTO reconciliation (date, system_sales, actual_cash, variance, status, created_at)
            VALUES (?, ?, ?, ?, 'Closed', ?)
        """, (date_str, system_sales, actual_cash, variance, time_str))

        # ==========================================
        # 2. PRODUCTION & WASTE DATA (FORECASTING)
        # ==========================================
        for pid in products:
            # Gumawa ng Production Record
            base_qty = random.randint(100, 250)
            if pid == 1: base_qty += 150 # I-force na mataas ang volume ng Pandesal

            cursor.execute("""
                INSERT INTO production_schedule (product_id, forecast_qty, special_order_qty, status, scheduled_date)
                VALUES (?, ?, 0, 'Done', ?)
            """, (pid, base_qty, date_str))

            # Gumawa ng Waste Record (5% to 20% ng na-produce ang nasisira)
            waste_qty = int(base_qty * random.uniform(0.05, 0.20))
            
            # Randomize kung Market Spoilage o Kitchen Waste (Mas madalas ang Market Spoilage)
            waste_type = random.choice(['Market Spoilage', 'Market Spoilage', 'Kitchen Waste'])

            if waste_qty > 0:
                cursor.execute("""
                    INSERT INTO waste_logs (product_id, waste_type, quantity, reason, created_at)
                    VALUES (?, ?, ?, 'System Generated Mock Data', ?)
                """, (pid, waste_type, waste_qty, time_str))

    # I-save sa database
    conn.commit()
    conn.close()
    print("✅ SUCCESS! 30 days of data injected successfully. You can now open Analytics!")

if __name__ == "__main__":
    inject_mock_data()
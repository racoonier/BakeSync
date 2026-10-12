import random
from datetime import datetime, timedelta
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bakesync.core.database import DatabaseManager

def inject_mock_data():
    db_manager = DatabaseManager("bakesync_demo.db")  # Demo database lang, hindi ang totoong data
    conn = db_manager.conn
    c = conn.cursor()

    print("Kumokonekta sa database at nililinis ang lumang test data...")
    c.execute("DELETE FROM sales")
    c.execute("DELETE FROM waste_logs")
    c.execute("DELETE FROM reconciliation")
    c.execute("DELETE FROM void_logs")
    c.execute("DELETE FROM ingredients") # Linisin pati ingredients
    c.execute("DELETE FROM products") # Linisin pati products

    # 1. GUMAWA NG MGA TEST PRODUCTS
    products = [
        ("Pandesal", 3.00, 1.50, 500, "bread"),
        ("Spanish Bread", 5.00, 2.50, 200, "bread"),
        ("Ensaymada", 10.00, 6.00, 150, "bread"),
        ("Monay", 5.00, 2.00, 300, "bread"),
        ("Coke Mismo", 25.00, 18.00, 50, "beverage"),
        ("Peanut Butter", 55.00, 40.00, 20, "spread")
    ]

    product_ids = []
    for p in products:
        c.execute("SELECT id FROM products WHERE name = ?", (p[0],))
        existing = c.fetchone()
        if not existing:
            c.execute("""
                INSERT INTO products (name, retail_price, production_cost, stock_qty, product_type, is_archived) 
                VALUES (?, ?, ?, ?, ?, 0)
            """, p)
            product_ids.append(c.lastrowid)
        else:
            product_ids.append(existing[0])

    # 🟢 1.5. GUMAWA NG MGA TEST INGREDIENTS PARA SA DASHBOARD ALERTS
    ingredients = [
        ("Bread Flour", 50, "kg", 15),       # Optimal Status
        ("White Sugar", 5, "kg", 3),         # Low Warning Status
        ("Yeast", 0, "kg", 0.5),             # Out of Stock Status
        ("Salt", 10, "kg", 0.5),             # Optimal Status
        ("Butter", 2, "kg", 1),              # Low Warning Status
        ("Cooking Oil", 20, "L", 2)          # Optimal Status
    ]
    
    for ing in ingredients:
        c.execute("SELECT id FROM ingredients WHERE name = ?", (ing[0],))
        if not c.fetchone():
            c.execute("""
                INSERT INTO ingredients (name, bulk_qty, unit, avg_daily_usage, is_archived) 
                VALUES (?, ?, ?, ?, 0)
            """, ing)

    # 2. MAG-GENERATE NG SALES DATA (30 DAYS)
    print("Nagge-generate ng makatotohanang Sales History (30 Days)...")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    current_date = start_date
    total_sales_added = 0
    total_recon_added = 0

    while current_date <= end_date:
        is_weekend = current_date.weekday() >= 5
        transactions_per_day = random.randint(30, 60) if is_weekend else random.randint(15, 40)
        daily_system_sales = 0.0
        
        for _ in range(transactions_per_day):
            hour = random.choice([6, 7, 8, 9, 15, 16, 17, 18])
            minute = random.randint(0, 59)
            txn_date = current_date.replace(hour=hour, minute=minute, second=0)
            
            prod_id = random.choices(product_ids, weights=[40, 20, 15, 15, 8, 2], k=1)[0]
            
            c.execute("SELECT retail_price FROM products WHERE id = ?", (prod_id,))
            price = c.fetchone()[0]
            qty = random.randint(1, 20)
            amount = qty * price
            
            is_voided = 1 if random.random() < 0.05 else 0 
            
            if is_voided:
                c.execute("""
                    INSERT INTO void_logs (product_id, quantity, amount, reason, created_at)
                    VALUES (?, ?, ?, 'Customer Cancelled', ?)
                """, (prod_id, qty, amount, txn_date.strftime('%Y-%m-%d %H:%M:%S')))
            else:
                daily_system_sales += amount

            c.execute("""
                INSERT INTO sales (product_id, quantity, amount, cashier, tendered, change_given, is_voided, created_at)
                VALUES (?, ?, ?, 'Admin', ?, 0, ?, ?)
            """, (prod_id, qty, amount, amount, is_voided, txn_date.strftime('%Y-%m-%d %H:%M:%S')))
            total_sales_added += 1

        # 3. EOD RECONCILIATION PARA SA ANALYTICS
        if daily_system_sales > 0:
            variance = random.choice([0, 0, 0, 5, -5, 10, -10])
            actual_cash = daily_system_sales + variance
            recon_time = current_date.replace(hour=23, minute=30, second=0).strftime('%Y-%m-%d %H:%M:%S')

            c.execute("""
                INSERT INTO reconciliation (date, system_sales, actual_cash, variance, status, created_at)
                VALUES (?, ?, ?, ?, 'Submitted', ?)
            """, (current_date.strftime('%Y-%m-%d'), daily_system_sales, actual_cash, variance, recon_time))
            total_recon_added += 1

        current_date += timedelta(days=1)

    # 4. MAG-GENERATE NG WASTE LOGS PARA SA PIE CHART
    print("Nagge-generate ng Waste Logs para sa Analytics...")
    c.execute("SELECT id FROM products WHERE product_type = 'bread'")
    bread_ids = [row[0] for row in c.fetchall()]

    for _ in range(30):
        days_ago = random.randint(1, 30)
        waste_date = datetime.now() - timedelta(days=days_ago)
        prod_id = random.choice(bread_ids)
        waste_type = random.choice(["Market Spoilage", "Kitchen Waste"])
        qty = random.randint(5, 30)
        
        c.execute("""
            INSERT INTO waste_logs (product_id, waste_type, quantity, reason, created_at)
            VALUES (?, ?, ?, 'Mock Data Spoilage', ?)
        """, (prod_id, waste_type, qty, waste_date.strftime('%Y-%m-%d %H:%M:%S')))

    conn.commit()
    conn.close()

    print("\n✅ DATA INJECTION COMPLETE!")
    print(f"➜ Added {total_sales_added} Sales & Void Transactions")
    print(f"➜ Added {total_recon_added} EOD Reconciliations")
    print("➜ Added 6 Test Ingredients for Dashboard Alerts")
    print("Restart BakeSync and check your Dashboard Module now!")

if __name__ == "__main__":
    inject_mock_data()
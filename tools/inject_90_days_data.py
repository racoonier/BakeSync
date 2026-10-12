import os
import sqlite3
import random
from datetime import datetime, timedelta

def inject_90_days_data():
    # Demo database lang ang ginagalaw (hindi ang totoong bakesync.db)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "data", "bakesync_demo.db")

    if not os.path.exists(db_path):
        print(f"❌ Error: Hindi mahanap ang database sa {db_path}")
        print("Paki-run muna ang main app para magawa ang database.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("⏳ Naglilinis ng lumang transactional data para sa malinis na 3-month charts...")
    # Clean up old data to prevent duplication
    cursor.execute("DELETE FROM sales")
    cursor.execute("DELETE FROM pos_sessions")
    cursor.execute("DELETE FROM reconciliation")
    cursor.execute("DELETE FROM waste_logs")
    cursor.execute("DELETE FROM production_schedule")
    cursor.execute("DELETE FROM operating_expenses")
    conn.commit()

    # CHECK PRODUCTS: Kung walang products, mag-iinject tayo para hindi mag-error
    cursor.execute("SELECT id, name, retail_price FROM products WHERE is_archived = 0")
    products = cursor.fetchall()
    
    if not products:
        print("⚠️ Walang nakitang products. Nag-iinject ng default bakery products...")
        default_products = [
            ('Pandesal', 3.0, 1.5, 'bread'),
            ('Ensaymada', 15.0, 8.0, 'bread'),
            ('Spanish Bread', 10.0, 5.0, 'bread'),
            ('Monay', 5.0, 2.5, 'bread'),
            ('Pan de Coco', 12.0, 6.0, 'bread'),
            ('Cheese Bread', 8.0, 4.0, 'bread')
        ]
        for p in default_products:
            cursor.execute("""
                INSERT INTO products (name, retail_price, production_cost, product_type) 
                VALUES (?, ?, ?, ?)
            """, p)
        conn.commit()
        cursor.execute("SELECT id, name, retail_price FROM products WHERE is_archived = 0")
        products = cursor.fetchall()

    today = datetime.now()
    total_days = 90
    cashiers = ['Jane Cashier', 'Admin User']
    
    print(f"📈 Nag-iinject ng napakadetalyeng dataset para sa nakaraang {total_days} na araw...")

    # Loop 90 days pabalik hanggang ngayon
    for i in range(total_days, -1, -1):
        current_date = today - timedelta(days=i)
        date_str = current_date.strftime("%Y-%m-%d")
        
        # Randomize opening and closing times for realism (e.g., 6 AM to 6 PM)
        open_time = current_date.replace(hour=random.randint(5, 7), minute=random.randint(0, 59))
        close_time = current_date.replace(hour=random.randint(17, 19), minute=random.randint(0, 59))
        
        open_time_str = open_time.strftime("%Y-%m-%d %H:%M:%S")
        close_time_str = close_time.strftime("%Y-%m-%d %H:%M:%S")
        cashier = random.choice(cashiers)

        # 1. CREATE POS SESSION
        cursor.execute("""
            INSERT INTO pos_sessions (opened_at, closed_at, closed_by, status)
            VALUES (?, ?, ?, 'Closed')
        """, (open_time_str, close_time_str, cashier))
        session_id = cursor.lastrowid

        daily_total_sales = 0.0
        daily_total_txns = random.randint(15, 50) # 15 to 50 customers per day

        # 2. GENERATE DETAILED SALES PER DAY
        for txn in range(daily_total_txns):
            # Pick 1 to 3 random products per transaction
            num_items = random.randint(1, 3)
            txn_time = open_time + timedelta(minutes=random.randint(10, 600))
            txn_time_str = txn_time.strftime("%Y-%m-%d %H:%M:%S")

            for _ in range(num_items):
                prod = random.choice(products)
                prod_id = prod[0]
                prod_price = prod[2]
                
                # Mas maraming binibiling Pandesal (ID 1 usually) kaysa iba
                qty = random.randint(10, 50) if "Pandesal" in prod[1] else random.randint(1, 10)
                amount = qty * prod_price
                daily_total_sales += amount

                # Tendered at Change para realistic ang POS data
                tendered = amount + random.choice([0, 20, 50, 100, 500])
                change = tendered - amount if tendered > amount else 0

                cursor.execute("""
                    INSERT INTO sales (product_id, quantity, amount, session_id, cashier, tendered, change_given, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (prod_id, qty, amount, session_id, cashier, tendered, change, txn_time_str))

        # Update POS session totals
        cursor.execute("""
            UPDATE pos_sessions 
            SET total_sales = ?, total_txns = ? 
            WHERE id = ?
        """, (daily_total_sales, daily_total_txns, session_id))

        # 3. PRODUCTION & WASTE LOGS
        for prod in products:
            prod_id = prod[0]
            # Production is usually 10% to 30% higher than actual sales
            base_forecast = random.randint(50, 200)
            if "Pandesal" in prod[1]:
                base_forecast += 300 

            cursor.execute("""
                INSERT INTO production_schedule (product_id, forecast_qty, status, scheduled_date)
                VALUES (?, ?, 'Done', ?)
            """, (prod_id, base_forecast, date_str))

            # Waste generation (3% to 12% of forecast)
            waste_qty = int(base_forecast * random.uniform(0.03, 0.12))
            if waste_qty > 0:
                waste_type = random.choice(['Market Spoilage', 'Kitchen Waste'])
                reason = "Expired shelf life" if waste_type == 'Market Spoilage' else "Burnt/Mishandled"
                
                cursor.execute("""
                    INSERT INTO waste_logs (product_id, waste_type, quantity, reason, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (prod_id, waste_type, waste_qty, reason, close_time_str))

        # 4. OPERATING EXPENSES (OpEx) - Haluang daily at monthly bills
        if random.random() < 0.3:  # 30% chance may random daily expense (pamasahe, gas, etc.)
            expense_amt = random.uniform(100, 500)
            cursor.execute("""
                INSERT INTO operating_expenses (expense_name, amount, expense_date, logged_by, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (random.choice(['Transportation', 'Cleaning Supplies', 'Drinking Water']), expense_amt, date_str, cashier, close_time_str))
        
        # Monthly bills tuwing katapusan ng buwan (roughly every 30 days logic for mock data)
        if current_date.day == 28:
            cursor.execute("""
                INSERT INTO operating_expenses (expense_name, amount, expense_date, logged_by, created_at)
                VALUES ('Electricity & Water Bill', ?, ?, ?, ?)
            """, (random.uniform(5000, 8000), date_str, 'Admin User', close_time_str))
            
            cursor.execute("""
                INSERT INTO operating_expenses (expense_name, amount, expense_date, logged_by, created_at)
                VALUES ('Shop Rent', 15000.00, ?, ?, ?)
            """, (date_str, 'Admin User', close_time_str))

        # 5. RECONCILIATION DATA
        # Actual cash is slightly off sometimes (short or over by a few pesos)
        variance = random.choice([0, 0, 0, 0, random.uniform(-50, -5), random.uniform(5, 30)]) 
        actual_cash = daily_total_sales + variance

        # Denominations string simulation
        denoms = f"1000x{int(actual_cash//1000)}, 500x1, 100x5" 

        cursor.execute("""
            INSERT INTO reconciliation (date, system_sales, actual_cash, variance, status, denominations, verified_by, created_at)
            VALUES (?, ?, ?, ?, 'Closed', ?, 'Admin User', ?)
        """, (date_str, daily_total_sales, actual_cash, variance, denoms, close_time_str))

    # I-SAVE ANG LAHAT SA DATABASE
    conn.commit()
    conn.close()
    print("✅ SUCCESS! 90 days of complete, highly-detailed data injected successfully.")
    print("Maaari mo nang buksan ang Analytics dashboard mo!")

if __name__ == "__main__":
    inject_90_days_data()
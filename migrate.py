"""Migration script to add history columns to orders table in Supabase"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: Supabase credentials not found in .env")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Test: try to read orders to see current columns
try:
    res = supabase.table("orders").select("*").limit(1).execute()
    print("Current orders columns:", list(res.data[0].keys()) if res.data else "No orders yet, checking schema...")
    
    # Check if new columns exist
    if res.data:
        row = res.data[0]
        has_payment_mode = "payment_mode" in row
        has_discount = "discount" in row
        has_final_amount = "final_amount" in row
        has_completed_at = "completed_at" in row
        print(f"payment_mode: {'EXISTS' if has_payment_mode else 'MISSING'}")
        print(f"discount: {'EXISTS' if has_discount else 'MISSING'}")
        print(f"final_amount: {'EXISTS' if has_final_amount else 'MISSING'}")
        print(f"completed_at: {'EXISTS' if has_completed_at else 'MISSING'}")
    else:
        print("No orders in table - cannot auto-detect columns.")
        print("Please add these columns via Supabase Dashboard SQL Editor:")
        print("""
ALTER TABLE orders ADD COLUMN IF NOT EXISTS payment_mode TEXT;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS discount FLOAT DEFAULT 0;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS final_amount FLOAT;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS completed_at TEXT;
        """)
except Exception as e:
    print(f"Error: {e}")
    print("\nPlease run this SQL in Supabase Dashboard > SQL Editor:")
    print("""
ALTER TABLE orders ADD COLUMN IF NOT EXISTS payment_mode TEXT;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS discount FLOAT DEFAULT 0;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS final_amount FLOAT;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS completed_at TEXT;
    """)

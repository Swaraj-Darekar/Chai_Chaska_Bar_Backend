"""Migration script to create wallet tables in Supabase"""
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

print("="*60)
print("  CHAI CHASKA BAR - Wallet Migration Helper")
print("="*60)
print()
print("Please run the following SQL in your Supabase Dashboard")
print("Go to: Supabase Dashboard > SQL Editor > New Query")
print()
print("="*60)
print("""
-- 1. Create the wallet table (single row, id=1 always)
CREATE TABLE IF NOT EXISTS cafe_wallet (
    id INT PRIMARY KEY DEFAULT 1,
    balance FLOAT NOT NULL DEFAULT 0.0
);

-- 2. Seed with initial balance of 0
INSERT INTO cafe_wallet (id, balance)
VALUES (1, 0.0)
ON CONFLICT (id) DO NOTHING;

-- 3. Create wallet transaction log
CREATE TABLE IF NOT EXISTS wallet_transactions (
    id SERIAL PRIMARY KEY,
    amount FLOAT NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
""")
print("="*60)
print()

# Test if the tables already exist
try:
    res = supabase.table("cafe_wallet").select("balance").eq("id", 1).execute()
    if res.data:
        print(f"✅ cafe_wallet table EXISTS. Current balance: ₹{res.data[0]['balance']}")
    else:
        print("⚠️  cafe_wallet table found but no data row. The SQL above will seed it.")
except Exception as e:
    print(f"❌ cafe_wallet table NOT FOUND. Please run the SQL above.")
    print(f"   Error: {e}")

try:
    res = supabase.table("wallet_transactions").select("id").limit(1).execute()
    print(f"✅ wallet_transactions table EXISTS.")
except Exception as e:
    print(f"❌ wallet_transactions table NOT FOUND. Please run the SQL above.")
    print(f"   Error: {e}")

print()
print("After running the SQL, restart your backend server.")

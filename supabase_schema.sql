-- CHAI CHASKA BAR - FULL SUPABASE DATABASE SCHEMA
-- RUN THIS IN YOUR SUPABASE SQL EDITOR

-- 1. Categories Table
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    description TEXT
);

-- 2. Items Table
CREATE TABLE IF NOT EXISTS items (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    price FLOAT NOT NULL,
    image_url TEXT,
    category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE
);

-- 3. Orders Table
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    customer_name TEXT NOT NULL,
    customer_phone TEXT NOT NULL,
    table_id TEXT NOT NULL,
    total_price FLOAT NOT NULL,
    status TEXT DEFAULT 'pending',
    payment_mode TEXT,
    payment_status TEXT DEFAULT 'paid',
    member_id INTEGER,
    discount FLOAT DEFAULT 0,
    final_amount FLOAT,
    settled INTEGER DEFAULT 0,
    settlement_id INTEGER, -- Will be linked later
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- 4. Order Items Table
CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    item_name TEXT NOT NULL,
    item_price FLOAT NOT NULL,
    quantity INTEGER NOT NULL
);

-- 5. Expenses Table
CREATE TABLE IF NOT EXISTS expenses (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    amount FLOAT NOT NULL,
    date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    settled INTEGER DEFAULT 0,
    settlement_id INTEGER, -- Will be linked later
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 6. Monthly Settlements Table
CREATE TABLE IF NOT EXISTS monthly_settlements (
    id SERIAL PRIMARY KEY,
    month_name TEXT NOT NULL,
    total_sales FLOAT NOT NULL,
    total_expenses FLOAT NOT NULL,
    net_profit FLOAT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 7. Members Table
CREATE TABLE IF NOT EXISTS members (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    phone TEXT,
    total_bill FLOAT DEFAULT 0.0,
    due_bill FLOAT DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 8. Member Payments Table
CREATE TABLE IF NOT EXISTS member_payments (
    id SERIAL PRIMARY KEY,
    member_id INTEGER REFERENCES members(id) ON DELETE CASCADE,
    amount FLOAT NOT NULL,
    payment_mode TEXT NOT NULL,
    note TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Add Foreign Key relationships for settlements & members
ALTER TABLE orders ADD CONSTRAINT fk_order_settlement FOREIGN KEY (settlement_id) REFERENCES monthly_settlements(id);
ALTER TABLE expenses ADD CONSTRAINT fk_expense_settlement FOREIGN KEY (settlement_id) REFERENCES monthly_settlements(id);
ALTER TABLE orders ADD CONSTRAINT fk_order_member FOREIGN KEY (member_id) REFERENCES members(id);

-- 9. Cafe Wallet Table
CREATE TABLE IF NOT EXISTS cafe_wallet (
    id INTEGER PRIMARY KEY DEFAULT 1,
    balance FLOAT DEFAULT 0.0
);

-- Initialize wallet if empty
INSERT INTO cafe_wallet (id, balance) VALUES (1, 0.0) ON CONFLICT (id) DO NOTHING;

-- 10. Wallet Transactions Table
CREATE TABLE IF NOT EXISTS wallet_transactions (
    id SERIAL PRIMARY KEY,
    amount FLOAT NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 11. System Settings Table
CREATE TABLE IF NOT EXISTS system_settings (
    key TEXT PRIMARY KEY,
    value FLOAT NOT NULL
);

-- Initialize settings if empty
INSERT INTO system_settings (key, value) VALUES ('commission_rate', 2.0) ON CONFLICT (key) DO NOTHING;

-- IMPORTANT: DISABLE RLS (Row Level Security) TO ALLOW FRONTEND/BACKEND ACCESS WITHOUT AUTH
ALTER TABLE categories DISABLE ROW LEVEL SECURITY;
ALTER TABLE items DISABLE ROW LEVEL SECURITY;
ALTER TABLE orders DISABLE ROW LEVEL SECURITY;
ALTER TABLE order_items DISABLE ROW LEVEL SECURITY;
ALTER TABLE expenses DISABLE ROW LEVEL SECURITY;
ALTER TABLE monthly_settlements DISABLE ROW LEVEL SECURITY;
ALTER TABLE members DISABLE ROW LEVEL SECURITY;
ALTER TABLE member_payments DISABLE ROW LEVEL SECURITY;
ALTER TABLE cafe_wallet DISABLE ROW LEVEL SECURITY;
ALTER TABLE wallet_transactions DISABLE ROW LEVEL SECURITY;
ALTER TABLE system_settings DISABLE ROW LEVEL SECURITY;

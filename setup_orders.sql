-- Create orders table
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    customer_name TEXT NOT NULL,
    customer_phone TEXT NOT NULL,
    table_id TEXT NOT NULL,
    total_price FLOAT NOT NULL,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create order_items table
CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    item_name TEXT NOT NULL,
    item_price FLOAT NOT NULL,
    quantity INTEGER NOT NULL
);

-- Note: Depending on your Supabase settings, you might need to disable Row Level Security (RLS) 
-- temporarily so the anon key can insert data, or you can create policies.
-- To allow public access (for development):
ALTER TABLE orders DISABLE ROW LEVEL SECURITY;
ALTER TABLE order_items DISABLE ROW LEVEL SECURITY;

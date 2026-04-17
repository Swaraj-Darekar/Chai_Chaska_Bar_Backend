import os
from dotenv import load_dotenv
from supabase import create_client, Client
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

USE_SUPABASE = bool(SUPABASE_URL and SUPABASE_KEY)

# Supabase Client
supabase: Client | None = None

# SQLite Fallback
engine = None
SessionLocal = None
Base = declarative_base()

class CategoryModel(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, unique=True, index=True)
    description = Column(String, nullable=True)

class ItemModel(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, index=True)
    price = Column(Float)
    image_url = Column(String)
    category_id = Column(Integer, ForeignKey("categories.id"))

class OrderModel(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    customer_name = Column(String, nullable=False)
    customer_phone = Column(String, nullable=False)
    table_id = Column(String, nullable=False)
    total_price = Column(Float, nullable=False)
    status = Column(String, default="pending")  # pending | preparing | served | done
    payment_mode = Column(String, nullable=True)  # cash | online
    discount = Column(Float, default=0)
    final_amount = Column(Float, nullable=True)
    settled = Column(Integer, default=0) # 0: No, 1: Yes (Using Integer for better cross-compat)
    settlement_id = Column(Integer, ForeignKey("monthly_settlements.id"), nullable=True)
    created_at = Column(String, default=lambda: datetime.now().isoformat())
    completed_at = Column(String, nullable=True)

class OrderItemModel(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    item_name = Column(String, nullable=False)
    item_price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)

class ExpenseModel(Base):
    __tablename__ = "expenses"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    date = Column(String, default=lambda: datetime.now().isoformat())
    settled = Column(Integer, default=0)
    settlement_id = Column(Integer, ForeignKey("monthly_settlements.id"), nullable=True)
    created_at = Column(String, default=lambda: datetime.now().isoformat())

class MonthlySettlementModel(Base):
    __tablename__ = "monthly_settlements"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    month_name = Column(String, nullable=False)
    total_sales = Column(Float, nullable=False)
    total_expenses = Column(Float, nullable=False)
    net_profit = Column(Float, nullable=False)
    created_at = Column(String, default=lambda: datetime.now().isoformat())

class CafeWalletModel(Base):
    __tablename__ = "cafe_wallet"
    id = Column(Integer, primary_key=True, default=1)
    balance = Column(Float, default=0.0)

class WalletTransactionModel(Base):
    __tablename__ = "wallet_transactions"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    amount = Column(Float, nullable=False)
    description = Column(String, nullable=False)
    created_at = Column(String, default=lambda: datetime.now().isoformat())

class SystemSettingsModel(Base):
    __tablename__ = "system_settings"
    key = Column(String, primary_key=True)
    value = Column(Float, nullable=False)

if USE_SUPABASE:
    print("Using Supabase for Database")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    print("WARNING: Supabase credentials not found. Using local SQLite fallback.")
    SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

def get_db():
    if not USE_SUPABASE:
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    else:
        yield supabase

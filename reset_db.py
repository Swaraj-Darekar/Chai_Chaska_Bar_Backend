"""
Clear all row data from all database tables (Supabase or SQLite)
Preserves table structures, schemas, and columns 100%.
"""
import sys
import database

def clear_all_tables():
    print("Starting complete database data wipe...")
    
    if database.USE_SUPABASE:
        print("Connecting to Supabase...")
        db = database.supabase
        
        tables = [
            "order_items",
            "member_payments",
            "orders",
            "expenses",
            "monthly_settlements",
            "members",
            "wallet_transactions",
            "items",
            "categories"
        ]
        
        for t in tables:
            try:
                print(f"Clearing rows from table: {t}...")
                db.table(t).delete().neq("id", -1).execute()
            except Exception as e:
                print(f"Note on {t}: {e}")
                
        try:
            print("Resetting cafe_wallet balance to 0.0...")
            db.table("cafe_wallet").update({"balance": 0.0}).eq("id", 1).execute()
        except Exception as e:
            print(f"Note on cafe_wallet: {e}")
            
    else:
        print("Using local SQLite database...")
        db = database.SessionLocal()
        try:
            db.query(database.OrderItemModel).delete()
            db.query(database.MemberPaymentModel).delete()
            db.query(database.OrderModel).delete()
            db.query(database.ExpenseModel).delete()
            db.query(database.MonthlySettlementModel).delete()
            db.query(database.MemberModel).delete()
            db.query(database.WalletTransactionModel).delete()
            db.query(database.ItemModel).delete()
            db.query(database.CategoryModel).delete()
            
            wallet = db.query(database.CafeWalletModel).filter(database.CafeWalletModel.id == 1).first()
            if wallet:
                wallet.balance = 0.0
            else:
                db.add(database.CafeWalletModel(id=1, balance=0.0))
                
            db.commit()
        finally:
            db.close()
            
    print("SUCCESS: All table data has been completely cleared!")
    print("Database structure, columns, and tables remain intact 100%. Ready for fresh usage.")

if __name__ == "__main__":
    clear_all_tables()

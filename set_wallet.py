from database import USE_SUPABASE, supabase, SessionLocal, CafeWalletModel

if USE_SUPABASE:
    res = supabase.table("cafe_wallet").update({"balance": 18.0}).eq("id", 1).execute()
    print("Updated wallet balance to 18.0 via Supabase")
else:
    db = SessionLocal()
    wallet = db.query(CafeWalletModel).filter(CafeWalletModel.id == 1).first()
    if wallet:
        wallet.balance = 18.0
        db.commit()
        print("Updated wallet balance to 18.0 via SQLite")
    else:
        print("Wallet not found")
    db.close()

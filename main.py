from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from sqlalchemy import func
import database

app = FastAPI(title="Chai Chaska Bar Backend API")

import os
# Setup CORS
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic  Schemas
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class CategoryResponse(CategoryBase):
    id: int

class ItemBase(BaseModel):
    name: str
    price: float
    image_url: Optional[str] = "https://images.unsplash.com/photo-1541167760496-1628856ab772?q=80&w=200&auto=format&fit=crop"
    category_id: int

class ItemResponse(ItemBase):
    id: int

class OrderItemBase(BaseModel):
    item_name: str
    item_price: float
    quantity: int

class OrderCreate(BaseModel):
    customer_name: str
    customer_phone: str
    table_id: str
    total_price: float
    status: Optional[str] = "pending"
    items: List[OrderItemBase]

class AddItems(BaseModel):
    items: List[OrderItemBase]

class CompleteOrder(BaseModel):
    payment_mode: str  # cash | online
    discount: float = 0
    final_amount: float

class WalletRecharge(BaseModel):
    amount: float
    description: str = "Recharged from Super Admin"

class SystemSettings(BaseModel):
    commission_rate: float

def get_system_settings(db) -> float:
    if database.USE_SUPABASE:
        res = db.table("system_settings").select("value").eq("key", "commission_rate").execute()
        if res.data:
            return res.data[0]["value"]
    else:
        setting = db.query(database.SystemSettingsModel).filter(database.SystemSettingsModel.key == "commission_rate").first()
        if setting:
            return setting.value
    return 2.0

def set_system_settings(db, rate: float):
    if database.USE_SUPABASE:
        db.table("system_settings").upsert({"key": "commission_rate", "value": rate}).execute()
    else:
        setting = db.query(database.SystemSettingsModel).filter(database.SystemSettingsModel.key == "commission_rate").first()
        if not setting:
            setting = database.SystemSettingsModel(key="commission_rate", value=rate)
            db.add(setting)
        else:
            setting.value = rate
        db.commit()

class OrderItemResponse(OrderItemBase):
    id: int

class OrderResponse(BaseModel):
    id: int
    customer_name: str
    customer_phone: str
    table_id: str
    total_price: float
    status: str
    payment_mode: Optional[str] = None
    discount: float = 0
    final_amount: Optional[float] = None
    settled: int = 0
    settlement_id: Optional[int] = None
    created_at: str
    completed_at: Optional[str] = None
    items: List[OrderItemResponse] = []

class ExpenseBase(BaseModel):
    name: str
    amount: float
    date: Optional[str] = None

class ExpenseResponse(ExpenseBase):
    id: int
    settled: int
    settlement_id: Optional[int] = None
    created_at: str

class MonthlySettlementResponse(BaseModel):
    id: int
    month_name: str
    total_sales: float
    total_expenses: float
    net_profit: float
    created_at: str

@app.get("/")
def read_root():
    return {"message": "Welcome to Chai Chaska Bar API", "using_supabase": database.USE_SUPABASE}

# Categories
@app.get("/api/categories", response_model=List[CategoryResponse])
def get_categories(db = Depends(database.get_db)):
    if database.USE_SUPABASE:
        res = db.table("categories").select("*").execute()
        return res.data
    else:
        return db.query(database.CategoryModel).all()

@app.post("/api/categories", response_model=CategoryResponse)
def create_category(category: CategoryBase, db = Depends(database.get_db)):
    if database.USE_SUPABASE:
        res = db.table("categories").insert([category.model_dump()]).execute()
        return res.data[0]
    else:
        db_cat = database.CategoryModel(**category.model_dump())
        db.add(db_cat)
        db.commit()
        db.refresh(db_cat)
        return db_cat

@app.put("/api/categories/{category_id}", response_model=CategoryResponse)
def update_category(category_id: int, category: CategoryBase, db = Depends(database.get_db)):
    if database.USE_SUPABASE:
        res = db.table("categories").update(category.model_dump()).eq("id", category_id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Category not found")
        return res.data[0]
    else:
        db_cat = db.query(database.CategoryModel).filter(database.CategoryModel.id == category_id).first()
        if not db_cat:
            raise HTTPException(status_code=404, detail="Category not found")
        for key, value in category.model_dump().items():
            setattr(db_cat, key, value)
        db.commit()
        db.refresh(db_cat)
        return db_cat

@app.delete("/api/categories/{category_id}")
def delete_category(category_id: int, db = Depends(database.get_db)):
    if database.USE_SUPABASE:
        # Delete all items in this category first
        db.table("items").delete().eq("category_id", category_id).execute()
        res = db.table("categories").delete().eq("id", category_id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Category not found")
        return {"message": "Category and its items deleted successfully"}
    else:
        # Delete all items in this category first
        db.query(database.ItemModel).filter(database.ItemModel.category_id == category_id).delete()
        db_cat = db.query(database.CategoryModel).filter(database.CategoryModel.id == category_id).first()
        if not db_cat:
            raise HTTPException(status_code=404, detail="Category not found")
        db.delete(db_cat)
        db.commit()
        return {"message": "Category and its items deleted successfully"}

# Items
@app.get("/api/menu", response_model=List[ItemResponse])
def get_menu_items(db = Depends(database.get_db)):
    if database.USE_SUPABASE:
        res = db.table("items").select("*").execute()
        return res.data
    else:
        return db.query(database.ItemModel).all()

@app.post("/api/menu", response_model=ItemResponse)
def create_menu_item(item: ItemBase, db = Depends(database.get_db)):
    if database.USE_SUPABASE:
        res = db.table("items").insert([item.model_dump()]).execute()
        return res.data[0]
    else:
        db_item = database.ItemModel(**item.model_dump())
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return db_item

@app.put("/api/menu/{item_id}", response_model=ItemResponse)
def update_menu_item(item_id: int, item: ItemBase, db = Depends(database.get_db)):
    if database.USE_SUPABASE:
        res = db.table("items").update(item.model_dump()).eq("id", item_id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Item not found")
        return res.data[0]
    else:
        db_item = db.query(database.ItemModel).filter(database.ItemModel.id == item_id).first()
        if not db_item:
            raise HTTPException(status_code=404, detail="Item not found")
        for key, value in item.model_dump().items():
            setattr(db_item, key, value)
        db.commit()
        db.refresh(db_item)
        return db_item

@app.delete("/api/menu/{item_id}")
def delete_menu_item(item_id: int, db = Depends(database.get_db)):
    if database.USE_SUPABASE:
        res = db.table("items").delete().eq("id", item_id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Item not found")
        return {"message": "Deleted successfully"}
    else:
        db_item = db.query(database.ItemModel).filter(database.ItemModel.id == item_id).first()
        if not db_item:
            raise HTTPException(status_code=404, detail="Item not found")
        db.delete(db_item)
        db.commit()
        return {"message": "Deleted successfully"}

# Orders
@app.post("/api/orders", response_model=OrderResponse)
def create_order(order: OrderCreate, db = Depends(database.get_db)):
    if database.USE_SUPABASE:
        # 1. Check if there is an existing active order for this table
        # Only for physical tables (1-6). Takeaway orders are ALWAYS separate.
        if order.table_id != "Takeaway":
            existing_res = db.table("orders").select("*, order_items(*)").eq("table_id", order.table_id).in_("status", ["pending", "preparing", "served"]).eq("settled", 0).order("created_at", desc=True).limit(1).execute()
            
            if existing_res.data:
                # If it's a physical table, block merging as per user request
                raise HTTPException(status_code=400, detail="Table is already occupied. Please contact counter.")

        # No active order found, proceed with new order creation
        order_dict = order.model_dump()
        items_data = order_dict.pop("items")
        order_res = db.table("orders").insert([order_dict]).execute()
        new_order = order_res.data[0]
        
        if items_data:
            for item in items_data:
                item["order_id"] = new_order["id"]
            items_res = db.table("order_items").insert(items_data).execute()
            new_order["items"] = items_res.data
        else:
            new_order["items"] = []
            
        return new_order
    else:
        # 1. Check if there is an existing active order for SQLite
        # Only for physical tables. Takeaway orders are ALWAYS separate.
        if order.table_id != "Takeaway":
            db_order = db.query(database.OrderModel).filter(
                database.OrderModel.table_id == order.table_id,
                database.OrderModel.status.in_(["pending", "preparing", "served"]),
                database.OrderModel.settled == 0
            ).order_by(database.OrderModel.id.desc()).first()

            if db_order:
                raise HTTPException(status_code=400, detail="Table is already occupied. Please contact counter.")

        # 2. No active order, create new
        db_order = database.OrderModel(
            customer_name=order.customer_name,
            customer_phone=order.customer_phone,
            table_id=order.table_id,
            total_price=order.total_price,
            status=order.status
        )
        db.add(db_order)
        db.commit()
        db.refresh(db_order)
        
        order_items = []
        for item in order.items:
            db_item = database.OrderItemModel(
                order_id=db_order.id,
                item_name=item.item_name,
                item_price=item.item_price,
                quantity=item.quantity
            )
            db.add(db_item)
            order_items.append(db_item)
        
        db.commit()
        for db_item in order_items:
            db.refresh(db_item)
        
        return {
            **db_order.__dict__,
            "items": order_items
        }

@app.get("/api/tables/{table_id}/active")
def get_table_active_order(table_id: str, db = Depends(database.get_db)):
    if database.USE_SUPABASE:
        res = db.table("orders").select("*, order_items(*)").eq("table_id", table_id).in_("status", ["pending", "preparing", "served"]).eq("settled", 0).order("created_at", desc=True).limit(1).execute()
        if res.data:
            order = res.data[0]
            order["items"] = order.pop("order_items", [])
            return order
        return None
    else:
        db_order = db.query(database.OrderModel).filter(
            database.OrderModel.table_id == table_id,
            database.OrderModel.status.in_(["pending", "preparing", "served"]),
            database.OrderModel.settled == 0
        ).order_by(database.OrderModel.id.desc()).first()
        if db_order:
            items = db.query(database.OrderItemModel).filter(database.OrderItemModel.order_id == db_order.id).all()
            return {
                **db_order.__dict__,
                "items": items
            }
        return None

@app.get("/api/orders/active", response_model=List[OrderResponse])
def get_active_orders(db = Depends(database.get_db)):
    if database.USE_SUPABASE:
        # Fetch pending/preparing/served orders
        res = db.table("orders").select("*, order_items(*)").in_("status", ["pending", "preparing", "served"]).order("created_at", desc=False).execute()
        # Transform items mapping if needed (supabase often nests them)
        orders = []
        for row in res.data:
            order = row.copy()
            order["items"] = order.pop("order_items", [])
            orders.append(order)
        return orders
    else:
        # Using SQLite
        db_orders = db.query(database.OrderModel).filter(database.OrderModel.status.in_(["pending", "preparing", "served"])).order_by(database.OrderModel.created_at.asc()).all()
        results = []
        for order in db_orders:
            items = db.query(database.OrderItemModel).filter(database.OrderItemModel.order_id == order.id).all()
            results.append({
                **order.__dict__,
                "items": [OrderItemResponse(id=i.id, item_name=i.item_name, item_price=i.item_price, quantity=i.quantity) for i in items]
            })
        return results

@app.get("/api/orders/history", response_model=List[OrderResponse])
def get_order_history(settled: int = 0, db = Depends(database.get_db)):
    if database.USE_SUPABASE:
        res = db.table("orders").select("*, order_items(*)").eq("status", "done").eq("settled", settled).order("completed_at", desc=True).execute()
        orders = []
        for row in res.data:
            order = row.copy()
            order["items"] = order.pop("order_items", [])
            orders.append(order)
        return orders
    else:
        db_orders = db.query(database.OrderModel).filter(
            database.OrderModel.status == "done",
            database.OrderModel.settled == settled
        ).order_by(database.OrderModel.completed_at.desc()).all()
        results = []
        for order in db_orders:
            items = db.query(database.OrderItemModel).filter(database.OrderItemModel.order_id == order.id).all()
            results.append({
                **order.__dict__,
                "items": [OrderItemResponse(id=i.id, item_name=i.item_name, item_price=i.item_price, quantity=i.quantity) for i in items]
            })
        return results

@app.get("/api/orders/{order_id}")
def get_order(order_id: int, db = Depends(database.get_db)):
    if database.USE_SUPABASE:
        res = db.table("orders").select("*").eq("id", order_id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Order not found")
        return res.data[0]
    else:
        db_order = db.query(database.OrderModel).filter(database.OrderModel.id == order_id).first()
        if not db_order:
            raise HTTPException(status_code=404, detail="Order not found")
        return db_order

@app.put("/api/orders/{order_id}/status")
def update_order_status(order_id: int, status: str, db = Depends(database.get_db)):
    if database.USE_SUPABASE:
        res = db.table("orders").update({"status": status}).eq("id", order_id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Order not found")
        return res.data[0]
    else:
        db_order = db.query(database.OrderModel).filter(database.OrderModel.id == order_id).first()
        if not db_order:
            raise HTTPException(status_code=404, detail="Order not found")
        db_order.status = status
        db.commit()
        return db_order

@app.put("/api/orders/{order_id}/complete")
def complete_order(order_id: int, data: CompleteOrder, db = Depends(database.get_db)):
    from datetime import datetime, timezone
    completed_at = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    
    # Wallet Logic
    should_deduct = data.final_amount > 40
    commission_amount = get_system_settings(db)
    
    if database.USE_SUPABASE:
        # Check wallet
        wallet_res = db.table("cafe_wallet").select("balance").eq("id", 1).execute()
        wallet_balance = wallet_res.data[0]["balance"] if wallet_res.data else 0
        
        if should_deduct and wallet_balance < 10:
            raise HTTPException(status_code=400, detail="Insufficient wallet balance. Please recharge.")
            
        update_data = {
            "status": "done",
            "payment_mode": data.payment_mode,
            "discount": data.discount,
            "final_amount": data.final_amount,
            "completed_at": completed_at,
            "settled": 0
        }
        res = db.table("orders").update(update_data).eq("id", order_id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Order not found")
            
        if should_deduct:
            new_balance = wallet_balance - commission_amount
            db.table("cafe_wallet").update({"balance": new_balance}).eq("id", 1).execute()
            db.table("wallet_transactions").insert([{
                "amount": -commission_amount,
                "description": f"Commission for Order #{order_id}"
            }]).execute()
            
        return res.data[0]
    else:
        # Check wallet
        db_wallet = db.query(database.CafeWalletModel).filter(database.CafeWalletModel.id == 1).first()
        if not db_wallet:
            db_wallet = database.CafeWalletModel(id=1, balance=0.0)
            db.add(db_wallet)
            db.commit()
            
        if should_deduct and db_wallet.balance < 10:
            raise HTTPException(status_code=400, detail="Insufficient wallet balance. Please recharge.")

        db_order = db.query(database.OrderModel).filter(database.OrderModel.id == order_id).first()
        if not db_order:
            raise HTTPException(status_code=404, detail="Order not found")
            
        db_order.status = "done"
        db_order.payment_mode = data.payment_mode
        db_order.discount = data.discount
        db_order.final_amount = data.final_amount
        db_order.completed_at = completed_at
        db_order.settled = 0
        
        if should_deduct:
            db_wallet.balance -= commission_amount
            db_txn = database.WalletTransactionModel(
                amount=-commission_amount,
                description=f"Commission for Order #{order_id}"
            )
            db.add(db_txn)
            
        db.commit()
        db.refresh(db_order)
        return db_order

# Wallet API
@app.delete("/api/orders/{order_id}/items/{item_pk}")
def delete_order_item(order_id: int, item_pk: int, db = Depends(database.get_db)):
    if database.USE_SUPABASE:
        # Check if item belongs to order
        item_res = db.table("order_items").select("*").eq("id", item_pk).eq("order_id", order_id).execute()
        if not item_res.data:
            raise HTTPException(status_code=404, detail="Item not found in this order")
        
        # Delete item
        db.table("order_items").delete().eq("id", item_pk).execute()
        
        # Recalculate total
        rem_items = db.table("order_items").select("item_price, quantity").eq("order_id", order_id).execute()
        new_total = sum(i["item_price"] * i["quantity"] for i in rem_items.data)
        db.table("orders").update({"total_price": new_total}).eq("id", order_id).execute()
        return {"msg": "Item deleted", "new_total": new_total}
    else:
        item = db.query(database.OrderItemModel).filter(database.OrderItemModel.id == item_pk, database.OrderItemModel.order_id == order_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        
        db.delete(item)
        db.commit()
        
        # Recalculate total
        new_total = db.query(func.sum(database.OrderItemModel.item_price * database.OrderItemModel.quantity)).filter(database.OrderItemModel.order_id == order_id).scalar() or 0
        order = db.query(database.OrderModel).filter(database.OrderModel.id == order_id).first()
        order.total_price = new_total
        db.commit()
        return {"msg": "Item deleted", "new_total": new_total}

@app.get("/api/wallet")
def get_wallet(db = Depends(database.get_db)):
    if database.USE_SUPABASE:
        res = db.table("cafe_wallet").select("balance").eq("id", 1).execute()
        if not res.data:
            # Seed if empty
            db.table("cafe_wallet").insert([{"id": 1, "balance": 0.0}]).execute()
            return {"balance": 0.0}
        return {"balance": res.data[0]["balance"]}
    else:
        db_wallet = db.query(database.CafeWalletModel).filter(database.CafeWalletModel.id == 1).first()
        if not db_wallet:
            db_wallet = database.CafeWalletModel(id=1, balance=0.0)
            db.add(db_wallet)
            db.commit()
        return {"balance": db_wallet.balance}

@app.post("/api/wallet/recharge")
def recharge_wallet(data: WalletRecharge, db = Depends(database.get_db)):
    if database.USE_SUPABASE:
        res = db.table("cafe_wallet").select("balance").eq("id", 1).execute()
        current_balance = res.data[0]["balance"] if res.data else 0
        new_balance = current_balance + data.amount
        
        if not res.data:
            db.table("cafe_wallet").insert([{"id": 1, "balance": new_balance}]).execute()
        else:
            db.table("cafe_wallet").update({"balance": new_balance}).eq("id", 1).execute()
            
        db.table("wallet_transactions").insert([{
            "amount": data.amount,
            "description": data.description
        }]).execute()
        return {"balance": new_balance}
    else:
        db_wallet = db.query(database.CafeWalletModel).filter(database.CafeWalletModel.id == 1).first()
        if not db_wallet:
            db_wallet = database.CafeWalletModel(id=1, balance=data.amount)
            db.add(db_wallet)
        else:
            db_wallet.balance += data.amount
            
        db_txn = database.WalletTransactionModel(
            amount=data.amount,
            description=data.description
        )
        db.add(db_txn)
        db.commit()
        return {"balance": db_wallet.balance}

@app.get("/api/superadmin/settings")
def get_settings(db = Depends(database.get_db)):
    rate = get_system_settings(db)
    return {"commission_rate": rate}

@app.put("/api/superadmin/settings")
def update_settings(settings: SystemSettings, db = Depends(database.get_db)):
    set_system_settings(db, settings.commission_rate)
    return {"message": "Settings updated", "commission_rate": settings.commission_rate}

@app.get("/api/superadmin/analytics")
def get_superadmin_analytics(db = Depends(database.get_db)):
    commission_rate = get_system_settings(db)
    
    # Needs to determine today and current month strings matching 'YYYY-MM-DD' and 'YYYY-MM'
    today_str = datetime.now().isoformat()[:10]
    month_str = datetime.now().isoformat()[:7]
    
    if database.USE_SUPABASE:
        # Fetch all orders that are done and amount > 40
        # Not easily aggregatable purely via REST without RPC, so fetch minimal data and aggregate in python
        # Since it's a small app, this is very fast.
        res = db.table("orders").select("completed_at", "final_amount").eq("status", "done").execute()
        valid_orders = [o for o in res.data if (o.get("final_amount") or 0) > 40 and o.get("completed_at")]
    else:
        # SQLite
        valid_orders = db.query(database.OrderModel.completed_at, database.OrderModel.final_amount).filter(
             database.OrderModel.status == "done",
             database.OrderModel.final_amount > 40,
             database.OrderModel.completed_at != None
        ).all()
        # Convert to dict for uniform processing
        valid_orders = [{"completed_at": o[0]} for o in valid_orders]
        
    todays_bookings = 0
    monthly_bookings = 0
    
    for o in valid_orders:
        cat = o["completed_at"]
        if cat.startswith(today_str):
            todays_bookings += 1
        if cat.startswith(month_str):
            monthly_bookings += 1
            
    return {
        "todaysBookings": todays_bookings,
        "todaysEarnings": todays_bookings * commission_rate,
        "monthlyBookings": monthly_bookings,
        "monthlyEarnings": monthly_bookings * commission_rate,
        "commissionRate": commission_rate
    }

@app.post("/api/orders/{order_id}/items", response_model=OrderResponse)
def add_items_to_order(order_id: int, add_data: AddItems, db = Depends(database.get_db)):
    if database.USE_SUPABASE:
        # 1. Fetch order
        order_res = db.table("orders").select("*").eq("id", order_id).execute()
        if not order_res.data:
            raise HTTPException(status_code=404, detail="Order not found")
        order = order_res.data[0]
        
        # 2. Insert new items
        new_total = order["total_price"]
        items_to_insert = []
        for item in add_data.items:
            item_dict = item.model_dump()
            item_dict["order_id"] = order_id
            items_to_insert.append(item_dict)
            new_total += (item.item_price * item.quantity)
            
        db.table("order_items").insert(items_to_insert).execute()
        
        # 3. Update total price
        db.table("orders").update({"total_price": new_total}).eq("id", order_id).execute()
        
        # 4. Return updated order
        updated_res = db.table("orders").select("*, order_items(*)").eq("id", order_id).execute()
        new_order = updated_res.data[0]
        new_order["items"] = new_order.pop("order_items", [])
        return new_order
    else:
        # SQLite
        db_order = db.query(database.OrderModel).filter(database.OrderModel.id == order_id).first()
        if not db_order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        for item in add_data.items:
            db_item = database.OrderItemModel(
                order_id=order_id,
                item_name=item.item_name,
                item_price=item.item_price,
                quantity=item.quantity
            )
            db.add(db_item)
            db_order.total_price += (item.item_price * item.quantity)
            
        db.commit()
        db.refresh(db_order)
        
        items = db.query(database.OrderItemModel).filter(database.OrderItemModel.order_id == order_id).all()
        return {
            **db_order.__dict__,
            "items": [OrderItemResponse(id=i.id, item_name=i.item_name, item_price=i.item_price, quantity=i.quantity) for i in items]
        }

# Expenses API
@app.get("/api/expenses", response_model=List[ExpenseResponse])
def get_expenses(db = Depends(database.get_db)):
    if database.USE_SUPABASE:
        res = db.table("expenses").select("*").eq("settled", 0).order("date", desc=True).execute()
        return res.data
    else:
        return db.query(database.ExpenseModel).filter(database.ExpenseModel.settled == 0).order_by(database.ExpenseModel.date.desc()).all()

@app.post("/api/expenses", response_model=ExpenseResponse)
def create_expense(expense: ExpenseBase, db = Depends(database.get_db)):
    from datetime import datetime
    expense_data = expense.model_dump()
    if not expense_data.get("date"):
        expense_data["date"] = datetime.now().isoformat()
    expense_data["created_at"] = datetime.now().isoformat()
    
    if database.USE_SUPABASE:
        res = db.table("expenses").insert([expense_data]).execute()
        return res.data[0]
    else:
        db_expense = database.ExpenseModel(**expense_data)
        db.add(db_expense)
        db.commit()
        db.refresh(db_expense)
        return db_expense

@app.delete("/api/expenses/{expense_id}")
def delete_expense(expense_id: int, db = Depends(database.get_db)):
    if database.USE_SUPABASE:
        db.table("expenses").delete().eq("id", expense_id).execute()
        return {"msg": "Expense deleted"}
    else:
        db_expense = db.query(database.ExpenseModel).filter(database.ExpenseModel.id == expense_id).first()
        if db_expense:
            db.delete(db_expense)
            db.commit()
        return {"msg": "Expense deleted"}

# Settlement API
@app.get("/api/analytics/settlements", response_model=List[MonthlySettlementResponse])
def get_settlements(db = Depends(database.get_db)):
    if database.USE_SUPABASE:
        res = db.table("monthly_settlements").select("*").order("created_at", desc=True).execute()
        return res.data
    else:
        return db.query(database.MonthlySettlementModel).order_by(database.MonthlySettlementModel.created_at.desc()).all()

@app.post("/api/analytics/settle")
def settle_this_month(db = Depends(database.get_db)):
    from datetime import datetime
    now = datetime.now()
    month_name = now.strftime("%B %Y")
    
    if database.USE_SUPABASE:
        # 1. Get non-settled done orders
        orders_res = db.table("orders").select("final_amount, total_price").eq("status", "done").eq("settled", 0).execute()
        total_sales = sum(float(o["final_amount"] or o["total_price"] or 0) for o in orders_res.data)
        
        # 2. Get non-settled expenses
        expenses_res = db.table("expenses").select("amount").eq("settled", 0).execute()
        total_expenses = sum(float(e["amount"] or 0) for e in expenses_res.data)
        
        # 3. Create settlement
        settlement_data = {
            "month_name": month_name,
            "total_sales": total_sales,
            "total_expenses": total_expenses,
            "net_profit": total_sales - total_expenses
        }
        set_res = db.table("monthly_settlements").insert([settlement_data]).execute()
        settlement_id = set_res.data[0]["id"]
        
        # 4. Mark everything as settled
        db.table("orders").update({"settled": 1, "settlement_id": settlement_id}).eq("status", "done").eq("settled", 0).execute()
        db.table("expenses").update({"settled": 1, "settlement_id": settlement_id}).eq("settled", 0).execute()
        
        return set_res.data[0]
    else:
        # 1. Get stats
        orders = db.query(database.OrderModel).filter(database.OrderModel.status == "done", database.OrderModel.settled == 0).all()
        total_sales = sum(float(o.final_amount or o.total_price or 0) for o in orders)
        
        expenses = db.query(database.ExpenseModel).filter(database.ExpenseModel.settled == 0).all()
        total_expenses = sum(float(e.amount or 0) for e in expenses)
        
        # 2. Create settlement
        db_set = database.MonthlySettlementModel(
            month_name=month_name,
            total_sales=total_sales,
            total_expenses=total_expenses,
            net_profit=total_sales - total_expenses
        )
        db.add(db_set)
        db.commit()
        db.refresh(db_set)
        
        # 3. Update orders and expenses
        for o in orders:
            o.settled = 1
            o.settlement_id = db_set.id
        for e in expenses:
            e.settled = 1
            e.settlement_id = db_set.id
        
        db.commit()
        return db_set

@app.get("/api/analytics/settlements/{settlement_id}/expenses", response_model=List[ExpenseResponse])
def get_settlement_expenses(settlement_id: int, db = Depends(database.get_db)):
    if database.USE_SUPABASE:
        res = db.table("expenses").select("*").eq("settlement_id", settlement_id).execute()
        return res.data
    else:
        return db.query(database.ExpenseModel).filter(database.ExpenseModel.settlement_id == settlement_id).all()

@app.post("/api/superadmin/reset")
def reset_all_data(db = Depends(database.get_db)):
    if database.USE_SUPABASE:
        db.table("order_items").delete().neq("id", -1).execute()
        db.table("orders").delete().neq("id", -1).execute()
        db.table("expenses").delete().neq("id", -1).execute()
        db.table("monthly_settlements").delete().neq("id", -1).execute()
        db.table("wallet_transactions").delete().neq("id", -1).execute()
        db.table("cafe_wallet").update({"balance": 0.0}).eq("id", 1).execute()
    else:
        db.query(database.OrderItemModel).delete()
        db.query(database.OrderModel).delete()
        db.query(database.ExpenseModel).delete()
        db.query(database.MonthlySettlementModel).delete()
        db.query(database.WalletTransactionModel).delete()
        wallet = db.query(database.CafeWalletModel).filter(database.CafeWalletModel.id == 1).first()
        if wallet:
            wallet.balance = 0.0
        else:
            db.add(database.CafeWalletModel(id=1, balance=0.0))
        db.commit()
    return {"message": "System reset successfully"}

from fastapi import FastAPI, APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from fastapi.middleware.cors import CORSMiddleware
import os

# Connects to your Supabase Database
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/delivery_app")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

# Boots up the API
app = FastAPI(title="Delivery App API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

admin_router = APIRouter(prefix="/api/admin")

@admin_router.get("/cash-bank")
def get_cash_bank(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT SUM(amount) as current_balance FROM operating_ledger"))
    return {"cash_on_hand": result.scalar() or 0.00}

@admin_router.get("/pending-users")
def get_pending_users(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT user_id, first_name, last_name, email, id_image_url FROM users WHERE is_approved = FALSE")).fetchall()
    return [dict(row._mapping) for row in result]

@admin_router.post("/users/{user_id}/approve")
def approve_user(user_id: int, db: Session = Depends(get_db)):
    db.execute(text("UPDATE users SET is_approved = TRUE WHERE user_id = :id"), {"id": user_id})
    db.commit()
    return {"status": "User approved"}

# NEW: Fetches your live inventory for the storefront
@admin_router.get("/products")
def get_all_products(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT product_id, name, base_sticker_price, category FROM products WHERE is_visible = TRUE")).fetchall()
    return [dict(row._mapping) for row in result]

@admin_router.post("/products/{product_id}/toggle")
def toggle_product_visibility(product_id: int, payload: dict, db: Session = Depends(get_db)):
    db.execute(text("UPDATE products SET is_visible = :visible WHERE product_id = :id"), {"visible": payload.get("is_visible"), "id": product_id})
    db.commit()
    return {"status": "Visibility updated"}

class PromotionPayload(BaseModel):
    name: str
    trigger_category_id: int
    trigger_qty_threshold: int
    reward_type: str
    reward_value: float
    active_days: str 
    is_stackable: bool

@admin_router.post("/promotions")
def create_promotion(payload: PromotionPayload, db: Session = Depends(get_db)):
    db.execute(text("""
        INSERT INTO promotions (name, trigger_category_id, trigger_qty_threshold, reward_type, reward_value, active_days, is_stackable, discount_target) 
        VALUES (:name, :category_id, :qty, :type, :value, :days, :stackable, 'cheapest_item')
    """), {
        "name": payload.name, "category_id": payload.trigger_category_id, "qty": payload.trigger_qty_threshold,
        "type": payload.reward_type, "value": payload.reward_value, "days": payload.active_days, "stackable": payload.is_stackable
    })
    db.commit()
    return {"status": "Promotion active"}

class OrderStatusPayload(BaseModel):
    status: str

@admin_router.get("/orders/active")
def get_active_orders(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT order_id, user_id, status, final_rounded_total FROM orders WHERE status != 'Completed' ORDER BY created_at ASC")).fetchall()
    return [dict(row._mapping) for row in result]

@admin_router.post("/orders/{order_id}/status")
def update_order_status(order_id: int, payload: OrderStatusPayload, db: Session = Depends(get_db)):
    db.execute(text("UPDATE orders SET status = :status WHERE order_id = :id"), {"status": payload.status, "id": order_id})
    if payload.status == 'Completed':
        order = db.execute(text("SELECT final_rounded_total FROM orders WHERE order_id = :id"), {"id": order_id}).fetchone()
        db.execute(text("""
            INSERT INTO operating_ledger (transaction_type, amount, description) 
            VALUES ('Order Revenue', :amount, :desc)
        """), {"amount": order.final_rounded_total, "desc": f"Order #{order_id} Delivered"})
    db.commit()
    return {"status": "Updated"}

app.include_router(admin_router)

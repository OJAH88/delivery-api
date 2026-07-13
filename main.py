from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/delivery_app")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="Delivery App API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"], allow_credentials=True)

@app.post("/api/cart/calculate")
async def calculate_cart(request: Request):
    db = SessionLocal()
    try:
        payload = await request.json()
        items = payload.get("items", [])
        
        # 1. Aggregate quantities per category
        cat_quantities = {}
        raw_total = 0.0
        for item in items:
            cat_id = str(item.get('category_id'))
            qty = int(item.get('qty') or 1)
            price = float(item.get('base_sticker_price') or 0)
            
            cat_quantities[cat_id] = cat_quantities.get(cat_id, 0) + qty
            raw_total += (price * qty)
        
        # 2. Check promotions
        promos = db.execute(text("SELECT * FROM promotions")).fetchall()
        total_discount = 0.0
        
        for p in promos:
            trigger_cat = str(p.trigger_category_id)
            if cat_quantities.get(trigger_cat, 0) >= p.trigger_qty_threshold:
                # Apply discount logic
                if p.reward_type == 'flat_discount':
                    total_discount += p.reward_value
        
        final_total = max(0.0, raw_total - total_discount)
        final_cash_total = round(final_total / 5.0) * 5
        
        return {
            "raw_total": float(raw_total),
            "discount_applied": float(total_discount),
            "final_cash_total": float(final_cash_total)
        }
    except Exception as e:
        return {"error": str(e), "raw_total": 0.0, "discount_applied": 0.0, "final_cash_total": 0.0}
    finally:
        db.close()

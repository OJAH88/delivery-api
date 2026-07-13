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
        
        # 1. Fetch active promotions
        promos = db.execute(text("SELECT * FROM promotions")).fetchall()
        
        raw_total = 0.0
        total_discount = 0.0
        
        for item in items:
            price = float(item.get('base_sticker_price') or 0)
            qty = int(item.get('qty') or 1)
            raw_total += (price * qty)
            
            # Check for bulk discount
            for p in promos:
                # Ensure you are comparing IDs correctly
                if str(item.get('category_id')) == str(p.trigger_category_id) and qty >= p.trigger_qty_threshold:
                    if p.reward_type == 'flat_discount':
                        total_discount += p.reward_value
        
        # 2. Corrected math: Define final_total first
        final_total = max(0, raw_total - total_discount)
        final_cash_total = round(final_total / 5.0) * 5
        
        return {
            "raw_total": float(raw_total),
            "discount_applied": float(total_discount),
            "final_cash_total": float(final_cash_total)
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

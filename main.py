from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"], allow_credentials=True)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/delivery_app")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@app.post("/api/cart/calculate")
async def calculate_cart(request: Request):
    try:
        payload = await request.json()
        items = payload.get("items", [])
        
        raw_total = 0.0
        discount_applied = 0.0
        
        for item in items:
            price = float(item.get('base_sticker_price') or 0)
            qty = int(item.get('qty') or 1)
            tier = item.get('tier_name')
            
            # BULK LOGIC: Only apply discount to the *extra* items if needed
            # Here: if it's Flower and qty is 2+, apply $5 discount to the total
            item_total = price * qty
            if tier == 'Flower' and qty >= 2:
                discount_applied += 5.0
            
            raw_total += item_total
            
        final_total = max(0.0, raw_total - discount_applied)
        final_cash_total = round(final_total / 5.0) * 5
        
        return {
            "raw_total": float(raw_total),
            "discount_applied": float(discount_applied),
            "final_cash_total": float(final_cash_total)
        }
    except Exception as e:
        return {"error": str(e)}

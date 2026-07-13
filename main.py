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
        
        raw_total = 0.0
        
        # Aggregate quantity per product and apply Tier logic
        for item in items:
            price = float(item.get('base_sticker_price') or 0)
            qty = int(item.get('qty') or 1)
            tier_name = item.get('tier_name') # This comes from your JOIN in the products table
            
            # BULK LOGIC: Apply tier discounts based on quantity
            # Example: If tier is 'Flower', apply specific bulk price scaling
            if tier_name == 'Flower' and qty >= 2:
                # Example bulk rule: $X off per item for qty 2+
                price = price - 5.0 
            
            raw_total += (price * qty)
        
        final_cash_total = round(raw_total / 5.0) * 5
        
        return {
            "raw_total": float(raw_total),
            "discount_applied": 0.0, # We don't need this if we use tiered pricing
            "final_cash_total": float(final_cash_total)
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

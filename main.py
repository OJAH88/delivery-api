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

@app.get("/api/admin/products")
def get_products():
    db = SessionLocal()
    try:
        # Re-added the JOIN to get tier_name so the math engine can group by it
        query = """
            SELECT p.product_id, p.name, COALESCE(p.base_sticker_price, 0.0) as base_sticker_price, p.category_id, t.name as tier_name 
            FROM products p
            LEFT JOIN price_tiers t ON p.tier_id = t.tier_id
        """
        result = db.execute(text(query)).fetchall()
        return [dict(row._mapping) for row in result]
    except Exception as e:
        print("Inventory Error:", e)
        return []
    finally:
        db.close()


@app.post("/api/cart/calculate")
async def calculate_cart(request: Request):
    try:
        payload = await request.json()
        items = payload.get("items", [])
        
        # 1. Group by Tier: Count total quantity of items per tier across the whole cart
        tier_counts = {}
        for item in items:
            tier = item.get('tier_name')
            qty = int(item.get('qty') or 1)
            if tier:
                tier_counts[tier] = tier_counts.get(tier, 0) + qty
                
        raw_total = 0.0
        discount_applied = 0.0
        
        # 2. Calculate Math: Apply discounts based on the tier totals
        for item in items:
            price = float(item.get('base_sticker_price') or 0)
            qty = int(item.get('qty') or 1)
            tier = item.get('tier_name')
            
            item_total = price * qty
            raw_total += item_total
            
            # BULK LOGIC: If the user has 2 or more TOTAL items in the 'Flower' tier...
            if tier == 'Flower' and tier_counts.get('Flower', 0) >= 2:
                # ...take $5 off EVERY unit of flower they buy
                discount_applied += (5.0 * qty)
                
        final_total = max(0.0, raw_total - discount_applied)
        final_cash_total = round(final_total / 5.0) * 5
        
        return {
            "raw_total": float(raw_total),
            "discount_applied": float(discount_applied),
            "final_cash_total": float(final_cash_total)
        }
    except Exception as e:
        return {"error": str(e)}

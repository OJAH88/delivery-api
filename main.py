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
        # Tries to get the tier_name
        query = """
            SELECT p.product_id, p.name, COALESCE(p.base_sticker_price, 0.0) as base_sticker_price, p.category_id, t.name as tier_name 
            FROM products p
            LEFT JOIN price_tiers t ON p.tier_id = t.tier_id
        """
        result = db.execute(text(query)).fetchall()
        return [dict(row._mapping) for row in result]
    except Exception as e:
        # FAILSAFE: If price_tiers is broken or missing, pull products anyway so items don't disappear
        try:
            fallback = "SELECT product_id, name, COALESCE(base_sticker_price, 0.0) as base_sticker_price, category_id FROM products"
            result = db.execute(text(fallback)).fetchall()
            return [dict(row._mapping) for row in result]
        except:
            return []
    finally:
        db.close()

@app.post("/api/cart/calculate")
async def calculate_cart(request: Request):
    try:
        payload = await request.json()
        items = payload.get("items", [])
        
        # 1. Bulletproof Grouping
        group_counts = {}
        for item in items:
            # Grabs tier_name. If null, grabs category_id.
            group_key = str(item.get('tier_name') or item.get('category_id') or 'unknown')
            qty = int(item.get('qty') or 1)
            group_counts[group_key] = group_counts.get(group_key, 0) + qty
                
        raw_total = 0.0
        discount_applied = 0.0
        
        # 2. Math Engine
        for item in items:
            price = float(item.get('base_sticker_price') or 0)
            qty = int(item.get('qty') or 1)
            group_key = str(item.get('tier_name') or item.get('category_id') or 'unknown')
            
            item_total = price * qty
            raw_total += item_total
            
            # BULK LOGIC: Checks if the group is 'Flower' OR ID '1'. 
            # If the total items in that group are 2 or more, apply the discount to all.
            if group_key in ['Flower', '1'] and group_counts.get(group_key, 0) >= 2:
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

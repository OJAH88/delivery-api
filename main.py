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
        try:
            # We fetch everything with the tier_name attached so the frontend can filter it
            query = """
                SELECT p.product_id, p.name, COALESCE(p.base_sticker_price, 0.0) as base_sticker_price, p.category_id, t.name as tier_name 
                FROM products p
                LEFT JOIN price_tiers t ON p.tier_id = t.tier_id
            """
            result = db.execute(text(query)).fetchall()
        except:
            query = "SELECT product_id, name, COALESCE(base_sticker_price, 0.0) as base_sticker_price, category_id, 'Tier 1' as tier_name FROM products"
            result = db.execute(text(query)).fetchall()
            
        return [dict(row._mapping) for row in result]
    except Exception as e:
        return []
    finally:
        db.close()

@app.post("/api/cart/calculate")
async def calculate_cart(request: Request):
    try:
        payload = await request.json()
        items = payload.get("items", [])
        
        raw_total = 0.0
        
        # Dead simple math. The frontend bundle already set the correct discounted base_sticker_price.
        for item in items:
            price = float(item.get('base_sticker_price') or 0)
            qty = int(item.get('qty') or 1)
            raw_total += (price * qty)
            
        final_total = max(0.0, raw_total)
        final_cash_total = round(final_total / 5.0) * 5
        
        return {
            "raw_total": float(raw_total),
            "discount_applied": 0.0, 
            "final_cash_total": float(final_cash_total)
        }
    except Exception as e:
        return {"error": str(e), "raw_total": 0.0, "discount_applied": 0.0, "final_cash_total": 0.0}

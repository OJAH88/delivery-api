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
            query = """
                SELECT p.product_id, p.name, COALESCE(p.base_sticker_price, 0.0) as base_sticker_price, p.category_id, t.name as tier_name 
                FROM products p
                LEFT JOIN price_tiers t ON p.tier_id = t.tier_id
            """
            result = db.execute(text(query)).fetchall()
        except:
            # Fallback if price_tiers table is missing
            query = "SELECT product_id, name, COALESCE(base_sticker_price, 0.0) as base_sticker_price, category_id FROM products"
            result = db.execute(text(query)).fetchall()
            
        return [dict(row._mapping) for row in result]
    except Exception as e:
        return []
    finally:
        db.close()

@app.post("/api/cart/calculate")
async def calculate_cart(request: Request):
    db = SessionLocal()
    try:
        payload = await request.json()
        items = payload.get("items", [])
        
        # 1. Grab the ultimate source of truth from the DB so we don't rely on the frontend
        query = "SELECT product_id, category_id, name FROM products"
        db_products = {str(row.product_id): row for row in db.execute(text(query)).fetchall()}
        
        flower_qty = 0
        raw_total = 0.0
        
        # 2. Count total flower items in the cart
        for item in items:
            pid = str(item.get('product_id'))
            qty = int(item.get('qty') or 1)
            
            # Look up the real item in the database
            db_item = db_products.get(pid)
            
            frontend_cat = str(item.get('category_id') or '').lower()
            frontend_tier = str(item.get('tier_name') or '').lower()
            db_cat = str(db_item.category_id).lower() if db_item else ''
            db_name = str(db_item.name).lower() if db_item else ''
            
            # MASSIVE NET: If it looks like a flower in ANY way, count it.
            if frontend_cat == '1' or db_cat == '1' or 'flower' in frontend_tier or 'flower' in db_name:
                flower_qty += qty

        discount_applied = 0.0
        
        # 3. Apply the math
        for item in items:
            pid = str(item.get('product_id'))
            qty = int(item.get('qty') or 1)
            price = float(item.get('base_sticker_price') or 0)
            
            db_item = db_products.get(pid)
            frontend_cat = str(item.get('category_id') or '').lower()
            frontend_tier = str(item.get('tier_name') or '').lower()
            db_cat = str(db_item.category_id).lower() if db_item else ''
            db_name = str(db_item.name).lower() if db_item else ''
            
            raw_total += (price * qty)
            
            # Apply the $5 off per unit IF they hit the 2+ threshold
            if (frontend_cat == '1' or db_cat == '1' or 'flower' in frontend_tier or 'flower' in db_name) and flower_qty >= 2:
                discount_applied += (5.0 * qty)
                
        final_total = max(0.0, raw_total - discount_applied)
        final_cash_total = round(final_total / 5.0) * 5
        
        return {
            "raw_total": float(raw_total),
            "discount_applied": float(discount_applied),
            "final_cash_total": float(final_cash_total)
        }
    except Exception as e:
        return {"error": str(e), "raw_total": 0.0, "discount_applied": 0.0, "final_cash_total": 0.0}
    finally:
        db.close()

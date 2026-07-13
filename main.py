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

# 1. RESTORED: The inventory route I stupidly deleted
@app.get("/api/admin/products")
def get_products():
    db = SessionLocal()
    try:
        # The query we know works
        query = """
            SELECT product_id, name, COALESCE(base_sticker_price, 0.0) as base_sticker_price, category_id 
            FROM products
        """
        result = db.execute(text(query)).fetchall()
        return [dict(row._mapping) for row in result]
    except Exception as e:
        print("Inventory Error:", e)
        return []
    finally:
        db.close()

# 2. THE CART LOGIC
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
            
            # Use category_id for bulk pricing. 
            # Note: Change '1' to whatever your Flower category_id actually is.
            cat_id = str(item.get('category_id')) 
            
            item_total = price * qty
            
            # BULK LOGIC: If it's Flower and they buy 2 or more, give a flat discount
            if cat_id == '1' and qty >= 2:
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

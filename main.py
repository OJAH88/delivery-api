from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"], allow_credentials=True)

# Database Setup
engine = create_engine(os.getenv("DATABASE_URL", "postgresql://user:password@localhost/delivery_app"))

@app.post("/api/cart/calculate")
async def calculate_cart(request: Request):
    try:
        payload = await request.json()
        items = payload.get("items", [])
        
        # Calculate raw_total with fallback to 0
        raw_total = sum(float(item.get('base_sticker_price') or 0) * int(item.get('qty') or 1) for item in items)
        
        # Calculate final total
        final_total = max(0.0, float(raw_total))
        final_cash_total = round(final_total / 5.0) * 5
        
        return {
            "raw_total": float(raw_total),
            "discount_applied": 0.0,
            "final_cash_total": float(final_cash_total)
        }
    except Exception as e:
        # If it fails, return a safe object so the frontend doesn't break
        return {"raw_total": 0.0, "discount_applied": 0.0, "final_cash_total": 0.0, "error": str(e)}

@app.get("/api/admin/products")
def get_products():
    try:
        db = sessionmaker(bind=engine)()
        result = db.execute(text("SELECT product_id, name, COALESCE(base_sticker_price, 0.0) as base_sticker_price FROM products")).fetchall()
        db.close()
        return [dict(row._mapping) for row in result]
    except:
        return []

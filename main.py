from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
import traceback

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/delivery_app")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="Delivery App API")

# Hardened CORS policy to allow your Vercel frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

@app.get("/")
def health_check():
    return {"status": "online"}

@app.post("/api/cart/calculate")
async def calculate_cart(request: Request):
    try:
        payload = await request.json()
        items = payload.get("items", [])
        raw_total = 0.0
        for item in items:
            price = float(item.get('base_sticker_price') or 0)
            qty = int(item.get('qty') or 1)
            raw_total += (price * qty)
        
        final_cash_total = round(raw_total / 5.0) * 5
        return {"raw_total": float(raw_total), "final_cash_total": float(final_cash_total)}
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}

@app.get("/api/admin/products")
def get_products():
    db = SessionLocal()
    try:
        query = "SELECT product_id, name, COALESCE(base_sticker_price, 0.0) as base_sticker_price FROM products"
        result = db.execute(text(query)).fetchall()
        return [dict(row._mapping) for row in result]
    except Exception as e:
        return []
    finally:
        db.close()

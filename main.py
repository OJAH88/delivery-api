from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/delivery_app")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"], allow_credentials=True)

@app.get("/api/admin/products")
def get_products():
    db = SessionLocal()
    try:
        # Force a price if the DB is null
        query = "SELECT product_id, name, COALESCE(base_sticker_price, 25.0) as base_sticker_price FROM products"
        result = db.execute(text(query)).fetchall()
        return [dict(row._mapping) for row in result]
    finally:
        db.close()

@app.post("/api/cart/calculate")
async def calculate_cart(request: Request):
    payload = await request.json()
    items = payload.get("items", [])
    raw_total = sum((float(i.get('base_sticker_price') or 25.0) * int(i.get('qty') or 1)) for i in items)
    return {
        "raw_total": float(raw_total), 
        "discount_applied": 0.0, 
        "final_cash_total": round(raw_total / 5.0) * 5
    }

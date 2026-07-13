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

@app.get("/api/admin/products")
def get_products():
    db = SessionLocal()
    try:
        query = """
            SELECT p.product_id, p.name, p.base_sticker_price, t.name as tier_name 
            FROM products p
            LEFT JOIN price_tiers t ON p.tier_id = t.tier_id
        """
        result = db.execute(text(query)).fetchall()
        return [dict(row._mapping) for row in result]
    finally:
        db.close()

@app.post("/api/cart/calculate")
async def calculate_cart(request: Request):
    try:
        payload = await request.json()
        items = payload.get("items", [])
        raw_total = 0.0
        for item in items:
            price = float(item.get('base_sticker_price') or 0)
            qty = int(item.get('qty') or 1)
            tier = item.get('tier_name')
            # Bulk logic: Flower tier gets $5 off per item if qty >= 2
            if tier == 'Flower' and qty >= 2:
                price = price - 5.0
            raw_total += (price * qty)
        return {"raw_total": float(raw_total), "final_cash_total": round(raw_total / 5.0) * 5}
    except Exception as e:
        return {"error": str(e)}
